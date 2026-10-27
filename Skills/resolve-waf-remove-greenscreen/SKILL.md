---
name: resolve-waf-remove-greenscreen
description: Remove WAF's green screen (#00ff42) from the numbered recording clips (1.mp4, 2.mp4 …) of a DaVinci Resolve guide video by putting a Delta Keyer named DeltaKeyer_Green between MediaIn1 and MediaOut1 in each clip's Fusion comp, with Background Color set to #00ff42 (R 0, G 1, B 0.2588). Use this whenever the user asks to key out / remove the green, "ลบเขียว", "เอาสีเขียวออก", "รีมูฟสีเขียว", "ใช้เดลต้าคีย์เยอร์", "Delta Keyer", "green screen", "#00ff42", or wants the same key copied to more clips — even if they don't name the node.
---

# Remove green screen (WAF)

WAF records with a flat green backdrop of exactly **#00ff42**. Each recording clip on the timeline
gets its own Delta Keyer in its Fusion comp so the green turns transparent.

## The approved node setup

Taken from the working clip `2.mp4` in the **Pearl** project (timeline `Main`, track V5):

```
MediaIn1 ──► DeltaKeyer_Green ──► MediaOut1
```

| DeltaKeyer_Green input | value |
|---|---|
| `BackgroundRed` | **0** |
| `BackgroundGreen` | **1** |
| `BackgroundBlue` | **0.258823529411765** (= 66/255) |
| everything else | Fusion default (`Gain` 1, `PreBlur` 0, `LowThreshold` 0, `HighThreshold` 1, `SpillSuppression` 1) |

Use the same node name `DeltaKeyer_Green` on every clip so a later pass can find it by name.
If the user tunes the key on one clip (thresholds, erode, spill) and wants it everywhere,
read those inputs back from that clip and copy them; don't guess new values.

## Before touching anything

1. **Check the project and timeline.** Run `project_manager get_current` and `timeline get_current`.
   The user switches projects between turns. If they aren't the ones the request is about, stop and ask.
2. **Find the clips by filename number** (`timeline clip_where name_contains=".mp4"`, video only).
   Clips that are split in pieces are separate timeline items; each piece has its own comp and
   needs its own keyer.
3. **Skip clips that already have it.** `fusion_comp find_tool name="DeltaKeyer_Green"` on the item.
   If it's there, just check the three Background values.

## Applying it (per clip, via the davinci-resolve MCP)

Address the comp with `timeline_item_id` (from `clip_where`) so the right item is hit even if
track order changes. `script_plugin run_inline` no longer exists in this MCP, so use the
`fusion_comp` actions:

0. If `fusion_comp get_tool_list` says *Timeline item has no Fusion compositions*, first run
   `timeline_item_fusion add_comp` on that item (by `track_type` / `track_index` / 0-based
   `item_index`; check the order with `timeline get_items`). The new comp holds just MediaIn1 →
   MediaOut1. Its internal name may read `Composition2`, but the item still lists one comp, `Composition 1`.
1. `add_tool` `tool_type="DeltaKeyer"`, `name="DeltaKeyer_Green"`.
2. `set_input` the three Background values above.
3. `connect` `target_tool="DeltaKeyer_Green"`, `input_name="Input"`, `source_tool="MediaIn1"`.
4. `connect` `target_tool="MediaOut1"`, `input_name="Input"`, `source_tool="DeltaKeyer_Green"`.
5. Read it back with `probe_fusion_tool` and confirm the wiring: MediaOut1.Input ← DeltaKeyer_Green,
   DeltaKeyer_Green.Input ← MediaIn1.

These per-clip comps are tiny (MediaIn, two AudioDisplay nodes, MediaOut), so direct editing is
safe here. The "no live scripting" rule from `resolve-basic` §7 is about the big
graphics comps.

## Verify it really renders

On Resolve 21 a node added through the API can read back correctly yet not show in the
output. Comp readback is not proof. After applying, ask the user to look at the clips on the
Edit page (green gone, background visible through), or grab a still with `gallery_stills`.
Report only what was actually seen. If a clip still shows green, the fallback is to have the user
copy `DeltaKeyer_Green` from a working clip and paste it into that clip's comp in Fusion.

## Related skills

- `resolve-waf-editing-video`: timeline layout rules for the same recordings
- `resolve-basic`: safety rules for scripting Fusion (§7)
