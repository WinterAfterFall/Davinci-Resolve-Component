---
name: resolve-hsr-compare-graph
description: >-
  Build or update the "Compare Graph" section of WAF's Honkai Star Rail guide videos in DaVinci
  Resolve (the "Compare Bar Graph" Fusion comp): section title (e.g. "Light Cone"), the character
  portrait with its "Base Team" label, the horizontal bar rows comparing options (Light Cones, relic
  sets, teammates, eidolons…) by %, and the right-side Note panel (image + title + info) that
  slides in. Use this whenever the user wants a comparison graph scene for an HSR character ("ทำ
  compare graph", "กราฟเทียบ", "เทียบ Light Cone", "เทียบทีม", "ช่วงเปรียบเทียบ", "compare bar
  graph", "ใส่ข้อมูลกราฟเทียบ", "ใส่ note ในกราฟ") or hands over a list of options with % to show
  in that scene, even if they don't name the comp.
---

# HSR Compare Graph section

One scene in WAF's HSR guide videos: a titled comparison of options for one character, shown as
horizontal bars. An optional Note panel on the right explains one option.
The template lives in the Resolve project **"Compare Bar Graph"**, in the Fusion comp of
"Fusion Composition" on Timeline 1, track V1.

**This skill delegates the parts:**
- **Bar rows** → follow the **`resolve-bar-graph`** skill (Max/Min/Value, Rows/Position, Label,
  FullValue, images, Visibility timing).
- **Note panel** → follow **`NoteBox.md`** at
  `~/.claude/skills/resolve-basic/references/NoteBox.md` (Switch and controls
  on `NoteArea`, Title/Info text, image slot, what not to touch).
- **Safety** → the **`resolve-basic`** §7 rules: set plain values and text only, never
  render from a script, no expressions that loop, the user deletes nodes, save before multi-step edits.

## Scene map (live comp, read 2026-10-01)

The flow runs from bottom to top of the stack, and each merge adds one layer:

```
BG → BaseTeam ─► Title_Merge ─► Sub ─► Merge5 ─► Pic_Merge ─► Note_Merge ─► MediaOut1_1
                 (title text)           (bars)    (portrait)   (Note panel)
```

| Part | Where | What to change |
|---|---|---|
| Section title | `CharName_4_1` (TextPlus, currently "Light Cone") → `DropShadow2_4_1` → `Title_Merge` | `StyledText`: the comparison topic, e.g. "Light Cone", "Relic", "Teammate" |
| Portrait label | `CharName_4` (TextPlus, currently "Base Team ") | `StyledText` |
| Character portrait | `Merge6` branch (`Background3`, `Merge2` ← `XF2`/`Transform1`, circle crops in `MultiMerge2`) → `Pic_Merge` | swap the MediaIn image of the character |
| Bar rows | `MultiMerge1` layers ← `Merge8_3_2_1…` from the `B1`–`B4` groups (H_BarGraph(Pic+Text), new macro; they replaced `Bar`/`Bar2`/`Bar3`/`Bar3_1` on 2026-10-01). `B1` is the master row, and `B2`–`B4` read the shared values (margins, Rows, Padding, Max, Min, Visibility) from `B1.InputN` expressions → `Merge5` | see `resolve-bar-graph` |
| Note panel | `NoteArea` … `Note_Merge` | see `NoteBox.md` |

**The layout is tied to the Note Switch:** `NoteArea.Switch` (0 = hidden, 1 = shown) also slides
`Title_Merge`, `Pic_Merge` and `Merge5` to the left and shortens the bars through `RightMargin`
(`B1` › `GC.RightMargin`, which B2–B4 follow through `B1.Input2`). Animate the Note with **one** Switch keyframe pair and everything moves
together. Don't add separate moves on those merges.

## Workflow

1. **Get the data:** the character, the comparison topic, and the list of options with their % values. For example:
   the Light Cone ranking from a `waf-hsr-script` script, relative to the signature LC = 100%.
2. **Names:** follow the HSR naming memory for Light Cones: "<Character>'s Signature S1", and
   non-signature Light Cones as S5/S1. Keep the row titles short enough to fit the `LeftText` of a row.
3. **Title and portrait:** set `CharName_4_1` (topic) and `CharName_4` (label), and swap the portrait image.
4. **Bars:** set Rows (reduce it if there are too many options), Max/Min shared by all rows, and a Value,
   title and image per row, following `resolve-bar-graph`. Add or remove Bar groups to match the row count. The user
   deletes groups; when adding one, also connect it to `MultiMerge1` and keep the `RightMargin`
   expression tied to the Note Switch.
5. **Note (optional):** when the narration explains one option in detail, fill the Note image, Title and Info
   following `NoteBox.md`, and keyframe `NoteArea.Switch` 0 → 1 where the explanation starts and 1 → 0 where it ends.
6. **Timing:** stagger each bar's `Visibility` 0 → 1 after the title pops in. Keep the Note Switch
   out of the moments when the bars are still growing, unless the user wants that.
7. **Check:** read the values back through MCP, then ask the user to look at the viewer. **Never render to check.**

## Multi-topic Note (built for Pearl, 2026-10-01; generator `build_pearl.py` pattern)

In the Pearl guide the scene lives on **V3 Adjustment Clips** (one comp per section: V3[0] Light Cone
over 5.mp4, V3[1] Teammate Score over 6.mp4). Edit them with `item.GetFusionCompByIndex(1)` + `comp.Execute(lua)`.
To step the Note through several topics without keyframing text:
- `NoteArea` user controls **Cut1–Cut3** (comp-local frames; 99999 = unused). Every switch reads them.
- `NoteTitle`/`NoteInfo.StyledText` expression: `time < NoteArea.Cut1 and "A" or time < NoteArea.Cut2 and "B" or "C"`.
- Image and title change: `NoteImage_Merge`/`NoteTitle_Merge.Blend` = `math.min(1, math.abs(time-NoteArea.CutN)/30, …)`,
  i.e. 1→0→1 over 60 frames. The image comes from Loaders `NoteImg1..n` chained through Dissolves
  `NoteImgSwitchN` (Mix = `time >= NoteArea.CutN and 1 or 0`), and the last Dissolve feeds `NoteImage.Foreground`.
- Info write-on: `Start` 0→1 over the 30 frames before a cut, then `End` 0→1 over the 30 frames after it (60 frames total).
- Left alignment: HLCR = -1, HorizontalJustificationNew = 0, and Center X = the image's left edge
  `NoteArea.Center.X-NoteArea.Width/2+NoteFrame.Width+(1-NoteArea.ImgWidth)/2*(NoteArea.Width-NoteFrame.Width)`.
- Thai Info needs the font **Quark** (Open Sans has no Thai). Use `»` instead of `→`.
- SRT time → comp frame: `216000 + seconds*60 - clipStart` (the SRT matches the Main timeline at 60 fps).
- ⚠ `comp:AddTool("Loader", -32768, -32768)` auto-merges the Loader into the flow of the active tool (Merge7…).
  Deselect first (`FlowView:Select()`) or pass real coordinates, and afterwards check that no new Merge appeared.
- ⚠ Connecting a new BezierSpline to `NoteArea.Switch` adds a stray key at the comp's CurrentTime even after
  `SetKeyFrames`. Call `SetKeyFrames(tbl, true)` again in a **separate** Execute, then read the keys back.

## Notes

- This scene map was read on 2026-10-01. The user may rename or restructure the comp, so re-check a node by
  name (`FindTool`) before editing it, and update this map if it changed.
- The bar macro file now places Image 1 at the bar start (edited 2026-10-01). The Bar groups already in the comp
  still use the old `Point(0.5, 0.5)` image centre until they are fixed. See `resolve-bar-graph`.
