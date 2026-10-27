---
name: resolve-basic
description: WAF's house rules for ANY DaVinci Resolve / Fusion work in a guide video - load this first whenever the task touches a Resolve project, a Fusion comp, an Adjustment Clip or Fusion clip, or designs on-screen text/graphics. Covers how to lay out Fusion nodes (components above one straight main merge line, links only left→right / top→bottom), how to mark cut points on an Adjustment/Fusion layer (one layer at a time, say which pieces to delete), disabling instead of deleting unused nodes, the pre-export render-crash check (Trim in/out, Global in/out, ranges, missing files, broken links), and how to design text slides as infographics with good spacing and nothing touching an edge. Also the safe way to BUILD A NEW FUSION COMPONENT (a reusable node set or panel, e.g. NoteBox) as a Group .setting file the user pastes, tests and swaps in, the safety rules for scripting a live comp through the davinci-resolve MCP without freezing Resolve, and the specs of existing components (NoteBox, InfoBox, ClipCallback, PopupTextBoxWithTitle, V_BarGraph). Triggers include "Fusion", "node", "จัด node", "วาง node", "adjustment layer", "adjustment clip", "ตัด adjustment", "mark จุดตัด", "disable node", "export", "render", "ก่อน export", "ตรวจงาน", "render crash", "ออกแบบสไลด์", "นำเสนอ", "กระดาน", "infographic", "spacing", "ชิดขอบ", "รก", "ว่างเกิน", "ทำ component ใหม่", "ทำ node", "สร้าง group", "ทำมาโคร", "กล่อง Note", "NoteBox", "panel", "overlay", "เอาไปวางที่อื่นได้", "ตั้ง expression", "สร้างตัวแปร", "switch", "davinci ค้าง", "not responding", "crash"; also load it before running any run_inline / comp.Execute code against a live comp. Use together with a specific skill (resolve-info-box, resolve-bar-graph …) when one fits. Scripts: comp_layout.py, layout_comp.py, copy_pos.py, find_unused.py, cutoff.py, check_render.py.
---

# Resolve basics (WAF)

Rules the user set while finishing the Pearl2 guide (2026-10-24). They apply to every Resolve / Fusion
job unless the user says otherwise for that job. Scripts are in `scripts/`; run Python with `-I`.
§7 (safe scripting + building new components) was merged in from the old `davinci-resolve-instructor`
skill on 2026-10-26; its docs are in `references/`.

## 1. Node layout

Think of a comp as separate **components** first (a title, a bar graph, a Note sidebar; on a board:
the board itself, then one component per page). Then:

```
      [component A]              [component B]                 [C]
                Canvas                       Canvas              …
                  ↓                            ↓
   Mask → Src → Merge           Mask → Src → Merge
          Src → Merge                  Src → Merge
                  ↓            Mask → Src → Merge
                  ↓                            ↓
MediaIn ───────► Merge ──────────────────────► Merge ─────────► Merge → MediaOut
```

1. **Main merge line**: one straight horizontal line along the bottom, left → right, ending at MediaOut.
   Each merge on it takes in one component.
2. **Each component sits above the main-line merge that collects it**, in its own clearly separate zone.
   The gap between main-line merges stretches to the width of the component above it. The component's
   last merge is in the same column as its main-line merge, so the link drops straight down.
3. **Inside a component: mix top → bottom, feed layers left → right.** The component's merges stack in
   one column going down (Canvas on top); each layer comes in from the left on its merge's row:
   mask → source (Text / Background …) → merge. (The opposite, merges in a row with masks above, was
   tried first and the user found it harder to read.)
4. **Every link runs left → right or top → bottom.** None right → left or bottom → up.
   Check: `python -I scripts/layout_comp.py --check <comp>` must report 0 backward links.
5. **Don't re-lay out a comp the user arranged by hand without asking.** The Pearl2 V2 bar graph was
   auto-laid out, the user preferred their own, it was put back.
- **Lay out with `scripts/comp_layout.py`** for every comp you create or change (generated or not):
  `python -I scripts/comp_layout.py [--cells] <comp> <pos.json>` places nodes by this section's rules
  (main line, components above their main-line merge, merges stacked, mask → source → merge from
  the left). `layout_comp.py` (plain layered layout, doesn't know components) is only the checker.
- Generated comps: build the layout into the generator (example: `gen_clip3_board.py`, "node layout"),
  or run `comp_layout.py` on its output before handing it over. A layout rule added later applies to
  comps already in the timeline too: go back and fix them.
- **Moving nodes in a live comp via MCP** (`fusion_comp set_position`):
  - x / y are FlowView **grid cells** (1 = one node: 110 px wide, 33 px tall), not the `Pos` pixels
    of the .comp file. Use `comp_layout.py --cells`. Pixels spread the nodes 110× / 33× apart.
  - It fails with "FlowView unavailable" until that comp has been opened on the Fusion page in this
    Resolve session: ask the user to open each clip once, then apply.
  - Read back: export the comp, run `layout_comp.py --check` (0 backward links) and look at the
    spacing (neighbouring nodes one cell apart), before telling the user it's done.
- Change positions only: export the comp, edit `Pos`, import it back (`scripts/copy_pos.py <layout comp>
  <target> <out>` copies positions by node name). On a **cut** Adjustment clip do it per piece; never
  import a fresh whole comp into a cut piece (each piece carries its own time range).
- A Group's own position is the multi-line `ViewInfo = GroupInfo {` at 3 tabs, not the `Pos` of a
  node inside it. Diff the non-`Pos` lines before importing: they must not change.

## 2. Cutting an Adjustment / Fusion layer

Once the work on a layer is approved, cut the clip so each piece renders only what it needs.
1. **Work out the segments** from the comp's timing: when each component is visible, when it is hidden
   under a full-screen opaque layer above, when nothing shows at all.
2. **Add timeline markers** at the cut points (`timeline_markers add`, frame = timeline-relative frame;
   check with `get_all`). Name them `<Track> cut N` and put in the note what is on each side and
   whether each side is **kept or deleted**. One colour for "edge of a piece to delete", another for
   "split, keep both sides".
3. **Tell the user in a table**: each piece, its timecodes, what is in it, keep / delete.
4. **One layer at a time.** Mark one track, let the user cut it, then the next. Never mark two layers
   at once. The user does the cutting and deleting.
5. After the cut, **disable** (PassThrough) in each piece the nodes that piece doesn't use (§3).
   Keep 1 frame of margin at the edge of a "covered by the layer above" stretch.

## 3. Unused nodes: disable, don't delete

- Nodes no longer needed are **disabled** (`fusion_comp set_attrs TOOLB_PassThrough true`, or
  `PassThrough = true,` in the exported comp). The user deletes them later. Never delete them yourself.
- Find candidates: `python -I scripts/find_unused.py <comp>` (not reached from MediaOut1 by links or
  expressions; parses ResolveFX `ofx.…` tools and groups).
- Before disabling, check nothing still **renders through** it: a disabled Merge passes its Background,
  so disabling a merge in the main chain cuts off its foreground only (useful to switch a whole
  component off in one piece). Controls of a disabled tool stay readable by expressions.
- Read back after: export the comp and take a still that shows the remaining parts still render.

## 4. Before export: check for render-crash risks

For every piece on the layers you touched, export the comp and run
`python -I scripts/check_render.py <comp> [...]` (exit 1 on any ERROR). It checks:
- comp RenderRange inside GlobalRange and not reversed
- MediaIn **GlobalIn / GlobalOut** matching the comp range (typical drift after cutting)
- Loaders: file exists, **TrimIn ≤ TrimOut**, clip GlobalStart ≤ GlobalEnd, clip range covers the comp
  (or Loop / HoldLastFrame / Extend fills it)
- links and expressions naming tools that don't exist; images taken from disabled tools
Then also: no expression errors in the Console, macros (`SxSFilename`) still installed, and a still at
each piece's first and last frame.

**Rules check (required, every piece of every Adjustment / Fusion layer in the export range, not only
the ones you touched today)**:
- (a) layout: `python -I scripts/layout_comp.py --check <comp>` reports 0 backward links (a link
  through a Group that loops back into it can't be fixed by moving nodes: name it in the report).
- (b) cut pieces compute only what they show: `python -I scripts/cutoff.py --reached <comp>`; the
  reached nodes may belong only to components visible in that piece's time range. Any other
  component still reached means §2 step 5 was skipped: switch it off (§3) before rendering.
- (c) nothing is left still computing a page or component from before a cut (compare pieces of the
  same layer: identical comps on every piece usually mean nothing was disabled).
Report what was found in a table (piece, timecodes, a/b/c), including warnings you left on purpose,
and **tell the user before starting the render** if anything fails.

## 5. Designing text content (boards, popups, slides)

When the user lets you design the presentation and the content is text, design it like an
**infographic slide**, chosen to fit the content. Don't just stack points 1–5 top to bottom or put
each point in a plain box, unless the user asks for that.
- **Steps / process** → arrow flow or timeline.
- **Comparison** → side by side (two cards, two columns, before → after).
- **Cause and effect** → show the link (cause → effect chain, arrows between cards).
- **Numbers** → a chart or a proportion (bars, stacked bar, gauge, dots counting, big number + label).
- Each page has **one clear main point**, an obvious place to start reading and an easy reading order.
- Short, tight text; comfortable empty space. The layout explains the content, it isn't decoration.
- Make it move like motion graphics: elements build in step with the narration (slide up / pop / grow),
  not all at once.

## 6. Spacing and edges

- Always balance the space: nothing too empty, nothing too crowded.
  - Too crowded → enlarge the box or make the text smaller; don't let things crowd an edge.
  - Too empty → bring the content closer together / toward the space, enlarge the text, or shrink the box.
- **No text or graphic touches an edge** (frame, card border, screen edge). Leave a visible margin;
  check long lines (Thai lines run wide), dots/circles at the ends of rows, and the last line of a
  text box.
- Circles are drawn as circles: an EllipseMask's Width and Height are both in frame-width units, so
  Height = Width for a circle.
- Verify with stills (see memory `resolve-still-verify`: set the timecode, wait, then
  `export_frame_as_still`; zoom/crop the still to check edges). Don't move the playhead while the user
  is working in Resolve; put back track enable states and the page you switched from.

## 7. Scripting Fusion safely and building new components

The user's Fusion comps are large ("Compare Bar Graph" has about 475 tools). On 2026-10-01 editing such
a comp node by node through scripts froze Resolve twice; unsaved work was lost and many tokens went into
recovery. **Main use of this section: implementing a new component.** Follow "Delivering a component"
from start to finish.

**Core rule: do not build or rewire a big live comp through scripts.** Write the new node set as a
**Group `.setting` file** (plain text). The user pastes it in, tests it next to the old set, and deletes
the old set only after it works. (Small per-clip comps such as MediaIn → keyer → MediaOut are fine to
edit directly.)

Before doing anything:
1. Read **`references/fusion-setting-workflow.md`**: the 7-step process, the cycle-free expression rule,
   the file checks, the paste methods and the safety rules for when you still have to script a live comp.
2. If the task continues an existing component, read its spec in `references/` (catalogue below).
3. Prefer MCP reads over screen control. Use screenshots only when no MCP read can answer, and only to
   look. Never trigger a render from a script to "see" the result.

### Non-negotiables

- **Never pull an image or render from a script** (`tool.Output[time]`, `:Render()`). It freezes the UI.
- **No expression cycles.** If A's expression reads B, then B must not receive image data from A.
  Read image sizes (`Foreground.Width`, `Background.Height`) only in a tool whose image inputs come from
  an isolated source, such as a transparent canvas plus the plugged-in image.
- **Use a Group, not a Macro.** The user wants to be able to Ungroup (extract) it.
- **`comp.Execute(lua)` is async.** Read results back in a *separate* call. Wire nodes in Lua, never
  through Python proxy assignment.
- **Check `GetCurrentComp()` and name availability before editing or renaming.** The user changes the
  comp between turns, and Fusion silently appends `1` to a duplicate name.
- **Ask the user to save (Ctrl+S) before any multi-step live edit.**
- If Resolve shows "Not responding" with idle CPU, it is deadlocked. End the task, reopen on the
  **Edit** page, and inspect the comp by script before opening Fusion.

### Delivering a component

1. Write `<Name>.setting` with `NB_`-style prefixed internal names and published `InstanceInput`s.
2. Check that braces balance and every `SourceOp` exists (commands in the workflow doc).
3. Put it on the clipboard (`Get-Content f -Raw | Set-Clipboard`) so the user can Ctrl+V it in Nodes.
   Also copy it to `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Macros\`; it shows up
   in Select Tool after Resolve restarts.
4. Tell the user exactly which node each input and the output connect to, using real node names from
   their comp.
5. Record the component as `references/<Name>.md`: spec, formulas, structure, wiring, untested
   assumptions. Add it to the catalogue below.
6. Swap it in: repoint any expressions elsewhere in the comp that still reference the old nodes (scan
   every tool's expressions by name), rewire the output, and confirm the old set is fully disconnected.
   **The user deletes the old nodes themselves** (auto mode blocks deletion as irreversible); hand them
   the exact list. The Delete key often fails because the Nodes panel lacks focus: tell them to
   **right-click the node → Delete**, and confirm with `FindTool` that the nodes are gone before you go on.
7. Rename the new internal nodes to the user's naming style (e.g. `NoteTitle`, `NoteTitle_Merge`).
   Rename the ones whose names are free right away, the ones that collide with old nodes after the user
   deletes those. Fusion updates expression references on rename, but check that no stale names remain.
8. Tidy the layout by §1 (`FlowView:SetPos` is position only and safe; check with
   `scripts/layout_comp.py --check`). Check whether other tools overlap the block, such as the image's
   MediaIn, and move them into place.
9. Update `references/<Name>.md` to match the comp: final node names, which controls the user adjusts and
   on which node, what not to touch, which expressions outside the block depend on it. Tell the user
   where the main control (e.g. Switch) now lives.

### Component catalogue

`.setting` files live in the git repo `E:\Youtube\Workspace\WAF\DavinciResolveComponent\component\`.
Always write new `.setting` files there, then copy them to the Fusion Macros folder. Specs are in
`references/` of this skill. (The repo's `Instructor\` folder holds the pre-merge copy of these docs.)

| Component | Spec | Status |
|---|---|---|
| NoteBox: right-side note panel with image (85% width), Title, Info, and a Switch to slide it out | `references/NoteBox.md` (file: `component\NoteBox.setting`, `NB_*` names) | **in use** in Compare Bar Graph: ungrouped, renamed `Note*`, old set deleted. Controls are on `NoteArea` (Controls tab) |
| InfoBox: navy/gold caption box (skill `resolve-info-box`) — approved layout: width 0.272, 34 px right gap, body 0.0335 / title 0.036, wrap lines > 28 chars | `references/InfoBox.md` | **house standard** since 2026-10-02 (Pearl guide) |
| ClipCallback: old-clip callback — footage blur, cover + gold line + title reveal, slide left, navy panel with 5 line-by-line wipe-ons, timed by expressions from `CC_Ctrl.T0` | `references/ClipCallback.md` (file: `component\ClipCallback.setting`, `CC_*` names, regenerate with `component\gen_clipcallback.py`) | written 2026-10-22, untested |
| Popup Text Box With Title: centred navy/gold box + title box, content via Insert. **Rule: short content swaps fade the inner content with its Blend (Merge2_1 BlendClone) 30 f out + 30 f in, not Visible** | `references/PopupTextBoxWithTitle.md` (macro in Fusion Macros folder) | in use (pie chart header); guide written 2026-10-22 |
| V_BarGraph: vertical bar column (grows up from a baseline, 1 image under it, value label above the bar) | `references/V_BarGraph.md` (file: `component\V_BarGraph.setting`, `Bar_*` names, renamed from `VB_*`) | written 2026-10-01, in testing |

`resolve-info-box`, `resolve-pie-chart`, `resolve-bar-graph`, `resolve-hsr-compare-graph` and
`resolve-section-transitions` drive the user's existing templates. Use those for their tasks, and the
rules of this section whenever they script Fusion.
