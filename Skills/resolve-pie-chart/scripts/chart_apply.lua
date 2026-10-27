-- chart_apply.lua -- import the prepared chart comp and set every slice (and the header).
--
--   local cfg = dofile([[<cfg_out>]])
--   cfg.mode = "apply"     -- or "stills" with cfg.stills = { comp-local frames }, cfg.out_dir = [[...\]]
--   local ok, lines = pcall(assert(loadfile([[<skill>\scripts\chart_apply.lua]])), cfg)
--   print(ok and table.concat(lines, "\n") or ("ERROR " .. tostring(lines)))
-- run_inline sandboxes globals and swallows print() from loaded files: pass cfg in, print the return.

local C = ... or {}
local OUT = {}
local function out(...) local t = {} for i = 1, select("#", ...) do t[#t + 1] = tostring(select(i, ...)) end OUT[#OUT + 1] = table.concat(t, "\t") end

local proj = resolve:GetProjectManager():GetCurrentProject()
local tl = proj:GetCurrentTimeline()
local item
for tr = 1, tl:GetTrackCount("video") do
  for _, it in ipairs(tl:GetItemListInTrack("video", tr) or {}) do
    if it:GetUniqueId() == C.item_id then item = it end
  end
end
if not item then out("ERROR: chart clip not found", C.item_id) return OUT end

local function tc(frame)
  local fps = math.floor((tonumber(tl:GetSetting("timelineFrameRate")) or 60) + 0.5)
  local h, m, s, f = tl:GetStartTimecode():match("(%d+):(%d+):(%d+)[:;](%d+)")
  local a = ((tonumber(h) * 60 + tonumber(m)) * 60 + tonumber(s)) * fps + tonumber(f) + (frame - tl:GetStartFrame())
  return string.format("%02d:%02d:%02d:%02d", math.floor(a / (fps * 3600)), math.floor(a / (fps * 60)) % 60, math.floor(a / fps) % 60, a % fps)
end

if (C.mode or "apply") == "apply" then
  local imp = item:ImportFusionComp(C.comp)
  out("import", imp and "ok" or "FAILED", "comps", item:GetFusionCompCount())
  local comp = item:GetFusionCompByIndex(1)
  comp:Lock()
  for _, s in ipairs(C.slices) do
    local T, missing = {}, false
    for role, name in pairs(s.tools) do
      T[role] = comp:FindTool(name)
      if not T[role] then out("MISSING", s.group, role, name); missing = true end
    end
    if not missing then
      T.RW.Value = s.value
      T.Ellipse1.WritePosition = C.position
      T.MatteControl1:SetInput("Garbage.MaskInverted", C.ccw)
      T.CC.Height = C.height
      T.Color.TopLeftRed, T.Color.TopLeftGreen, T.Color.TopLeftBlue = s.rgb[1], s.rgb[2], s.rgb[3]
      T.LineAngle.Angle = s.angle
      T.Line1.Width = s.line1
      T.Line2.Width = s.line2
      T.Title.StyledText = s.label
      T.Title.Size = s.title_size
      T.PC.Percent = s.percent
      T.PC.Size = s.label_size
    end
  end
  if C.header and C.header_tool then
    local h = comp:FindTool(C.header_tool)
    if h then h.StyledText = C.header else out("MISSING header tool", C.header_tool) end
  end
  comp:Unlock()
  for _, s in ipairs(C.slices) do
    local rw, la, pc, cc = comp:FindTool(s.tools.RW), comp:FindTool(s.tools.LineAngle), comp:FindTool(s.tools.PC), comp:FindTool(s.tools.CC)
    if rw and la and pc and cc then
      out(s.group, s.label, "value", rw:GetInput("Value"), "angle", la:GetInput("Angle"),
        "switch@150", string.format("%.2f", cc:GetInput("Switch", 150)), "label@300", pc:GetInput("StyledText", 300))
    end
  end
elseif C.mode == "stills" then
  resolve:OpenPage("color")
  local base = item:GetStart()
  -- the first export of a run can return the previous frame: seek once and let every seek settle
  tl:SetCurrentTimecode(tc(base + math.max(0, C.stills[1] - 30))); bmd.wait(0.8)
  for _, f in ipairs(C.stills) do
    tl:SetCurrentTimecode(tc(base + f + 1)); tl:SetCurrentTimecode(tc(base + f)); bmd.wait(1.0)
    local path = C.out_dir .. "chart_" .. f .. ".png"
    out("still", f, tc(base + f), proj:ExportCurrentFrameAsStill(path) and path or "FAILED")
  end
end
return OUT
