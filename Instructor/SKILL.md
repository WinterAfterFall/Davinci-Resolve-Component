---
name: davinci-resolve-instructor
description: >-
  Main use: IMPLEMENTING A NEW FUSION COMPONENT (a new reusable node set or panel for a
  DaVinci Resolve guide video, e.g. NoteBox) the safe way, as a Group .setting file that the user
  pastes, tests, and then swaps in for the old nodes. Also the safe method for changing node
  setups in Fusion comps through the davinci-resolve MCP without freezing Resolve or wasting
  tokens. Use it whenever the user wants new Fusion nodes, a group, a macro or a reusable component (ทำ component ใหม่, ทำ node, สร้าง group,
  ทำมาโคร, กล่อง Note, NoteBox, panel, overlay, "เอาไปวางที่อื่นได้"), wants expressions or user
  controls added or rewired between Fusion tools (ตั้ง expression, สร้างตัวแปร, switch, Center,
  Size), wants to replace or tidy an old node set in a big comp, or when Resolve froze or hung
  after scripting Fusion ("davinci ค้าง", "not responding", "crash"). Also use it before running
  any script_plugin run_inline / comp.Execute code against a live comp.
---

# DaVinci Resolve Instructor (Fusion build workflow)

The user edits guide videos in DaVinci Resolve Studio. Their Fusion comps are large, and
"Compare Bar Graph" has about 475 tools. On 2026-10-01 editing such a comp node by node through
scripts froze Resolve twice. Unsaved work was lost and many tokens went into recovery.
This skill is the way to work from now on.

**Primary use: implementing a new component.** Follow "Delivering a component" below from start
to finish. Everything else in this skill (live edits, recovery) is secondary.

## Core rule

**Do not build or rewire a big live comp through scripts.** Write the new node set as a
**Group `.setting` file** (plain text). The user pastes it in, tests it next to the old set,
and deletes the old set only after it works.

## Before doing anything

1. Read **`fusion-setting-workflow.md`** in this folder. It has the 7-step process, the
   cycle-free expression rule, the file checks, the paste methods and the safety rules for
   the times you still have to script a live comp.
2. If the task continues an existing component, read its spec file. See the catalogue below.
3. Prefer MCP reads over screen control. Use screenshots only when no MCP read can answer,
   and only to look. Never trigger a render from a script to "see" the result.

## Non-negotiables (summary; details in the workflow doc)

- **Never pull an image or render from a script** (`tool.Output[time]`, `:Render()`). It freezes the UI.
- **No expression cycles.** If A's expression reads B, then B must not receive image data from A.
  Read image sizes (`Foreground.Width`, `Background.Height`) only in a tool whose image inputs
  come from an isolated source, such as a transparent canvas plus the plugged-in image.
- **Use a Group, not a Macro.** The user wants to be able to Ungroup (extract) it.
- **`comp.Execute(lua)` is async.** Read results back in a *separate* `run_inline` call.
  Wire nodes in Lua, never through Python proxy assignment.
- **Check `GetCurrentComp()` and name availability before editing or renaming.** The user
  changes the comp between turns, and Fusion silently appends `1` to a duplicate name.
- **Ask the user to save (Ctrl+S) before any multi-step live edit.**
- If Resolve shows "Not responding" with idle CPU, it is deadlocked. End the task, reopen on the
  **Edit** page, and inspect the comp by script before opening Fusion.

## Delivering a component

1. Write `<Name>.setting` with `NB_`-style prefixed internal names and published `InstanceInput`s.
2. Check that braces balance and every `SourceOp` exists (commands are in the workflow doc).
3. Put it on the clipboard (`Get-Content f -Raw | Set-Clipboard`) so the user can Ctrl+V it in
   Nodes. Also copy it to
   `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Macros\`; it shows up in
   Select Tool after Resolve restarts.
4. Tell the user exactly which node each input and the output connect to, using real node names from their comp.
5. Record the component in this folder as `<Name>.md`: spec, formulas, structure, wiring,
   untested assumptions. Add it to the catalogue below.
6. Swap it in: repoint any expressions elsewhere in the comp that still reference the old nodes
   (scan every tool's expressions by name), rewire the output, and confirm the old set is fully
   disconnected. **The user deletes the old nodes themselves.** Auto mode blocks deletion as
   irreversible, whether by script or by screen clicks, so hand them the exact list. The Delete
   key often fails to register because the Nodes panel does not have focus. Tell them to
   **right-click the node → Delete**, and confirm with `FindTool` that the nodes are really gone
   before you continue.
7. Rename the new internal nodes to the user's naming style (for example `NoteTitle`, `NoteTitle_Merge`).
   Rename the nodes whose new names are already free right away. Rename the ones that collide
   with old nodes after the user deletes those. Fusion updates expression references on rename
   automatically, but still check afterwards that no stale names remain.
8. Tidy the layout with `FlowView:SetPos`, which is position only and safe. Put the merges in one
   vertical spine from top to bottom, with each part entering from the left on its own row.
   Check whether other tools overlap the block, such as the image's MediaIn, and move them into place.
9. Update `<Name>.md` to match what is actually in the comp: final node names (comp ↔ file), which
   controls the user adjusts and on which node, what not to touch, and which expressions outside
   the block depend on it. Also tell the user where the main control (for example Switch) now lives.

## Component catalogue

Workspace: `E:\Youtube\Workspace\WAF\DavinciResolveComponent` (git repo). `.setting` files live in
`component\`, this skill and the specs live in `Instructor\` (the `~/.claude/skills/davinci-resolve-instructor`
junction points here). Always write new `.setting` files into `component\`, then copy them to the Fusion Macros folder.

| Component | Spec | Status |
|---|---|---|
| NoteBox: right-side note panel with image (85% width), Title, Info, and a Switch to slide it out | `NoteBox.md` (file: `component\NoteBox.setting`, uses `NB_*` names) | **in use** in Compare Bar Graph: ungrouped, renamed `Note*`, old set deleted. Controls are on `NoteArea` (Controls tab) |
| InfoBox: navy/gold caption box (skill `resolve-info-box`) — approved layout: width 0.272, 34 px right gap, body 0.0335 / title 0.036, wrap lines > 28 chars | `InfoBox.md` | **house standard** since 2026-10-02 (Pearl guide) |
| V_BarGraph: vertical bar column (grows up from a baseline, 1 image under it, value label above the bar) | `V_BarGraph.md` (file: `component\V_BarGraph.setting`, uses `Bar_*` names, renamed from `VB_*`) | written 2026-10-01, in testing |

## Related skills

- `resolve-info-box`, `resolve-pie-chart`, `resolve-bar-graph` and `resolve-section-transitions` drive the user's existing
  templates. Use those for their tasks, and use this skill's safety rules whenever they script Fusion.
