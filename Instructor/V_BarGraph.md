# V_BarGraph: vertical bar (one column per instance)

File: `E:\Youtube\Workspace\WAF\DavinciResolveComponent\component\V_BarGraph.setting` (also in Fusion `Macros\`). Group, internal names `Bar_*` (renamed from `VB_*` on 2026-10-01 at the user's request; a comp that still has a pasted `VB_*` copy must be re-pasted).
Derived from comp 3 in project "Motion Graph (Copy)" (horizontal bar with GC / Label / ConnectedImage / Popup).
Status: **written 2026-10-01, not yet tested in Resolve.**

## Changes vs the horizontal bar
- Bar grows **up** from the baseline (`BottomMargin`) instead of right. `Rows` became `Columns`.
- One image slot instead of 4 (single Dissolve slot, no ConnectedImage group). The image is centred on the baseline under its bar.
- Value label sits **above the bar top** (not inside the bar, no bar-alpha mask) and rides up with it.
- End-cap ellipse `C` removed, so the bar width no longer subtracts `Height*9/16/2`. `YLine` removed.
- New baseline: `Bar_Base` mask + `Bar_BaseColor`. Each instance draws only its own column slot `(1-L-R)/Columns`,
  so instances side by side form one continuous line. **Timing is sequential by Position** (one sweep left→right) inside the
  Baseline phase of Visibility: `BaseGrow = clamp(Visibility*TotalTime/BaseTime - (Position-1), 0, 1)`;
  the segment is left-anchored in its slot (`x = L + slot*(Position-1+BaseGrow/2)`, `Width = slot*BaseGrow`), so **Baseline Time is per column** (every segment
  takes the same time; the whole sweep = BaseTime*Columns, user request 2026-10-01). One unbroken sweep needs the same Visibility timing, BaseTime and Columns
  on every instance. History: v1 grew each segment from its own centre (5 bars = 5 odd growth points, rejected);
  v2 used comp `time` with Start Frame/Duration, but the baseline showed no animation, so the user asked for a Baseline
  Time phase instead.
- `LeftText`/`StrokeV1_1`/`Merge3` removed.
- Growth is eased (ease-out cubic). The label count-up uses the same `Grow`, so they stay in sync.

## Structure (spine Bar_M1 → Bar_M4 = group output)
- `Bar_GC` RectangleMask: the bar shape and **all controls** (Controls page) plus computed `TotalTime`, `Pop`, `Grow` (Calc page).
- `Bar_BorderMask` (copy of Bar_GC's centre/size/corner, `BorderWidth` = Border Size, 0 while the bar height is 0) → `Bar_BorderColor`
- `Bar_BarFill` Merge: BG `Bar_BorderColor`, FG `Bar_BarColor` (EffectMask Bar_GC), so the border shows as a rim around the bar
- `Bar_BarFill` → `Bar_BarShadow` → `Bar_M1` (BG `Bar_Canvas` transparent)
- Corners: `Bar_GC.CornerRadius` default 0.3 (rounded); the border mask follows it.
- `Bar_Base` → `Bar_BaseColor`; `Bar_BaseBorderMask` (same centre/width as Bar_Base, Height = BaseThickness + BorderSize, i.e. a
  rim of **half the bar's Border Size** above and below) → `Bar_BaseBorderColor` (white); `Bar_BaseFill` = border under line → `Bar_M2`
  (Blend = ShowBaseline). The rim is top/bottom only: no left/right border, so no white seams between column segments.
- `Bar_Label` → `Bar_LabelStroke` (hard DropShadow "stroke", FontValue) → `Bar_M3` (Blend fades in over the first 1/8 of GraphTime)
- `Bar_EmptyImage` (64x64 transparent) + image → `Bar_ImgSlot` Dissolve (Mix = UseImage), so Bar_ImgPlace always has a Foreground
- `Bar_ImgCanvas` + `Bar_ImgSlot` → `Bar_ImgPlace` (Merge Size/Center place the image) → `Bar_ImgShadow` → `Bar_ImgPop` (pop curve about the image centre) → `Bar_M4` (Blend = UseImage)
Group output = Bar_M4 (bar on a transparent 1920x1080 canvas); merge it over the scene yourself.
Group input: MainInput1 = Image (optional).

v1 (first paste) turned red: `Bar_Out` Merge had no Background, and `Bar_ImgPlace` expressions read
`Foreground.Width` with no image plugged. v2 removed Bar_Out and added the empty-image slot.

## Formulas (Bar_GC)
- X centre = `L + (1-L-R)/Columns*(Position-0.5)`
- Outer bar box incl. border (Calc page): `BarW = (1-L-R)/Columns*(1-Padding)`, `BarH = (1-Top-Bottom)/(Max-Min)*(Value-Min)*Grow`
- Fill mask = `BarW x (BarH + BottomExt)`, Centre Y = `Bottom + (BarH - BottomExt)/2` (no stroke subtraction: tried and reverted).
  `BottomExt = BarW/2` in height units = the largest possible corner radius, so the bottom rounding always sits below the
  baseline cut and only the **top corners** look rounded (user request).
- `Bar_BarClip` RectangleMask is the EffectMask of `Bar_M1`: it keeps only y > `Cut` = top edge of the baseline incl. its border
  (`Bottom + (BaseThickness + BorderSize)/2`, or just `Bottom` when Show Baseline is off). So the rounded bottom corners,
  the bottom border and the shadow below the line disappear under the baseline.
- Phases of Visibility 0→1: **Baseline Time → Image Pop Up Time (TitleTime) → Graph Time**, `TotalTime = BaseTime*Columns+TitleTime+GraphTime` (weights, not frames)
- Pop = `(Visibility - BaseTime*Columns/TotalTime)/(TitleTime/TotalTime)` clamped 0..1 (image pop)
- Grow = 0 until the Baseline and Image phases end, then `1-(1-t)^3` over GraphTime; the label fades in over the first 1/8 of it
- Label Centre = `(X, Bottom + Height + LabelGap)`, anchored bottom-centre, Size = `Width*LabelScale`
- Image width = `Width*ImageSize` (pixels via `Background.Width/Foreground.Width`), Centre = `(bar X, Bottom + ImageGap)`: the image is **centred on the baseline** by default (user choice 2026-10-01). `ImageGap` is shown as Offset Y (+ up / - down), default 0

No expression cycles: Bar_ImgPlace reads only its own Foreground (plugged image) and Background (empty canvas).

## Untested assumptions
- Dissolve output takes the plugged image's resolution when Mix = 1 (the user's ConnectedImage relies on the same).
- `VerticalTopCenterBottom = 1` means "anchor bottom" (text grows upward from the point). If the label
  sits inside the bar top, set it to -1.
- RectangleMask Height is in frame-height units (inferred from the user's GC formulas).
- Label size and colour defaults (0.55 × bar width, light grey + black stroke) are guesses.

## Inspector layout (v3)
Group controls are grouped under collapsible LabelControl headers: Animation, Value, Layout, Bar, Label,
Image, Baseline, spread over Inspector tabs (InstanceInput `Page`): **Controls** = Animation + Value,
**Layout** = Layout, **Style** = Bar + Label + Baseline, **Image** = Image (plus Fusion's own Settings tab).
Each tab's inputs must stay contiguous in the Inputs list. The headers are user controls `Hdr*` on `Bar_GC` with `LBLC_NumInputs` = number of published
inputs that follow (a colour counts as 3: R, G, B). When adding/removing a published input, update that count.
- Label section (Style tab) also publishes `Bar_Label.Font` + `Style` (shown as Font / Weight, ControlGroup 3) and
  `Bar_LabelStroke.FontValue` (Stroke Thickness). `HdrLabel` LBLC_NumInputs = 7. `HdrBar` = 8 (Bar Color 3, Corner Radius, Border Size, Border Color 3). `HdrBaseline` = 8 (Show, Thickness, Color 3, Border Color 3).
- "Bar Gap" in the Inspector = `Bar_GC.Padding` (fraction of the column slot left empty).
- `TitleTime` is shown as **Image Pop Up Time** in the Inspector (internal id unchanged; it now only drives the image pop).
- Bug fixed (2026-10-01): `Bar_ImgPop` had Center = Pivot = image position. In Fusion, Transform **Center is a translation** (0.5,0.5 = no move); only Pivot is the scale origin. So the image was shifted by (pos - 0.5) and left the frame. Now Center = (0.5,0.5), Pivot = `Bar_ImgPlace.Center`.
- **Baseline Slot** (Style → Baseline, `Bar_GC.BaseSlot`, default 0): the slot this instance's baseline segment
  occupies and its turn in the sweep (`BaseIdx = BaseSlot >= 1 ? BaseSlot : Position`). Set it whenever Position is
  ANIMATED (bars swapping places): otherwise each segment travels with its bar and the line breaks mid-swap
  (seen 2026-10-01 in Pearl Main). Give the instances a permutation 1..Columns. `HdrBaseline` LBLC_NumInputs = 9.
- Pearl Main (old `VB_*` copies, no BaseSlot control): fixed by replacing `Position` with the constant slot in
  `VB_Base<s>.Center` and `VB_GC<s>.BaseGrow` (LC 1, E1 2, E2 3, E4 4, E6 5).
- **Whole Line** (Style → Baseline, `Bar_GC.BaseFull`): this instance draws the ENTIRE baseline, sweeping left→right over
  `BaseTime*Columns` (`BaseAll`). Recommended multi-bar setup: tick Whole Line + Show Baseline on the instance that is the
  BOTTOM layer of the merge, untick Show Baseline on all others. Otherwise each instance's segment is merged above the
  previous instances' images and covers them (seen 2026-10-01: line over the eidolon portraits). `HdrBaseline` = 10.
- The bar clip `Cut` no longer depends on Show Baseline: bars always stop at the top edge of the line, even when another
  instance draws it.
- Pearl Main: `Bar_1` (E2, bottom layer of MultiMerge1) draws the whole line; the others have Show Baseline off.
