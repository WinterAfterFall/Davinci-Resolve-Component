---
name: resolve-section-transitions
description: Put WAF's section transitions between the numbered recording clips (1.mp4, 2.mp4, 3.mp4 …) of a DaVinci Resolve guide-video timeline — IntroduceTransitionV1 between clip 1 and 2, Transition2.0 between every other pair — on Adjustment Clips on the top video track, with the section title the user gives. Use this whenever the user asks to add/check/fix transitions, "ใส่ทรานซิชัน", "คั่นระหว่างคลิป", "transition ระหว่าง section", "ใส่ Title หัวข้อ", mentions IntroduceTransitionV1 / Transition2.0 / Transition20, gives a list of section titles for clips, or wants the transition Adjustment Clips placed, verified against the 34/27-frame overlap rule, or retitled — even if they don't name the macros.
---

# Resolve section transitions (WAF)

WAF's HSR guide videos are cut from numbered recordings `1.mp4`, `2.mp4`, … Every cut between two
consecutive recordings gets a navy/gold transition that covers the cut and shows the next
section's title. Each transition is an **Adjustment Clip on the top video track** whose Fusion comp
holds one of two macros (from `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Macros\`):

| cut | macro | clip length | title tool |
|---|---|---|---|
| 1 → 2 | `IntroduceTransitionV1` | **367 f** | `Title` (then "Presented by" + image 1, flip, "Winter After Fall" + image 2) |
| every other n → n+1 | `Transition2.0` (group `Transition20`) | **210 f** | `Test_TextPreview` |

Clip order is by **filename number**, not timeline position. The macros' animation is baked to
comp frames at 60 fps, so the clip must start exactly where the transition should start.

## The overlap rule and default placement

Let `C` = the cut (first frame of clip n+1) and `S` = the Adjustment Clip's start.

- **at least 34 frames before the cut** (`C − S ≥ 34`): the three circles need that long to cover the
  screen, so the cut stays hidden.
- **at least 27 frames after the cut** (`S + length − C ≥ 27`): the closing ellipse starts revealing
  the picture about 27 frames before the clip ends, and that picture has to be the new clip.
- **Default when the user gives no position: `S = C − 34`.** The user can ask for other offsets per
  cut (`offsets` in the config); anything inside the rule is fine.

## Fonts

- Default `Open Sans` Bold (the titles are normally English: "Ability", "Build", "Aventurine\nGuide").
- If a title contains Thai and the user named no font, use **`Sukhumvit Set`** Bold (installed per-user).
  The script does this automatically; an explicit font from the user wins.

## Why a script, and what the API cannot do

The Resolve API **cannot create an Adjustment Clip or move a clip** to a track/frame. So the skill
works in two modes, chosen by what's on the top track:

- **No Adjustment Clip across a cut** → compute the placement and drop a **timeline marker** at `S`
  with duration = clip length (pink = intro, cream = transition). The user drags an Adjustment Clip
  onto the top track snapped to that marker and trims it to the marker length, then says so.
- **Adjustment Clip already there** (placed roughly by the user or from an earlier pass) → match it
  to the cut it straddles, check the rule and length, report anything wrong, then fill it.

Filling = import the template comp (`assets/*.comp`, exported from working clips) with
`ImportFusionComp`, then set Title / font / images on the imported tools. Import matters: a comp
built with `AddFusionComp` + `AddTool` reads back fine but Resolve does not render it; an imported
comp renders immediately. Tools inside pasted macros carry `_1`, `_2` suffixes, which the script
handles by matching base names.

## Workflow

Paths: `SKILL_DIR = C:\Users\ADMIN\.claude\skills\resolve-section-transitions`. Every step runs
`scripts/transitions.lua` through the davinci-resolve MCP:

```lua
-- script_plugin.run_inline(language="lua", source = this)
local cfg = { mode = "plan", assets = [[SKILL_DIR\assets\]] }
local ok, lines = pcall(assert(loadfile([[SKILL_DIR\scripts\transitions.lua]])), cfg)
print(ok and table.concat(lines, "\n") or ("ERROR " .. tostring(lines)))
```
Pass the config as the argument and print the returned lines. `run_inline` sandboxes globals (a
global set in the inline source is invisible to a loaded file) and swallows `print` from inside
it, so `WAF_TR = …; dofile(…)` silently runs with an empty config — it looks like plan mode.
The config fields are listed at the top of `scripts/transitions.lua`.

1. **Plan (read-only).** `mode = "plan"`. It lists every cut in filename order with kind, cut
   frame/timecode, planned start, any Adjustment Clip already across it (before/after frames, length,
   OK or BREAKS, current macro + title), plus unmatched Adjustment Clips on the top track and notes
   such as *OUT OF ORDER*, *gap between clips*, *runs past end of clip*. Show the user a compact table.
   Out-of-order or gapped clips usually mean the edit isn't finished — ask before going on.

2. **Titles.** The user supplies the title per section ("Title จะบอกให้"). Key them by the number of the
   clip *after* the cut: `titles = { [2] = "Aventurine\nGuide", [3] = "Ability", [4] = "Build" }`.
   Don't invent titles; ask for missing ones. Break long titles into balanced lines yourself
   (`"Teammate Score\nMain Dps"`); at size 0.22 a line of ~14 Open Sans Bold characters
   ("Teammate Score") spans the whole 1920 px frame, so drop such clips to `sizes = { [n] = 0.17 }`.
   Always confirm line breaks and width on the stills. For the intro also confirm the two image paths if the
   user wants different ones (`images = { profile1 = …, profile3 = … }`, defaults are
   `E:\Youtube\Image\Work\profile1.png` / `profile3.png` already in the template).

3. **Markers for missing clips.** `mode = "markers"` (+ `titles` so the marker note shows the title).
   Tell the user which markers to fill, the length for each (367 / 210), and that they go on the top
   video track. Wait for them. Re-run plan afterwards; clear markers with `mode = "clear_markers"`
   once every cut has its clip.

   **Layout markers (user's preferred way to rebuild a sequence).** `mode = "layout"` keeps clip 1 where
   it is and chains everything from the clips' current lengths: transition n→n+1 starts **34 f before
   clip n ends**, clip n+1 starts **21 f before that transition ends** (`lead` / `tail` to override).
   It drops a blue 1-frame marker at every planned clip start and a pink/cream marker (length = clip
   length) at every planned transition start; the user then drags clips and Adjustment Clips onto
   them. Nothing is moved by the script. Note `tail = 21` is tighter than the 27-frame check that
   `plan` reports — the user chose it, so don't "fix" it; if `plan` flags *after cut 21f < 27* on a
   layout built this way, that's expected. If the pop-up box Adjustment Clip sits over clip 3, remind
   the user it must move to clip 3's new start too. Run `clear_markers` before re-running layout.

4. **Apply.** `mode = "apply"` with `titles` (and `fonts`, `images`, `only` as needed). Clips that break
   the rule are skipped and reported — fix placement, or pass `force = true` only if the user
   explicitly accepts it. `reimport = true` rebuilds a clip from the template (resets any hand
   tweaks inside it); leave it off to just retitle. `direct = { { id = …, kind = "transition", n = 5 } }`
   fills a specific Adjustment Clip by unique id when the user points at one.

5. **Verify with stills.** `mode = "stills"`, `out_dir = <scratchpad>\`. Transition2.0 → frame +120
   (title settled); intro → +100 (title) and +300 ("Winter After Fall" + image). Read the PNGs: title
   spelled right, no tofu boxes (wrong font for Thai), text not clipped, images present.
   Report what you actually saw.

6. **Save.** `resolve:GetProjectManager():SaveProject()` — only when the project name isn't
   "Untitled Project" (that call hangs on an unsaved default project).

## Gotchas

- Timelines here are 60 fps. At another rate the macros play at the wrong speed; tell the user
  rather than stretching clips.
- A clip number split into several pieces is treated as one span (first start → last end); the plan
  flags it.
- Markers are timeline-wide; if one already sits on the same frame `AddMarker` fails — the script
  reports it.
- `Test_TextPreview` inside the intro is expression-driven from `Title`; always set `Title` for the intro.
- The template comps capture the user's current tweaks (intro title size 0.185, transition 0.22). If
  the user changes the macro look on the timeline and wants it everywhere, re-export that clip with
  `ExportFusionComp` into `assets/` to refresh the template.
