# InfoBox: layout settings (house standard)

The navy-and-gold caption box that slides in from the right (skill `resolve-info-box`). This file records the
**layout WAF approved on 2026-10-02** in the Pearl guide (project "Pearl", timeline `Main`, Adjustment Clip on
**V3**, 01:01:48 – 01:13:11). Use these values for every new box unless the user asks otherwise.

The comp is the newer template with a separate header: `HeadText` / `HeadRect` / `HeadStroke` for the title,
`Text1` for the body, `rect` as the master control (`rectWidth`, `rectHeight`, `rectSwitch` splines).

## Values

| What | Control | Value | Notes |
|---|---|---|---|
| Box width | `rect.Width` (all keys of `rectWidth`) | **0.272** | 85% of the old 0.32. Same width for every state. |
| Gap box → right edge of frame | via `rect.Center.X` | **≈34 px** (0.0176 of frame width) | 25% of the old 135 px gap; counted to the outside of the gold stroke. |
| `rect.Center` | static (no keys) | **X = 1 − 0.017617 − stroke.Input2 − Width/2** = 0.8424 at Width 0.272, stroke 0.004; **Y = 0.596124** | Recompute X whenever Width changes so the right gap stays 34 px. The slide in/out, FrameMask, Merge5 all derive from `rect.Center`, so nothing else moves by hand. |
| Body font | `Text1.Size` | **0.0335** | Was 0.037. |
| Title font | `HeadText.Size` | **0.036** | Was 0.040. |
| Box height | `rect.Height` (keys of `rectHeight`) | **0.2045 + 0.065 × (body lines − 2)** | 2 lines 0.2045 · 3 lines 0.2695 · 4 lines 0.3345 · 5 lines 0.3995. Each state's height is keyed over that state's hold window (keys from `start−1` to `next_start−31`). |

## Line length rule

- At Width 0.272 / Size 0.0335 a body line holds **about 28 base characters** (Thai combining vowels and tone
  marks do not count). This was measured: at Size 0.037 a 27-character line (`- SW แรงกว่า ~4,000 (~4.5%)`)
  overflowed, so 0.037 held ~25–26.
- **Longer lines are wrapped, not shrunk** (user preference): break at a space near the middle, continuation line
  indented with two spaces (`"  "`), and add 0.065 to that state's height for each added line.
- Titles stay one line; the longest used so far is 24 characters (`ทีม Sparkle / Waventurine`).

## Notes

- The body text is one StyledText expression: `time < F1 and "..." or time < F2 and "..." or "last"` (`\n` for
  new lines). Colons inside these bullet strings work in this comp, but a raw `:` once broke a NoteBox Title
  expression; if a Text+ goes red after an edit, write the colon as `\058`.
- Changing width or height keys: rewrite the key values in place with `SetKeyFrames(..., False)` copying each
  key's LH/RH handles. Never delete keys.
- Font "Quark" lacks arrow glyphs; use `»`.
