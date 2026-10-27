---
name: resolve-pie-chart
description: Fill WAF's animated pie chart (PieChartV2 macro instances inside the "Damage Source" chart Fusion Composition) in a DaVinci Resolve guide video with real numbers — slice labels, percents, stacked Value, line angles, colors, header — for Honkai Star Rail damage breakdowns and similar shares. Use this whenever the user gives a list of parts with percentages to show as a chart ("ทำ pie chart", "กราฟวงกลม", "ที่มาของดาเมจ", "damage source", "damage share", "En ESkill 59.2%"), mentions PieChartV2 / p1 p2 p3 / PopupTextBoxWithTitle, or wants an existing chart's slices, labels or line directions changed — even if they don't say "pie".
---

# WAF pie chart (PieChartV2)

WAF presents damage breakdowns as an animated pie chart inside a **Fusion Composition clip** on the
timeline. The clip is built from the user's template:

```
PopupTextBoxWithTitle  (navy/gold panel, header text e.g. "Damage Source")
  └ Transform1 ← MultiMerge1 ← Layer1 = pie instance (largest slice, bottom)
                              Layer2 = next slice …   LayerN = smallest slice (top)
```

Each layer is one **PieChartV2** group (named `p1`, `p2`, `p3`, `PieChartV2`…). Fusion suffixes the tools
inside pasted copies (`CC`, `CC_3`, `CC_4`, `RW_5`, `Title_7`…), so never assume names —
`scripts/chart_prepare.py inspect` maps every instance.

## PieChartV2 controls (the user's definitions)

| control | meaning |
|---|---|
| **Height** | circle radius (template 0.283) |
| **Switch** | the whole animation, 0 → 1 (template: keyframed 0→1 over comp frames 0–150 on the first instance) |
| **PieGraphTime** | time *weight* of the pie sweep |
| **LineTime** | time *weight* of the leader line |
| **TextFadeTime** | time *weight* of the text fade (weights are proportions of the Switch range, not seconds) |
| **CounterClockwise** | direction the slice sweeps |
| **Position** | where the slice starts: 0 = the +X axis (3 o'clock), increasing counter-clockwise; 0..1 = 0..360° |
| **Line Rotate** | angle of the leader line from the centre (degrees, CCW) |
| **Line1 / Line2** | first segment (from the centre) / second segment; Line2 turns left or right automatically |
| **Percent** | the number the label shows |
| **Value** | how much of the circle this layer fills |

Star Rail convention: **Percent = the real value. Value = 100 − the sum of every percent larger than this
slice.** 70/20/10 → Values 100/30/10. All slices share one Position and are stacked largest at the
bottom, so each visible wedge ends up exactly its own size. Template: Position 0.25 (starts at 12
o'clock), CounterClockwise 1.

## Workflow

`SKILL_DIR = C:\Users\ADMIN\.claude\skills\resolve-pie-chart`. Resolve calls go through the davinci-resolve
MCP `script_plugin.run_inline` (Lua).

1. **Find the chart clip.** It's a `Fusion Composition` item whose comp has `PopupTextBoxWithTitle` and
   PieChartV2 groups. Note its unique id and where it sits against the narration (the user places it;
   don't move it — the API can't). Export it: `item:ExportFusionComp(<scratch>\chart.comp, 1)`.

2. **Inspect** (offline): `python SKILL_DIR/scripts/chart_prepare.py inspect chart.comp` → connected layers
   (bottom→top), spare unconnected instances, header tool. A template needs at least as many pie instances as
   slices; if it's short, ask the user to copy-paste a PieChartV2 group in Fusion (scripts can't paste macros).

3. **Plan + prepare** (offline): write `spec.json` (fields in the script docstring: `comp_in`, `comp_out`,
   `cfg_out`, `item_id`, `header`, `position`, `ccw`, `height`, `slices` with `label` + `percent`, optional
   `color`, `angle`, `title_size`, `label_size`, `line1`, `line2`) and run
   `python SKILL_DIR/scripts/chart_prepare.py prepare spec.json`. It
   - sorts slices, computes Value, and defaults Line Rotate to the middle of each visible wedge (it prints
     the wedge range, e.g. `wedge [90.0, 126.4]` — any override must stay inside it or the line points at
     the wrong slice);
   - connects spare instances as extra top layers and makes their Switch follow the first instance
     (`Expression = "CC.Switch"`), or disconnects extra layers when there are fewer slices;
   - writes the prepared comp and a Lua config. Sizes/colors fall back to the template's rank scale
     (title 0.079/0.0655/0.0555/0.0492, label 0.0686/0.055/0.05/0.0468, gold shades dark→light).
   Show the user the printed table (label, percent, Value, angle) before touching Resolve.

4. **Apply** (Resolve):
   ```lua
   local cfg = dofile([[<cfg_out>]])
   cfg.mode = "apply"
   local ok, lines = pcall(assert(loadfile([[SKILL_DIR\scripts\chart_apply.lua]])), cfg)
   print(ok and table.concat(lines, "\n") or ("ERROR " .. tostring(lines)))
   ```
   It `ImportFusionComp`s the prepared comp, then sets Value, Position, CounterClockwise, Height, color,
   Line Rotate, Line1/Line2, Title text/size, Percent/size per slice, and the header. Pass the config as the
   chunk argument and print the returned lines — `run_inline` sandboxes globals and swallows `print` from
   loaded files.

5. **Verify with stills.** Same call with `cfg.mode = "stills"`, `cfg.stills = { 60, 100, 200, 600 }`
   (comp-local frames: mid pie, mid line, settled, late), `cfg.out_dir = [[<scratch>\]]`. Read the PNGs:
   wedge sizes look right, each line points into its own wedge, labels don't overlap each other or the
   header, numbers match. Labels that collide: nudge `angle` inside the wedge, lengthen `line1`, or change
   `line2`/sizes in the spec, re-run prepare + apply.

6. **Save**: `resolve:GetProjectManager():SaveProject()` (not on "Untitled Project").

## Gotchas

- Import, don't build: comps created with `AddFusionComp` + `AddTool` read back fine but don't render;
  an imported comp renders. Editing inputs on an imported comp through the API is fine.
- The first still of a run can come back as the previous frame; the stills mode seeks once and waits.
- The template's Title font is Sukhumvit Set (Thai-safe) — keep it unless the user asks.
- Percent labels count up with Switch (`"%.1f%%"` of Percent × Switch); the number only reads correctly
  once Switch reaches 1, so judge numbers on a settled frame.
- Keep the template's own Switch keyframes (first instance) as the timing master; don't re-key extra
  instances.
