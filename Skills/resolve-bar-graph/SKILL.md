---
name: resolve-bar-graph
description: >-
  Fill and animate WAF's horizontal bar graph (the H_BarGraph(Pic+Text) group, the "Bar…" groups
  in comps like "Compare Bar Graph") in a DaVinci Resolve guide video: row titles, values, bar
  lengths (Max/Min), the % label, the 4 subject image slots, and the Visibility reveal timing
  (TitleTime / GraphTime). Use this whenever the user gives a list of things with numbers to show
  as bars ("ทำ bar graph", "กราฟแท่ง", "เทียบดาเมจ", "เทียบค่า", "Teammate Score", "118.1%"),
  mentions H_BarGraph / BarGraphV2 / GC / LeftText / Label / FullValue / Visibility, or wants an
  existing bar's value, order, images or animation changed, even if they don't say "bar graph".
---

# Resolve horizontal bar graph (H_BarGraph(Pic+Text))

One **group = one bar row**. A chart is several groups stacked with the same Rows/Max/Min and
different `Position`s. The macro file is
`%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Macros\H_BarGraph(Pic+Text).setting`.
In a comp the groups are named after the row, for example `B1`–`B4` in Compare Bar Graph. Row 1 is the
**master**, and the other rows read its shared inputs through expressions (`B1.Input1` … `B1.Input11`: margins,
Rows, Padding, Max, Min, Visibility), so change the shared values on the master only. Side Padding
(`B1.Input23` / `B1.Input34`) and Text Padding (`B1.Input22` / `B1.Input33`) also follow B1. In the macro,
TextPadding is a user control with `INP_External=false, INP_Passive=true`, which blocks expressions. Set it to
`INP_External=true, INP_Passive=false` on the inner `Label*`/`LeftText*` tools first, then put the expression on
the **inner** tool (a group-level read can still show the old value).
**Copying one group's settings to another group** (for example when swapping in a new macro version): copy
every group input by ID. Rewrite expressions that name the old master (`Bar.` → `B1.`), connect any image
inputs, and copy animation. Build the new BezierSpline, connect it, then `SetKeyFrames(src:GetKeyFrames(), true)`
**after** connecting, because connecting adds a stray key at the current frame. Re-link the consumers of the old
group's `FindMainOutput(1)` to the new group. In Lua, a group output reports its inner tool, not the group name.
The tools inside each group carry suffixes,
so the control tool is `GC`, `GC_3_1`, `GC_3_1_1` and so on.

Follow the safety rules in §7 of the `resolve-basic` skill. Only **set plain values** through
MCP: no renders, and no new expressions that read image data from downstream tools.

## Controls (what the user means by each)

All of these are published on the group. The real values live on the group's inner **`GC`** RectangleMask.

| Control | Meaning |
|---|---|
| **Max** | The value that gives the **longest possible bar**: the bar reaches the right margin. |
| **Min** | The value that gives a bar of **length 0**. Values in between scale linearly. |
| **Value** | The number that sets **this bar's length**. |
| **Visibility** | The **switch / reveal driver**. Keyframe it 0 → 1 to animate the row in, and 1 → 0 to take it out. |
| **TitleTime : GraphTime** | The **ratio** of the Visibility range spent on the title reveal versus the bar growing. Only the ratio matters (TotalTime = TitleTime + GraphTime). The default of 1 : 4 means the first 20% of the Visibility ramp pops in the title and images, and the last 80% grows the bar. |
| **FullValue** | Used **when the real number and a good-looking bar disagree**. Values can be so far apart that true proportions look ugly. Then `Value` keeps setting the bar length, and `FullValue` is the number the **Label should display**. ⚠ See "Known gap". |
| **Rows** | **How many bar rows the chart presents.** The area between Top and Bottom Margin is split into `Rows` equal slots, so row thickness = area ÷ Rows. If Rows is too high the bars get thin and the text and images become small. **Bring it down to fit**: match it to the number of bars actually shown, and cut or split the list rather than cramming. |
| **Position** | This row's slot, 1 = top. It must be ≤ Rows. |
| Left/Right/Top/Bottom Margin, Padding | The chart area and the gap between rows. `RightMargin` is often driven by an expression (see "Interplay with NoteBox"). |

**Label page** (the value text at the bar's end): `Auto Value` on means it shows the animated value as
`"%.1f%%"`, counting up while the bar grows. Off means it shows the **Text** field (manual). Font,
colour, Text Padding, Side Padding and stroke Thickness are also here.

**Left text page** is the row **title** (`LeftText`, drawn at the left inside the row), with Text,
font, colour, padding and stroke Thickness.

**Image page** has **4 slots** (Image 1–4) with a `Use Image N` checkbox for each, plus `Image Size`. They
show the **subject** the row describes. Usually one image is used, but a subject can need up to 4, for
example a team, so there are 4 slots. Slot 1 sits closest to the bar, and slots 2–4 stack further
left. Tick `Use Image N` for every slot you plug in. **Connect a Loader straight to the group's
`MainInput1..4`.** Don't add any Merge or Transform: the group already sizes and positions the images
(the user confirmed this 2026-10-01).
**Image 1 position** matches BarGraphV2, where the image sits at the Title's centre. Since the
2026-10-01 edit, `Popup_3 › Transform1_1_3.Center` =
`Point(GC.LeftMargin, 1 - GC.TopMargin - (1 - GC.TopMargin - GC.BottomMargin) / GC.Rows*(GC.Position - 1)-GC.Height/2)`.
That puts Image 1's centre at the bar's start, at the row's vertical centre. It used to be
`Point(0.5, 0.5)`, the screen centre, which ignored the row. Groups placed **before** this edit still
carry the old expression. Fix each live group's `Transform1_1_3`, whose name is suffixed, the same way.

## How it works (from the macro's expressions)

- Bar width = `(1-LeftMargin-RightMargin)/(Max-Min)*(Value-Min)`, minus the round-cap allowance, × the
  graph progress.
- Graph progress runs from 0 to 1 while `Visibility` goes from `TitleTime/TotalTime` to `1`.
- The title and image pop use `min(1, Visibility*TotalTime/TitleTime)`.
- The end-cap circle grows during the first half of the graph phase. The label and stroke fade in near
  the end of that phase.

## Filling a chart from the user's numbers

1. Get the list, for example "Robin 118.1, Sunday 95.2, …". Decide on the display order, usually highest first.
2. Set **Rows** to the number of bars you will actually present, and give each group its **Position**
   (1…Rows, top to bottom). If the list is too long for readable rows, **reduce Rows**. Show only the
   top entries, or split the list into two charts or scenes, and tell the user which ones you dropped. Every
   group in one chart must share the same Rows value. The Compare Bar Graph comp currently uses Rows 7.
3. Set the same **Max** and **Min** on every group:
   - Max = the largest value (or a round number just above it).
   - Min = a floor that keeps the smallest bar visibly non-zero but shows the differences. In Compare Bar
     Graph it is Max 118.1 and Min 50. Min = 0 gives true proportions.
4. Per row: **Value** (bar length), **Left text** (the name), and the images with their `Use Image N` ticked.
5. If the true numbers make the bars look bad, for example 5% next to 400%, choose Values for the look
   and put the true numbers in **FullValue**. Until the known gap is fixed, set `Auto Value` off and
   type the true number in the Label **Text** instead.
6. Animation: keyframe **Visibility** 0 → 1 on each row and stagger the rows a few frames apart.
   Adjust TitleTime : GraphTime to change how long the title waits before the bar grows.

Setting values via MCP: find the group's `GC` by its parent group. Use
`t.GetAttrs('TOOLH_GroupParent')` or known names such as `GC_3_1`, then `SetInput('Value', …)`.
Text goes through the `LeftText` / `Label` tools inside the same group (`StyledText`, `ManualText`). Read the
values back afterwards. Never pull images to check the result; ask the user to look at the viewer.

## Known gap: FullValue is not wired up

In both the macro file and the live comp (checked 2026-10-01), **no expression reads `FullValue`**.
The Label always formats `GC.Value`. Proposed fix, **not applied yet** (ask the user first). Set the
Label's `StyledText` expression to show FullValue when it is greater than 0:

```
(AutoValue == 1) and (string.format("%.1f%%", ((GC.FullValue > 0) and GC.FullValue or GC.Value) * <progress>)) or ManualText
```

Here `<progress>` is the existing graph-progress term. Apply it in the macro `.setting` file (text edit,
safe) and in each live group's `Label`, whose suffixed names need `GC_x` references.

## Interplay with NoteBox (Compare Bar Graph)

The Bar rows' **RightMargin** follows the NoteBox Switch, so the bars shorten when the note panel slides in:
`GC.RightMargin` in the master row `B1` = `0.08+NoteArea.Width*NoteArea.Switch*0.2`, and the other rows follow through `B1.Input2`. Keep this
when you add rows to that comp. See `references/NoteBox.md` in the resolve-basic skill.
