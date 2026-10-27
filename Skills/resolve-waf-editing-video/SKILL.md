---
name: resolve-waf-editing-video
description: WAF's editing rules for DaVinci Resolve guide videos — how a timeline is laid out from the numbered recordings (1.mp4, 2.mp4 …) and how far a section transition must overlap the clip before the cut and the clip after it (34 frames before, 27 after; layout uses 34 / 21), plus the transition clip lengths (IntroduceTransitionV1 367 f, Transition2.0 210 f). Use this whenever the user asks about editing a WAF video, "ตัดต่อ", "เรียงคลิป", "ทรานซิชันเหลื่อมกี่เฟรม", "ทรานซิชันควรทับคลิปก่อน/คลิป 2 เท่าไหร่", "วางทรานซิชันตรงไหน", "จัดไทม์ไลน์", or wants to check that a timeline follows WAF's rules — even if they don't name a macro. For actually placing or filling the transitions, hand off to the resolve-section-transitions skill.
---

# WAF video editing rules (DaVinci Resolve)

WAF's guide videos are cut from numbered recordings `1.mp4`, `2.mp4`, … on the timeline, ordered
by **filename number**, not by timeline position. The project runs at **60 fps**; every frame count
below is at 60 fps.

## Section transitions

Every cut between two consecutive recordings gets a transition: an **Adjustment Clip on the top
video track** holding a Fusion macro.

| cut | macro | clip length |
|---|---|---|
| 1 → 2 | `IntroduceTransitionV1` | **367 f** |
| every other n → n+1 | `Transition2.0` (group `Transition20`) | **210 f** |

### How much it must overlap each clip

Let `C` = the cut (first frame of clip n+1) and `S` = the transition clip's start.

- **Overlap the clip before the cut by at least 34 frames** (`C − S ≥ 34`). The three circles need
  that long to cover the whole screen, so the cut stays hidden.
- **Overlap the clip after the cut (clip 2) by at least 27 frames** (`S + length − C ≥ 27`). The
  closing ellipse starts revealing the picture about 27 frames before the transition ends, and the
  picture it reveals must already be the new clip.
- **Default when the user gives no position: `S = C − 34`.** That leaves 333 f over the next clip for
  the intro and 176 f for `Transition2.0`. Other offsets are fine as long as both minimums hold.

### Rebuilding a whole sequence (layout)

When the user rebuilds the timeline from scratch, they chain it like this:

- the transition starts **34 f before clip n ends**
- clip n+1 starts **21 f before that transition ends**

The 21 f here is tighter than the 27 f minimum above. The user chose it on purpose, so don't
"fix" it, and treat an *after cut 21f < 27* warning on such a layout as expected.

### Doing the work

Placement, markers, checks and titles are handled by the **resolve-section-transitions** skill
(`scripts/transitions.lua`, modes `plan` / `markers` / `layout` / `apply`). The Resolve API cannot
create Adjustment Clips or move clips, so the user drags them onto the markers that skill drops.

## Related WAF skills

- `resolve-info-box`: the navy-and-gold Info Box captions synced to the narration
- `resolve-bar-graph`, `resolve-hsr-compare-graph`: bar-graph and compare-graph scenes
- `resolve-pie-chart`: damage-source pie charts
- `resolve-basic`: house rules for any Resolve / Fusion work, incl. building new Fusion components safely (§7)

## Adding rules

When the user states a new editing rule (timing, track layout, spacing), add it here under a
matching heading, with the reason they gave, so it is not lost between sessions.
