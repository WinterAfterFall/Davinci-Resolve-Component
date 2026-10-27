# -*- coding: utf-8 -*-
"""
build_popup.py  --  generate the Lua that animates WAF's pop-up caption box
                    inside the Fusion comp of a DaVinci Resolve Adjustment Clip.

Usage:
    python build_popup.py spec.json out.lua

Then apply in Resolve via the davinci-resolve MCP:
    script_plugin.run_inline(language="lua", source='dofile([[<abs path to out.lua>]])')

The generated Lua is idempotent: it deletes every BezierSpline modifier in the comp,
reconnects fresh splines to the five animated inputs, rewrites all keyframes, and
resets the StyledText expression. Re-run it as many times as you like.

------------------------------------------------------------------------------
spec.json shape
------------------------------------------------------------------------------
{
  "controls": {                     # input ids on the comp's control tool(s)
    "switch":     "rect.Switch",     # 0..1 open/close (0 = parked off-screen)
    "width":      "rect.Width",
    "height":     "rect.Height",
    "write_on":   "Text1.Start",     # TextPlus "Write On Start" -> wipe-out from left
    "write_end":  "Text1.End",       # TextPlus "Write On End"   -> type-on from left
    "text_tool":  "Text1",           # TextPlus tool that holds StyledText
    "size_input": "Text1.Size",      # optional; set a global font size
    "size":       0.037,             # optional; value for size_input
    "title_tool": "HeadText"         # optional; TextPlus in the separate title box above the box
  },
  "height": { "base": 0.102, "per_line": 0.065, "max": 0.62 },
  "clip_end": 16992,                 # comp-local frame count of the adjustment clip
  "timing":  { "switch": 60, "write": 30, "lead": 3, "ease": true },   # optional, these are the defaults
                                     # ease: ease-in/out on rect.Switch (the slide); false = linear
  "states": [
    { "id":"T1",  "text":"heading\n- bullet 1\n- bullet 2", "start": 40,   "new_topic": true,  "width": 0.30 },
    { "id":"T2a", "text":"...",                              "start": 700,  "new_topic": true },
    { "id":"T2b", "text":"...",                              "start": 1700, "new_topic": false },  # sub-state: soft write swap
    ...
    # With a title box ("title_tool"): heading goes in "title", only the bullets in "text".
    # The title swaps at the same frames as the text (while the box is closed / wiped).
  ],
  "end_close": 16620                 # optional; frame the final close starts. default: clip_end-350
}

Per-state "width"/"height" override the auto value. Height auto = base + (lines-1)*per_line,
clamped to max. "lines" = number of \n-separated lines in "text".

Timing model (all comp-local frames), for a state whose narration starts at S:
  new_topic  -> switch out prev (S-2L-5 .. S-L-5), swap StyledText at S-L-4,
                switch in new  (S-L-3 .. S-3)          [L = timing.switch, default 60]
  sub-state  -> wipe out (S-2w-3 .. S-w-3), swap at S-w-2, type on (S-w-1 .. S-1)
                                                        [w = timing.write, default 30]
  first state -> type/switch in only, ending ~S.
  final       -> switch out over timing.switch frames starting at end_close.
"""
import json, sys


def lua_str(s: str) -> str:
    """Return a Lua single-quoted string literal whose VALUE contains literal
    backslash-n for every newline (Fusion turns \\n inside an expression string
    into a real newline at eval time)."""
    s = s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    return "'" + s + "'"


def esc(t: str) -> str:
    """Caption text -> body of a double-quoted Fusion expression string.
    A bare `"` inside the text ends the string and the whole StyledText goes blank."""
    return t.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out_path = sys.argv[2]

    C = spec["controls"]
    H = spec.get("height", {"base": 0.102, "per_line": 0.065, "max": 0.62})
    T = spec.get("timing", {})
    L = T.get("switch", 60)       # switch open/close duration
    w = T.get("write", 30)        # write-on / write-off duration
    lead = T.get("lead", 3)       # frames the box is fully ready before narration
    clip_end = spec["clip_end"]
    states = spec["states"]
    end_close = spec.get("end_close", clip_end - 350)

    def height_of(st):
        if "height" in st:
            return st["height"]
        n = st["text"].count("\n") + 1
        return round(min(H["max"], H["base"] + (n - 1) * H["per_line"]), 4)

    def width_of(st):
        return st.get("width", 0.384)

    # ---- build keyframe lists -------------------------------------------------
    switch_kf, width_kf, height_kf, start_kf, end_kf = [], [], [], [], []
    swaps = []  # (frame, state_index) for the StyledText expression

    switch_kf.append((0, 0.0))
    width_kf.append((0, width_of(states[0])))
    height_kf.append((0, height_of(states[0])))
    start_kf.append((0, 0.0)); end_kf.append((0, 1.0))

    for i, st in enumerate(states):
        S = st["start"]
        Wb, Hb = width_of(st), height_of(st)
        if i == 0:
            o0, o1 = max(2, S - L), S
            swaps.append((max(0, o0 - 5), i))
            switch_kf += [(o0, 0.0), (o1, 1.0)]
            start_kf += [(swaps[-1][0], 0.0)]
            end_kf += [(swaps[-1][0], 1.0)]
            continue
        Wa, Ha = width_of(states[i - 1]), height_of(states[i - 1])
        if st.get("new_topic"):
            cs, ce = S - 2 * L - 5, S - L - 5
            sw = S - L - 4
            os_, oe = S - L - 3, S - lead
            swaps.append((sw, i))
            switch_kf += [(cs, 1.0), (ce, 0.0), (os_, 0.0), (oe, 1.0)]
            width_kf += [(cs, Wa), (ce, Wb)]
            height_kf += [(cs, Ha), (ce, Hb)]
            start_kf += [(cs, 0.0), (sw, 0.0)]
            end_kf += [(cs, 1.0), (sw, 1.0)]
        else:  # sub-state -> soft write swap, box stays on screen
            ws, we = S - 2 * w - 3, S - w - 3
            sw = S - w - 2
            ts, te = S - w - 1, S - 1
            swaps.append((sw, i))
            start_kf += [(ws, 0.0), (we, 1.0), (sw, 0.0), (te, 0.0)]
            end_kf += [(we, 1.0), (sw, 0.0), (ts, 0.0), (te, 1.0)]
            width_kf += [(ws, Wa), (we, Wb)]
            height_kf += [(ws, Ha), (we, Hb)]

    # final close
    switch_kf += [(end_close, 1.0), (end_close + L, 0.0)]

    def dedup(kfs):
        d = {}
        for f, v in sorted(kfs):
            d[max(0, min(clip_end, int(round(f))))] = float(v)
        return sorted(d.items())

    # ---- StyledText expression ---------------------------------------------
    swaps.sort()
    parts = []
    for k in range(len(swaps) - 1):
        nxt_frame = swaps[k + 1][0]
        txt = states[swaps[k][1]]["text"]
        parts.append('time < %d and "%s"' % (nxt_frame, esc(txt)))
    parts.append('"%s"' % esc(states[swaps[-1][1]]["text"]))
    expr = " or ".join(parts)

    # ---- emit Lua ---------------------------------------------------------
    lines = []
    a = lines.append
    # Run through comp:Execute() on the target comp (global `comp`); falls back to the comp open in Fusion.
    a("local comp = comp or fusion:GetCurrentComp()")
    a('comp:StartUndo("popup_build")')
    a("comp:Lock()")
    a("local okrun, errrun = pcall(function()")
    a('for i,tl in pairs(comp:GetToolList(false, "BezierSpline")) do pcall(function() tl:Delete() end) end')
    tool_of = {}
    def emit_spline(input_path, kfs):
        toolname, inp = input_path.split(".", 1)
        v = "S_" + toolname + "_" + inp
        if toolname not in tool_of:
            a('local %s = comp:FindTool("%s")' % ("T_" + toolname, toolname))
            tool_of[toolname] = "T_" + toolname
        a('%s.%s = comp:AddTool("BezierSpline", -32768, -32768)' % (tool_of[toolname], inp))
        keys = dedup(kfs)
        for f, val in keys:
            a('%s.%s[%d] = %r' % (tool_of[toolname], inp, f, val))
        # Connecting a new spline drops an extra key at the comp's CurrentTime (wherever the Fusion
        # viewer was parked) holding the input's old value. Keep only the planned keys, or that stray
        # key re-opens the box / resizes it after the last state.
        a("do")
        a('  local spl = %s.%s:GetConnectedOutput():GetTool()' % (tool_of[toolname], inp))
        a("  local keep = { %s }" % ", ".join("[%d] = true" % f for f, _ in keys))
        a("  local kf, new = spl:GetKeyFrames(), {}")
        a("  for f, e in pairs(kf) do if keep[f] then new[f] = e end end")
        a("  spl:SetKeyFrames(new, true)")
        a("end")
    emit_spline(C["switch"], switch_kf)
    if T.get("ease", True):
        # Ease in/out on the slide: flat Bezier handles at 1/3 of the gap to each neighbour key.
        # Scripted SetKeyFrames takes handles RELATIVE to the key ({dx, dy}); absolute coordinates
        # (the form a saved .comp shows) produce a broken curve that crawls then snaps open.
        tn, ip = C["switch"].split(".", 1)
        a("do")
        a('  local spl = %s.%s:GetConnectedOutput():GetTool()' % (tool_of[tn], ip))
        a("  local kf, fr, new = spl:GetKeyFrames(), {}, {}")
        a("  for f in pairs(kf) do fr[#fr + 1] = f end")
        a("  table.sort(fr)")
        a("  for i, f in ipairs(fr) do")
        a("    local e = { kf[f][1] }")
        a("    if fr[i - 1] then e.LH = { -(f - fr[i - 1]) / 3, 0 } end")
        a("    if fr[i + 1] then e.RH = { (fr[i + 1] - f) / 3, 0 } end")
        a("    new[f] = e")
        a("  end")
        a("  spl:SetKeyFrames(new, true)")
        a("end")
    emit_spline(C["width"], width_kf)
    emit_spline(C["height"], height_kf)
    emit_spline(C["write_on"], start_kf)
    emit_spline(C["write_end"], end_kf)
    if C.get("size_input") and C.get("size") is not None:
        tn, ip = C["size_input"].split(".", 1)
        if tn not in tool_of:
            a('local T_%s = comp:FindTool("%s")' % (tn, tn))
            tool_of[tn] = "T_" + tn
        a('%s.%s = %r' % (tool_of[tn], ip, float(C["size"])))
    tt = C["text_tool"]
    if tt not in tool_of:
        a('local T_%s = comp:FindTool("%s")' % (tt, tt))
        tool_of[tt] = "T_" + tt
    a('%s.StyledText:SetExpression(' % tool_of[tt])
    a("  " + lua_str(expr))
    a(")")
    if C.get("title_tool"):
        tparts = []
        for k in range(len(swaps) - 1):
            tparts.append('time < %d and "%s"' % (swaps[k + 1][0], esc(states[swaps[k][1]].get("title", ""))))
        tparts.append('"%s"' % esc(states[swaps[-1][1]].get("title", "")))
        a('local T_title = comp:FindTool("%s")' % C["title_tool"])
        a("T_title.StyledText:SetExpression(")
        a("  " + lua_str(" or ".join(tparts)))
        a(")")
    a("end)")
    a("comp:Unlock()")
    a("comp:EndUndo(true)")
    a('if not okrun then print("ERROR:", tostring(errrun)) else print("popup applied: %d states, %d switch kf") end'
      % (len(states), len(dedup(switch_kf))))

    open(out_path, "w", encoding="utf-8").write("\n".join(lines))
    print("wrote", out_path)
    print("states:", len(states), " switch kf:", len(dedup(switch_kf)),
          " write kf:", len(dedup(start_kf)), "/", len(dedup(end_kf)),
          " expr bytes:", len(expr))
    # sanity: report any negative or out-of-range keyframes
    allf = [f for kfs in (switch_kf, width_kf, height_kf, start_kf, end_kf) for f, _ in kfs]
    if min(allf) < 0:
        print("!! WARNING: negative keyframe frame(s) -> a state's 'start' is too close to clip start")
    if max(allf) > clip_end:
        print("!! WARNING: keyframe past clip_end", clip_end)


if __name__ == "__main__":
    main()
