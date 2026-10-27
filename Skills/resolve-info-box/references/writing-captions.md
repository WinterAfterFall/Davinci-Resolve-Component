# Turning an SRT into synced pop-up caption states

## 1. Establish the frame mapping

- Get the timeline + fps: `timeline.get_current`, and fps from `template.comp` `FrameFormat.Rate`
  or the project settings (WAF: 60 fps, timeline starts frame 216000 = `01:00:00:00`).
- Get the Adjustment Clip's timeline span (`timeline.get_items_in_track`). The clip's **comp-local
  frame 0 = its timeline start frame**. So:
  `comp_frame = srt_seconds * fps − (clip_start_timeline_frame − timeline_start_frame)`
- `clip_end` for the spec = clip duration in frames.

If the user says "the clip that's open" — check `resolve_control.get_page` is `fusion` and use
`fusion_comp.get_tool_list` / `MediaOut1` region to confirm which clip, then find it on the tracks.

## 2. Read both files

- **SRT** = what was actually said, and the running order. Auto-generated SRTs are heavily
  garbled (names, game terms, numbers) — never trust the spelling.
- **Script / brief** (if provided) = the vocabulary source of truth: proper names, term
  capitalisation, correct numbers. Cross-check every name and figure against it.
- If SRT and script disagree on a number, the script is usually right (the SRT mis-hears digits);
  flag it in the plan so the user can confirm.

## 3. Segment into topics and sub-states

Walk the SRT for the target range. Group consecutive lines into **topics** (a distinct mechanic
or heading the narrator moves onto) and, within a long topic, **sub-states** (successive bullet
sets as the explanation builds).

- A topic = a new heading. A sub-state = same heading, next detail.
- Aim for **3–4 lines per state** (heading + 2–3 bullets). If a topic has more, split into
  sub-states rather than one tall box.
- Each state's `start` = the comp frame of the SRT line where that content begins to be spoken.
  The box will be fully open a few frames before that.
- Topics are usually tens of seconds to minutes apart — plenty of room. Sub-states within a
  topic need ~65 frames of gap minimum (30 wipe + swap + 30 type). If the narration moves
  faster than that, merge beats.

## 4. Write the bullet text

Pattern, `\n`-separated, no trailing spaces:

```
<heading>
- <point 1>
- <point 2>
```

- **Language follows the SRT** (Thai narration → Thai bullets) unless the user briefs otherwise.
- Use the script's vocabulary: real names (Bessie, Drummie, Paddie, Summer Songbirds…), term
  casing (Vibes, Groove, Fever, Special Guest, Light Cone…), correct numbers.
- **Keep each line short.** Target ≤ ~30 Thai base characters (≈ `rect.Width` 0.36–0.384).
  Trim particles, drop redundant context, use `»` for "→". Long explanatory clauses become two
  short bullets. If you truly can't fit, that state's `width` can go to 0.384 and/or note that
  `Text1.Size` may need nudging — but shortening the line is almost always better.
- `»` = "leads to / then". `×` = multiply. Never use `→` (tofu in font Quark — see
  template-and-mechanics.md).
- Headings can use `»` as a separator: `Vibes » Deviated Chords`, `Fever » หัก Vibes`.

## 5. Build the spec and present the plan

Assemble `spec.json` for `scripts/build_popup.py` (see its docstring). Per state: `id`, `text`,
`start` (comp frame), `new_topic` (bool), optional `width`.

**Before writing anything into the comp**, show the user a plan: a table of every state with
its text, line count → height, width, and `start` frame / timecode, plus the transition type
between each. Wait for approval (or "ลุยเลย" to skip). This is cheap insurance — the text and
segmentation are the subjective part and redoing ~200 keyframes is not fun.

## 6. Generate, apply, verify

```
python scripts/build_popup.py spec.json out.lua
# then via MCP:
script_plugin.run_inline(language="lua", source='dofile([[<abs path>/out.lua]])')
```

Read back a few inputs to confirm the splines connected and the expression is set. Then render
stills (see template-and-mechanics.md) at:
- one settled frame per topic (mid-hold),
- one mid-transition (box sliding / text typing),
- one frame before the first open and one after the final close (box should be absent).

Check for: text clipping past the box edge (widen or shorten), tofu glyphs, box height vs line
count, timing vs narration. Fix in `spec.json`, regenerate, re-run `dofile` (idempotent).

Finally: `resolve:GetProjectManager():SaveProject()` and keep `spec.json` + `out.lua` next to
the project (e.g. `D:\Video\WAF-info-box\`) so the next edit starts from the last spec.

## Worked example

`references/example_full_build.py` is the actual generator used for the first job (3.mp4, the
Skills section of the Robin Summeretto guide): 21 states / 11 topics over 16992 frames. It
predates `build_popup.py` (it hand-lists transitions) but the `states` list is a good model for
segmentation, line length, and vocabulary.
