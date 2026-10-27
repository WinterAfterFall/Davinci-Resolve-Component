---
name: resolve-info-box
description: >-
  Build WAF's animated Info Box (the navy-and-gold caption box that slides in from the right,
  formerly called the "pop-up box") inside the Fusion comp of a DaVinci Resolve Adjustment
  Clip, synced to what the narrator actually says. Use this whenever the user gives a
  subtitle/SRT file plus a video section or clip name (e.g. "ทำ info box ช่วง 3.mp4",
  "ทำ pop up box ช่วง 3.mp4", "caption the skills section", "adjustment clip ที่เปิดอยู่",
  hands over a "[...] DownSub" SRT, or references the info box / pop-up box / caption box /
  text box / กล่องข้อความ / บับเบิล in a Resolve guide-video project). Covers parsing the
  (often garbled auto-generated) SRT against a rough script for vocab, segmenting the
  narration into topic + bullet states, writing tight caption text, and keyframing the box's
  slide / write-on / resize animation via the davinci-resolve MCP. Also use it to tweak an
  existing Info Box build. Not for the big centred "Popup Text Box With Title" macro.
---

# Resolve Info Box (caption box)

The user edits guide videos (HoYo games) in DaVinci Resolve. Each section of narration gets a
navy-with-gold Info Box on the right that lists the key points, animated to appear as the
narrator reaches each point. The box lives in the Fusion comp of an **Adjustment Clip** and is
driven by a small set of controls. This skill takes an SRT of the real narration + which
section to caption, and produces the finished animation.

## What the user provides

- An **SRT** (usually auto-generated, e.g. `[Thai (auto-generated)] … [DownSub.com].srt`) — the
  actual spoken narration and its running order.
- **Which part to caption** — a clip name (`3.mp4`), a section ("the skills part"), or "the
  adjustment clip that's open" in Resolve.
- Optionally a **rough script** (`message.txt`, a Google-doc dump) — outline only, but the
  correct spelling of every name / term / number. SRT order wins; script vocab wins.

The **davinci-resolve MCP** must be connected and the project open in Resolve.

## Workflow

1. **Map frames.** Timeline + fps (WAF: "Nigga" timeline, 60 fps, starts frame 216000 =
   `01:00:00:00`). Find the Adjustment Clip's timeline span; its comp-local frame 0 = its
   timeline start frame. Work out `comp_frame ↔ srt_seconds ↔ timecode`.
   → details in `references/writing-captions.md` §1.

2. **Confirm the box.** If it's "the open clip", verify the Fusion page and which clip. If it's
   a box you haven't seen, `export_comp` and read it to find the real control input names.
   → `references/template-and-mechanics.md` (control API + "how to probe an unknown comp").

3. **Read both files.** Clean the garbled SRT terms using the script's vocabulary. Flag any
   number where SRT and script disagree.

4. **Segment + write.** Group the narration into topics (new headings) and sub-states
   (successive bullet sets within a topic). 3–4 lines per state. Write tight `- ` bullets in the
   SRT's language, ≤ ~30 Thai chars/line, `»` not `→`.
   → `references/writing-captions.md` §3–4.

5. **Present the plan and wait for approval.** A table of every state: text, line-count →
   height, width, `start` frame + timecode, and the transition type between states. The user
   signs off (or says "ลุยเลย" to skip). Don't touch the comp before this.

6. **Generate + apply.** Build `spec.json` and run:
   ```
   python <skill>/scripts/build_popup.py spec.json out.lua
   ```
   then apply through the MCP:
   ```
   script_plugin.run_inline(language="lua", source='dofile([[<abs path>/out.lua]])')
   ```
   The Lua is idempotent — it wipes and rebuilds every spline each run.

7. **Verify with stills.** Render frames (Color page, `SetCurrentTimecode` twice, then
   `project_settings.export_frame_as_still`) — one settled frame per topic, one mid-transition,
   one before first open, one after final close. Check text fit, glyphs, height, timing.
   Fix `spec.json`, regenerate, re-run `dofile`.

8. **Finish.** `resolve:GetProjectManager():SaveProject()`. Save `spec.json` + `out.lua` beside
   the project (`D:\Video\WAF-info-box\`) for the next edit.

## The control API (summary — full detail in references/template-and-mechanics.md)

Everything is on the `rect` tool of the template comp:

| control | effect |
|---|---|
| `rect.Switch` 0→1 | slide box in/out. Text shows only when Switch > 0.5. 60-frame move. |
| `rect.Width` | box width. 0.384 ≈ 28 Thai chars; that's the practical max. |
| `rect.Height` | `0.102 + (lines−1)·0.065`. |
| `Text1.StyledText` | driven by a `time`-based string expression (no clean keyframe API for text). |
| `Text1.Start` / `Text1.End` | Write-On start/end — wipe-out / type-on. |
| `Text1.Size` | global font size; `0.037` is a good default. |

Animation: **new topic** → switch out (60f) · swap text · switch in (60f). **Sub-state** →
wipe-out `Start` (30f) · swap text · type-on `End` (30f), box stays. `build_popup.py` computes
all of it from `start` + `new_topic` per state.

Font is "Quark": it has `» × • –` but **not** `→ ➤ ▸` (they render as ▯). Use `»`.

## Title box (added 2026-10-02, Pearl project)

Comps can carry a separate **title box** sitting on the top edge of the box: `HeadRect`
(Width = `rect.Width`, Center Y = `rect.Center.Y+rect.Height/2`, Height 0.075, CornerRadius 0.6)
→ `HeadColor` → `HeadStroke` (copy of `stroke`) → `HeadBoxMerge` (slides with the box) and
`HeadText` → `HeadTextMerge` (centred in the title box, Blend gated by Switch).
When it exists:
- put the heading in each state's `"title"` and only the bullets in `"text"`; add
  `"title_tool": "HeadText"` to `controls`. The title swaps at the same frames as the text.
- half the title box overlaps the content, so use `"height": {"base": 0.1395, ...}` and set
  `Text1.Center = Point(Merge3.Center.X+0.02-rect.Width/2, Merge3.Center.Y-HeadRect.Height/4)`.
- run the generated Lua with `comp:Execute()` on the target comp (it uses the global `comp`),
  not on whatever comp happens to be open in Fusion.
- never leave a bare `"` in caption text unescaped — `build_popup.py` escapes it now; before
  that fix a quote blanked the whole StyledText.
Two-stage open (same `rect.Switch` keys, no extra splines): Switch 0→0.5 slides **only the title**
in from the right; 0.5→1 drops the **body down from behind the title**. With
`S1 = clamp(Switch*2)`, `S2 = clamp(Switch*2-1)`, `D = (1-rect.Center.X+rect.Width/2+stroke.Input2)`,
`DY = (rect.Height+0.03)`:
- `HeadBoxMerge.Center = Point(0.5+D*(1-S1), 0.5)`; `HeadTextMerge.Center` x the same, Blend `clamp(Switch*4-1)`.
- `Merge3.Center = Point(0.5+D*(1-S1), 0.5+(1-S2)*DY)` with EffectMask `BodyClip` (RectangleMask,
  Width 1, Height = top edge `rect.Center.Y+rect.Height/2`, Center `Point(0.5, top/2)`) so the body is
  hidden above the top edge.
- `Merge5.Center` follows Merge3; `FrameMask` stays put vertically and covers only the area under the
  title, starting below its gold border (`Height = rect.Height-HeadRect.Height/2-0.018`, Center y
  `rect.Center.Y-HeadRect.Height/4-0.009`), else the dropping text draws over the title / its border. `Text1.Center = Point(0.52-rect.Width/2, 0.5-HeadRect.Height/4)`.
Closing plays it backwards (body up behind the title, then the title slides out).

Worked example: `D:\Video\WAF-info-box\pearl_make_spec.py` → `pearl_spec.json` → `pearl_info_box.lua`.
