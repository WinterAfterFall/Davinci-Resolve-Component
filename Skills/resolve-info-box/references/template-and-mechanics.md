> **House layout (2026-10-02):** WAF approved a narrower box: `rect.Width` 0.272, 34 px gap to the right edge
> (`rect.Center.X = 1 - 0.017617 - stroke - Width/2`), `Text1.Size` 0.0335, `HeadText.Size` 0.036, wrap body lines
> longer than ~28 base characters (indent the continuation 2 spaces, +0.065 height per added line). Full spec:
> `E:\Youtube\Workspace\WAF\DavinciResolveComponent\Instructor\InfoBox.md`. Prefer it over the older defaults below.

# Pop-up box template — anatomy, control API, and how to probe an unknown comp

## The template comp (`template.comp` in this folder is the exact export)

Built on an **Adjustment Clip** placed on a video track above the footage. The comp's
`MediaIn1` reads the whole timeline below, so the box composites over everything.

Node flow:

```
MediaIn1 (timeline below)
Color_1 (Background, navy #0D2850) ── masked by ─ rect (RectangleMask, CornerRadius 0.15)   ← the box FILL
        └─ stroke (GroupOperator = "Outer Stroke" template: ErodeDilate border #E5B14A + Shadow)
             └─ Merge3 (box graphic, Center expr slides it off-screen-right when rect.Switch<1)
                  └─ Text1 (TextPlus, font "Quark" Bold, left-justified, vertical-centre)
                       └─ Merge5 (text over box; EffectMask = FrameMask; Blend = clamp(min(rect.Switch*2-1, rect.TextSwitch)))
                            └─ Merge6 → Merge1 (over MediaIn1) → MediaOut1
```

`FrameMask` is a second RectangleMask whose `Width`/`Height` are **expression-linked** to
`rect.Width`/`rect.Height`; it clips the text to the box.

## Control API — everything is driven from the `rect` tool

`rect` carries three **user-added** controls (`Center`, `Switch`, `TextSwitch`) plus the
normal RectangleMask `Width` / `Height` / `CornerRadius`.

| input | id | meaning |
|---|---|---|
| open/close | `rect.Switch` | `0` = box parked fully off-screen right, `1` = fully in. **Text only shows once Switch > 0.5** (`Merge5.Blend = rect.Switch*2 − 1`). A 60-frame move ⇒ the box reads as "open" from roughly frame 45–50 of the move — leave a few frames of lead before narration. |
| box width | `rect.Width` | `0.384` fits about **28 Thai / 27 Latin** base characters at `Text1.Size` 0.0412 (render tolerance is generous, ~36–38 units before real clipping). `0.384` is the practical maximum — going wider looks odd. |
| box height | `rect.Height` | `0.102` = 1 line + border, `0.232` = 3 lines + border ⇒ **`H = 0.102 + (lines−1)·0.065`**. `lines` counts the heading. |
| text | `Text1.StyledText` | heading on line 1, then `- ` bullets, `\n`-separated. |
| wipe-out | `Text1.Start` ("Write On Start") | `0→1` wipes the text away from the left. |
| type-on | `Text1.End` ("Write On End") | `0→1` types the text on from the left. |
| font size | `Text1.Size` | global. `0.0412` is the template default; **`0.037`** gives more margin and is a good default for dense Thai bullets. |
| — leave alone — | `rect.Center` (~0.7655, 0.596), `rect.CornerRadius` 0.15, `rect.TextSwitch` 1 | calibrated; only touch `rect.Center` if the user wants the whole box moved. |

## Font "Quark" glyph coverage (matters — wrong glyph renders as a tofu box ▯)

- **Missing**: `→` `➤` `▸` `➔` `➙` and most arrow/dingbat codepoints.
- **Present**: `»` `«` `×` `•` `–` `—` `:` `/` `+` `%` `>` `<` `(` `)` and all ASCII + Thai.
- Use **`»`** for "leads to / then". Use `×` for multiply (e.g. `+Vibes×0.5%`). Use `>` `<`
  only for numeric comparison, and prefer words (`สูงกว่า` / `ต่ำกว่า`) when a line also uses `»`.

## Animation recipe (WAF's spec — this is the house style)

- **New topic / new heading** → *switch*: `Switch 1→0` over 60f · swap `StyledText` during the
  1 closed frame · `Switch 0→1` over 60f. The box physically slides out and back.
- **Same topic, next bullet-set** → *soft write swap*: `Start 0→1` over 30f (with `End` held at 1)
  · swap `StyledText`, set `Start=0` and `End=0` · `End 0→1` over 30f. The box stays put; only
  the text wipes and retypes. Use this when the next beat is a continuation of the same idea.
- Box `Width`/`Height` are re-keyed to the incoming state's values *during* the close/wipe, so
  the resize is hidden by the motion.
- Text always changes while it is invisible (box off-screen, or fully wiped).

`scripts/build_popup.py` implements this recipe — you give it states with a `start` frame and a
`new_topic` flag and it computes every keyframe.

## How to probe a comp you haven't seen (scope: other WAF boxes)

If the user points at a different Adjustment Clip / box, don't assume the input names. Export
and read the comp first:

```
timeline_item_fusion.export_comp(track_type=..., track_index=..., item_index=..., index=1, path="<scratch>/box.comp")
```

Then read `box.comp` and identify:
1. The **master control tool** — a RectangleMask (or Background) with custom `UserControls`
   containing something like `Switch`, or an input that other tools' expressions reference for
   the slide. Its `Width`/`Height` = box size.
2. The **TextPlus tool** name and whether `Start`/`End` (Write On) are free.
3. Any `Merge`/mask **expressions** that reference the switch — that tells you the "text visible"
   threshold and the slide direction.
Fill the `controls` block of the spec from what you find. If the box has no off-screen-slide
switch at all, fall back to animating the TextPlus `Start`/`End` only and the box mask opacity.

## Scripting facts (DaVinci Resolve MCP, Lua via `script_plugin.run_inline`)

- **Keyframes**: `tool.Input = comp:AddTool("BezierSpline", -32768,-32768)` then
  `tool.Input[frame] = value`. Plain `tool.Input[frame] = v` on an *unconnected* input, and
  `SetInput(name, v, time)`, both just set the constant — no keyframe. Default interpolation is
  linear (predictable, no overshoot). Put an equal-value key just before every ramp to hold.
- **Text keyframes have no clean API.** Drive `StyledText` with one string **expression**:
  `time < F1 and "a\nb" or time < F2 and "..." or "last"`. In the expression string, literal
  backslash-n becomes a newline; `time` is the comp-local frame. `build_popup.py` emits this.
- **Apply**: `run_inline(source='dofile([[<abs path>]])')`. `print()` from a dofile'd file is
  swallowed — verify separately by reading inputs back, or by rendering a still.
- **Undo via MCP is unreliable** — don't count on `comp:Undo()`. The generated Lua is
  idempotent instead: re-run it to change anything.
- Save when done: Lua `resolve:GetProjectManager():SaveProject()`.

## Verifying with rendered stills

```lua
local tl = resolve:GetProjectManager():GetCurrentProject():GetCurrentTimeline()
resolve:OpenPage('color')
tl:SetCurrentTimecode(tc); tl:SetCurrentTimecode(tc)   -- call twice: first call after a page switch is dropped
```
then MCP `project_settings.export_frame_as_still(path="<scratch>/chk.png")` and Read the PNG.

Timecode for comp-local frame `f`:  `timeline_frame = clip_start_timeline_frame + f`, then
`seconds = (timeline_frame − timeline_start_frame) / fps`, format `HH:MM:SS:FF`. For the WAF
"Nigga" timeline: timeline start = frame 216000 = `01:00:00:00`, 60 fps.
