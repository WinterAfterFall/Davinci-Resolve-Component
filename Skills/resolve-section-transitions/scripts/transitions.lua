-- transitions.lua -- WAF section transitions (IntroduceTransitionV1 / Transition2.0) on Adjustment Clips.
--
-- Run through the davinci-resolve MCP:
--   script_plugin.run_inline(language="lua", source=
--     local cfg = { mode = "plan", assets = [[<skill>\assets\]] }
--     local ok, lines = pcall(assert(loadfile([[<skill>\scripts\transitions.lua]])), cfg)
--     print(ok and table.concat(lines, "\n") or ("ERROR " .. tostring(lines)))
--   )
-- The config is passed as the chunk argument: run_inline sandboxes its globals, so a global set
-- there is invisible to the loaded file. The report comes back as the chunk's return value.
--
-- cfg fields
--   mode           "plan" | "markers" | "layout" | "clear_markers" | "apply" | "stills"
--   lead / tail    layout: transition starts `lead` (34) frames before clip n ends; clip n+1 starts `tail` (21) frames before the transition ends
--   assets         folder holding intro_template.comp / transition20_template.comp (trailing backslash)
--   titles         { [<number of the clip AFTER the cut>] = "Title text" }   e.g. { [2] = "Aventurine\nGuide", [3] = "Ability" }
--   fonts          optional { [n] = { font = "Open Sans", style = "Bold" } }
--   sizes          optional { [n] = 0.17 }  title text size (templates: transition 0.22, intro 0.185)
--   offsets        optional { [n] = -34 }  start of the transition relative to the cut (default -34)
--   images         optional { profile1 = [[path]], profile3 = [[path]] }  intro only
--   direct         optional { { id = "<adjustment clip unique id>", kind = "intro"|"transition", n = <n> } }
--                  fill these clips regardless of cut matching
--   reimport       true = import the template even if the clip already carries the macro
--   force          true = apply even when an overlap rule is broken
--   out_dir        folder for stills (trailing backslash)
--   only           optional { [n] = true } restrict apply/stills/markers to these boundaries
--   clip_starts    markers: also drop a blue 1-frame marker on the first frame of every numbered clip
--   all            markers: also mark cuts whose existing Adjustment Clip breaks the rule (to show where to drag it)

local C = ... or {}
local mode = C.mode or "plan"
local BEFORE, AFTER = 34, 27
local KIND = {
  intro      = { len = 367, template = "intro_template.comp",        group = "^IntroduceTransitionV1", title = "^Title",            stills = { 100, 300 } },
  transition = { len = 210, template = "transition20_template.comp", group = "^Transition20",          title = "^Test_TextPreview", stills = { 120 } },
}

local proj = resolve:GetProjectManager():GetCurrentProject()
local tl = proj:GetCurrentTimeline()
local tlStart = tl:GetStartFrame()
local fps = math.floor((tonumber(tl:GetSetting("timelineFrameRate")) or 60) + 0.5)

-- print() inside a loaded chunk is swallowed by run_inline, so collect lines and return them
local OUT = {}
local function out(...) local t = {} for i = 1, select("#", ...) do t[#t + 1] = tostring(select(i, ...)) end OUT[#OUT + 1] = table.concat(t, "\t") end

-- frame -> timecode (non-drop), anchored on the timeline start timecode
local function tc(frame)
  local h, m, s, f = tl:GetStartTimecode():match("(%d+):(%d+):(%d+)[:;](%d+)")
  local base = ((tonumber(h) * 60 + tonumber(m)) * 60 + tonumber(s)) * fps + tonumber(f)
  local a = base + (frame - tlStart)
  return string.format("%02d:%02d:%02d:%02d", math.floor(a / (fps * 3600)), math.floor(a / (fps * 60)) % 60, math.floor(a / fps) % 60, a % fps)
end

local function show(s) return '"' .. tostring(s):gsub("\n", "\\n") .. '"' end
local function isThai(s) return s and s:find("\224[\184\185]") ~= nil end
local function strip(name) return (name:gsub("_%d+$", "")) end

-- tools of a comp whose base name matches a pattern (Fusion suffixes pasted tools with _1, _2 ...)
local function findTool(comp, pattern, regid)
  for _, t in pairs(comp:GetToolList(false)) do
    local a = t:GetAttrs()
    if strip(t.Name):match(pattern .. "$") and (not regid or a.TOOLS_RegID == regid) then return t end
  end
end
local function findGroup(comp)
  for _, t in pairs(comp:GetToolList(false)) do
    if t:GetAttrs().TOOLS_RegID == "GroupOperator" then
      for kind, k in pairs(KIND) do if t.Name:match(k.group) then return kind, t end end
    end
  end
end

-- 1. numbered clips (1.mp4, 2.mov ...) on any video track, merged if a number appears in several pieces
local clips, nums = {}, {}
for tr = 1, tl:GetTrackCount("video") do
  for _, it in ipairs(tl:GetItemListInTrack("video", tr) or {}) do
    local n = it:GetName():match("^(%d+)%.%w+$")
    if n then
      n = tonumber(n)
      local e = clips[n]
      if not e then clips[n] = { n = n, s = it:GetStart(), e = it:GetEnd(), track = tr, parts = 1 }; nums[#nums + 1] = n
      else e.s = math.min(e.s, it:GetStart()); e.e = math.max(e.e, it:GetEnd()); e.parts = e.parts + 1 end
    end
  end
end
table.sort(nums)

-- 2. boundaries in filename order
local bounds = {}
for i = 2, #nums do
  local a, b = clips[nums[i - 1]], clips[nums[i]]
  local kind = (a.n == 1 and b.n == 2) and "intro" or "transition"
  local L = KIND[kind].len
  local cut = b.s
  local S = cut + ((C.offsets or {})[b.n] or -BEFORE)
  local notes = {}
  if b.n ~= a.n + 1 then notes[#notes + 1] = "number gap " .. a.n .. "->" .. b.n end
  if b.s < a.s then notes[#notes + 1] = "OUT OF ORDER: " .. b.n .. ".x starts before " .. a.n .. ".x" end
  if a.e < cut then notes[#notes + 1] = "gap " .. (cut - a.e) .. "f between clips" end
  if a.e > cut then notes[#notes + 1] = "clips overlap " .. (a.e - cut) .. "f" end
  if a.parts > 1 or b.parts > 1 then notes[#notes + 1] = "clip split in pieces" end
  if cut - S < BEFORE then notes[#notes + 1] = "offset breaks >=" .. BEFORE .. " before" end
  if S + L - cut < AFTER then notes[#notes + 1] = "offset breaks >=" .. AFTER .. " after" end
  if S < a.s then notes[#notes + 1] = "starts before clip " .. a.n .. " begins" end
  if S + L > b.e then notes[#notes + 1] = "runs past end of clip " .. b.n end
  bounds[#bounds + 1] = { a = a, b = b, kind = kind, L = L, cut = cut, S = S, notes = notes }
end

-- 3. adjustment clips on the top video track, matched to the cut they straddle
local top = tl:GetTrackCount("video")
local adjs = {}
for _, it in ipairs(tl:GetItemListInTrack("video", top) or {}) do
  if it:GetName() == "Adjustment Clip" then adjs[#adjs + 1] = { item = it, s = it:GetStart(), e = it:GetEnd(), id = it:GetUniqueId(), used = false } end
end
for _, bd in ipairs(bounds) do
  for _, ad in ipairs(adjs) do
    -- <= / >= so a clip that merely touches the cut is matched and reported as breaking the rule
    if not ad.used and ad.s <= bd.cut and ad.e >= bd.cut then bd.adj = ad; ad.used = true; break end
  end
end
local function adjChecks(bd, ad)
  local v = {}
  if bd.cut - ad.s < BEFORE then v[#v + 1] = "before cut " .. (bd.cut - ad.s) .. "f < " .. BEFORE end
  if ad.e - bd.cut < AFTER then v[#v + 1] = "after cut " .. (ad.e - bd.cut) .. "f < " .. AFTER end
  if ad.e - ad.s ~= bd.L then v[#v + 1] = "length " .. (ad.e - ad.s) .. " (expected " .. bd.L .. ")" end
  return v
end
local function inOnly(n) return not C.only or C.only[n] end

local function describeComp(item)
  if item:GetFusionCompCount() == 0 then return "no comp" end
  local comp = item:GetFusionCompByIndex(1)
  local kind, g = findGroup(comp)
  if not kind then return "comp without transition macro" end
  local tt = findTool(comp, KIND[kind].title, "TextPlus")
  return kind .. " macro, title=" .. show(tt and tt:GetInput("StyledText", 0) or "?") .. " font=" .. tostring(tt and tt:GetInput("Font", 0))
end

out("timeline", tl:GetName(), "fps", fps, "top track V" .. top, "numbered clips", #nums, "adjustment clips on top", #adjs)

if mode == "plan" then
  for _, bd in ipairs(bounds) do
    out(string.format("[%d->%d] %s  cut f%d %s  planned start f%d %s len %d", bd.a.n, bd.b.n, bd.kind, bd.cut, tc(bd.cut), bd.S, tc(bd.S), bd.L))
    if #bd.notes > 0 then out("   notes: " .. table.concat(bd.notes, "; ")) end
    if bd.adj then
      local v = adjChecks(bd, bd.adj)
      out(string.format("   adj %s f%d-%d (%s) before %d after %d -> %s | %s", bd.adj.id, bd.adj.s, bd.adj.e, tc(bd.adj.s), bd.cut - bd.adj.s, bd.adj.e - bd.cut,
        #v == 0 and "OK" or ("BREAKS: " .. table.concat(v, "; ")), describeComp(bd.adj.item)))
    else
      out("   no adjustment clip on V" .. top .. " across this cut")
    end
  end
  for _, ad in ipairs(adjs) do
    if not ad.used then out(string.format("unmatched adj %s f%d-%d %s len %d | %s", ad.id, ad.s, ad.e, tc(ad.s), ad.e - ad.s, describeComp(ad.item))) end
  end

elseif mode == "markers" then
  for _, bd in ipairs(bounds) do
    -- all = true also marks cuts whose Adjustment Clip exists but sits in the wrong place
    local misplaced = bd.adj and #adjChecks(bd, bd.adj) > 0
    if (not bd.adj or (C.all and misplaced)) and inOnly(bd.b.n) then
      local title = (C.titles or {})[bd.b.n] or "?"
      local ok = tl:AddMarker(bd.S - tlStart, bd.kind == "intro" and "Pink" or "Cream",
        (bd.kind == "intro" and "Intro " or "Transition ") .. bd.a.n .. "->" .. bd.b.n,
        "Adjustment Clip on V" .. top .. ", start here, length " .. bd.L .. "f. Title: " .. title, bd.L, "waf-transition")
      out("marker", bd.a.n .. "->" .. bd.b.n, tc(bd.S), "len", bd.L, ok and "added" or "FAILED (marker already at that frame?)")
    end
  end

  if C.clip_starts then
    for _, n in ipairs(nums) do
      local cl = clips[n]
      if inOnly(n) then
        local ok = tl:AddMarker(cl.s - tlStart, "Blue", "Start " .. n, "First frame of clip " .. n, 1, "waf-transition")
        out("marker", "start " .. n, tc(cl.s), ok and "added" or "FAILED (marker already at that frame?)")
      end
    end
  end

elseif mode == "layout" then
  -- Plan a gap-free sequence from the clips' current lengths and mark where everything should go:
  --   transition n->n+1 starts `lead` frames before clip n ends,
  --   clip n+1 starts `tail` frames before that transition ends.
  -- Clip 1 keeps its current start. Nothing is moved; markers only.
  local lead, tail = C.lead or BEFORE, C.tail or 21
  -- from = n: keep everything before clip n, chain from clip n's CURRENT start, and replace only the
  -- skill's markers from that clip onward (used after the user re-trims a clip mid-sequence)
  local first = 1
  if C.from then
    for i, n in ipairs(nums) do if n == C.from then first = i end end
    local cut = clips[nums[first]].s
    local removed = 0
    for f, m in pairs(tl:GetMarkers() or {}) do
      if m.customData == "waf-transition" and tlStart + f >= cut then
        if tl:DeleteMarkerAtFrame(f) then removed = removed + 1 end
      end
    end
    out("from clip " .. C.from .. ": removed " .. removed .. " old markers at/after " .. tc(cut))
  end
  local pos = clips[nums[first]] and clips[nums[first]].s
  for i = first, #nums do
    local n = nums[i]
    local cl = clips[n]
    local len = cl.e - cl.s
    local okc = tl:AddMarker(pos - tlStart, "Blue", "Start " .. n, "Clip " .. n .. " starts here (length " .. len .. "f)", 1, "waf-transition")
    out(string.format("clip %d  start f%d %s  len %d  (now at %s)  %s", n, pos, tc(pos), len, tc(cl.s), okc and "marked" or "MARK FAILED"))
    local nxt = nums[i + 1]
    if nxt then
      local kind = (n == 1 and nxt == 2) and "intro" or "transition"
      local L = KIND[kind].len
      local S = pos + len - lead
      local title = (C.titles or {})[nxt] or "?"
      local okt = tl:AddMarker(S - tlStart, kind == "intro" and "Pink" or "Cream",
        (kind == "intro" and "Intro " or "Transition ") .. n .. "->" .. nxt,
        "Adjustment Clip on V" .. top .. ", length " .. L .. "f. Title: " .. title, L, "waf-transition")
      out(string.format("  %s %d->%d  start f%d %s  end f%d %s  %s", kind, n, nxt, S, tc(S), S + L, tc(S + L), okt and "marked" or "MARK FAILED"))
      pos = S + L - tail
    end
  end

elseif mode == "clear_markers" then
  local n = 0
  while n < 200 and tl:DeleteMarkerByCustomData("waf-transition") do n = n + 1 end
  out("removed markers", n)

elseif mode == "apply" then
  local jobs = {}
  for _, bd in ipairs(bounds) do
    if bd.adj and inOnly(bd.b.n) then jobs[#jobs + 1] = { item = bd.adj.item, kind = bd.kind, n = bd.b.n, label = bd.a.n .. "->" .. bd.b.n, breaks = adjChecks(bd, bd.adj) } end
  end
  for _, d in ipairs(C.direct or {}) do
    for _, ad in ipairs(adjs) do
      if ad.id == d.id then jobs[#jobs + 1] = { item = ad.item, kind = d.kind, n = d.n, label = "direct " .. d.id, breaks = {} } end
    end
  end
  for _, job in ipairs(jobs) do
    local title = (C.titles or {})[job.n]
    if #job.breaks > 0 and not C.force then
      out(job.label, "SKIPPED: " .. table.concat(job.breaks, "; "))
    elseif not title then
      out(job.label, "SKIPPED: no title given for clip " .. tostring(job.n))
    else
      local item, K = job.item, KIND[job.kind]
      local have = item:GetFusionCompCount() > 0 and findGroup(item:GetFusionCompByIndex(1))
      if have ~= job.kind or C.reimport then
        local imp = item:ImportFusionComp(C.assets .. K.template)
        out(job.label, "import", K.template, imp and "ok" or "FAILED")
      end
      local comp = item:GetFusionCompByIndex(1)
      local kind = comp and findGroup(comp)
      if kind ~= job.kind then
        out(job.label, "ERROR: macro not found after import (found " .. tostring(kind) .. ")")
      else
        local f = (C.fonts or {})[job.n] or {}
        local font = f.font or (isThai(title) and "Sukhumvit Set" or "Open Sans")
        local style = f.style or "Bold"
        local tt = findTool(comp, K.title, "TextPlus")
        comp:Lock()
        tt.StyledText = title
        tt.Font = font
        tt.Style = style
        if (C.sizes or {})[job.n] then tt.Size = C.sizes[job.n] end
        if job.kind == "intro" and C.images then
          for key, pat in pairs({ profile1 = "^Loader_Profile1", profile3 = "^Loader_Profile3" }) do
            local p = C.images[key]
            local ld = p and findTool(comp, pat, "Loader")
            if ld then ld.Clip = p end
          end
        end
        comp:Unlock()
        local extra = ""
        if job.kind == "intro" then
          local l1, l3 = findTool(comp, "^Loader_Profile1", "Loader"), findTool(comp, "^Loader_Profile3", "Loader")
          extra = " img1=" .. tostring(l1 and l1:GetInput("Clip")) .. " img3=" .. tostring(l3 and l3:GetInput("Clip"))
        end
        out(job.label, "set", show(tt:GetInput("StyledText", 0)), tt:GetInput("Font", 0), tt:GetInput("Style", 0) .. extra,
          #job.breaks > 0 and ("(forced over: " .. table.concat(job.breaks, "; ") .. ")") or "")
      end
    end
  end

elseif mode == "stills" then
  resolve:OpenPage("color")
  local targets = {}
  for _, bd in ipairs(bounds) do if bd.adj and inOnly(bd.b.n) then targets[#targets + 1] = { s = bd.adj.s, kind = bd.kind, label = bd.a.n .. "-" .. bd.b.n } end end
  for _, d in ipairs(C.direct or {}) do
    for _, ad in ipairs(adjs) do if ad.id == d.id then targets[#targets + 1] = { s = ad.s, kind = d.kind, label = "direct" .. (d.n or "") } end end
  end
  -- the first export of a run can return the frame the viewer showed before: move the playhead once
  -- up front, and let every seek settle before exporting
  if targets[1] then tl:SetCurrentTimecode(tc(targets[1].s)); bmd.wait(0.5) end
  for _, t in ipairs(targets) do
    for _, off in ipairs(KIND[t.kind].stills) do
      local code = tc(t.s + off)
      tl:SetCurrentTimecode(tc(t.s + off + 1)); tl:SetCurrentTimecode(code)
      bmd.wait(0.5)
      local path = C.out_dir .. "tr_" .. t.label .. "_" .. off .. ".png"
      out("still", t.label, code, proj:ExportCurrentFrameAsStill(path) and path or "FAILED")
    end
  end
else
  out("unknown mode", mode)
end

return OUT
