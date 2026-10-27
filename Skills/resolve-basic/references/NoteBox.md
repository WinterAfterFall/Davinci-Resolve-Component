# NoteBox (กล่อง Note)

กล่อง Note ที่เลื่อนเข้ามาจากขอบขวาของจอ ประกอบด้วยรูป, Title และ Info
ทำให้โปรเจกต์ **Compare Bar Graph** (Resolve Studio 21.0.2.4) เมื่อ 2026-10-01 ตามขั้นตอนใน `fusion-setting-workflow.md`

- **สถานะ: ใช้งานจริงแล้ว** ในคอมพ์ของ "Fusion Composition" บน Timeline 1 ถูก ungroup และเปลี่ยนชื่อเป็น `Note*` แล้ว
  ชุด Note เก่าลบออกหมดแล้ว และ render ถูกต้อง (รูปอยู่บน → Title สีเหลือง → Info)
- ไฟล์ต้นฉบับ `E:\Youtube\Workspace\WAF\DavinciResolveComponent\component\NoteBox.setting` (มีสำเนาในโฟลเดอร์ Fusion Macros) ยังเป็นเวอร์ชัน Group ที่ใช้ชื่อ `NB_*`
  ถ้าวางไฟล์นี้ใหม่จะได้ชื่อ `NB_*` ตามตารางด้านล่าง

## โจทย์
- **พื้นที่ดำ** = พื้นที่เขียน ชิดขอบขวา **แถบเหลือง** = กรอบ อยู่ด้านในขอบซ้ายของพื้นที่ดำ
- ไล่จากบนลงล่าง: **รูป** (กว้าง 85% ของพื้นที่เขียน อยู่กึ่งกลาง ชิดบน) → **Title** → **Info** เว้นระยะเท่ากัน
- **Switch**: 0 = ซ่อน (ดันออกขวาสุด โดยเลื่อนน้อยที่สุดเท่าที่พอ) และ 1 = แสดง
- เปลี่ยนรูปขนาดไหนก็ได้ ขนาดและตำแหน่งจะปรับตามเอง

## ชื่อ node (ในคอมพ์ ↔ ในไฟล์ .setting)
| ในคอมพ์ | ในไฟล์ | หน้าที่ |
|---|---|---|
| `NoteArea` | `NB_Area` | RectangleMask ของพื้นที่ดำ + **user controls ทั้งหมด** |
| `NoteFill` | `NB_Fill` | Background สีดำ (mask NoteArea) |
| `NoteShadow` | `NB_Shadow` | DropShadow ของพื้นที่ดำ |
| `NoteFrame` | `NB_Frame` | RectangleMask ของแถบเหลือง |
| `NoteFrameColor` | `NB_FrameColor` | Background สีเหลือง |
| `NoteFrame_Merge` | `NB_M1` | ดำ + เหลือง |
| `NoteCanvas` | `NB_Canvas` | แผ่นใส ใช้เป็นฐานวางรูป (แยกไว้เพื่อตัด cycle) |
| `NoteImage` | `NB_ImgPlace` | Merge ที่วางรูป + คำนวณ `ImgBottom` **ช่อง Foreground = รูป** |
| `NoteImage_Merge` | `NB_M2` | + รูป |
| `NoteTitle` | `NB_Title` | TextPlus ของ Title (mask NoteArea) |
| `NoteTitle_Merge` | `NB_M3` | + Title |
| `NoteInfo` | `NB_Info` | TextPlus ของ Info (mask NoteArea) |
| `NoteInfo_Merge` | `NB_M4` | + Info |
| `Note_Merge` | `NB_Out` | วางกล่องบนภาพฉาก + เลื่อนตาม Switch |

## ผัง (ในคอมพ์ merge เรียงเป็นแกนแนวตั้ง ไหลจากบนลงล่าง)
```
NoteArea   NoteFill   NoteShadow ─┐
NoteFrame  NoteFrameColor ────────┴► NoteFrame_Merge
           NoteCanvas  NoteImage ──► NoteImage_Merge
           MediaIn3 ─┘ (รูป)
                       NoteTitle ──► NoteTitle_Merge
                       NoteInfo  ──► NoteInfo_Merge
                        Pic_Merge ─► Note_Merge ──► MediaOut1_1
```

## ค่าที่ปรับได้ (ต้องจำ)
**`NoteArea` → แท็บ Controls**

| ค่า | ค่าเริ่ม | ใช้ทำอะไร |
|---|---|---|
| **Switch** | 1 | 0 = ซ่อน, 1 = แสดง ใส่ keyframe ที่นี่ที่เดียว |
| **Width** | 0.348 | ความกว้างพื้นที่ดำ (อยู่ในแท็บ Controls ปกติของ mask) |
| Image Width | 0.85 | ความกว้างรูปเทียบกับพื้นที่เขียน |
| Gap | 0.03 | ระยะห่างระหว่าง รูป, Title และ Info |
| Title Line Height | 1.2 | × ขนาด Title ใช้คำนวณว่า Info ต้องอยู่ต่ำจาก Title แค่ไหน ต้องปรับตามถ้าเปลี่ยนขนาด Title |

**`NoteTitle` / `NoteInfo` → แท็บ Text:** ข้อความ ขนาด (Title 0.06, Info 0.035) ฟอนต์ และสี
**`NoteImage` ช่อง Foreground:** รูป ในคอมพ์นี้ต่อจาก `MediaIn3`

**ห้ามแตะ** (มี expression คำนวณให้อัตโนมัติ): Center และ Size ของ `NoteImage` และ Image Bottom (auto),
Center ของ `NoteTitle`, `NoteInfo`, `Note_Merge`, `NoteArea` และ `NoteFrame`

## สูตร
| อะไร | สูตร |
|---|---|
| ความกว้างพื้นที่เขียน | `areaW = NoteArea.Width - NoteFrame.Width` |
| x กลางพื้นที่เขียน | `NoteArea.Center.X + NoteFrame.Width/2` |
| Switch (`Note_Merge.Center`) | `Point(0.5+NoteArea.Width*(1-NoteArea.Switch), 0.5)` |
| ขนาดรูป (`NoteImage.Size`) | `NoteArea.ImgWidth*(NoteArea.Width-NoteFrame.Width)*Background.Width/Foreground.Width` |
| ตำแหน่งรูป (`NoteImage.Center`) | x กลางพื้นที่เขียน, y = `1 - (1-ImgWidth)/2*areaW*Background.Width/Background.Height - Foreground.Height*Size/Background.Height/2` |
| ขอบล่างรูป (`NoteImage.ImgBottom`) | `Center.Y-Foreground.Height*Size/Background.Height/2` |
| `NoteTitle.Center` (ยึดขอบบน) | `Point(x, NoteImage.ImgBottom-NoteArea.Gap)` |
| `NoteInfo.Center` (ยึดขอบบน) | `Point(x, NoteImage.ImgBottom-NoteArea.Gap-NoteTitle.Size*NoteArea.TitleLineH-NoteArea.Gap)` |

**Title lock (Pearl comps, 2026-10-01):** Title and Info don't move when Image Width changes. They are laid out
from the reference width `NoteImage.RefWidth` (0.85) instead of `ImgWidth`:
`NoteImage.RefBottom` = the image's bottom edge if the width were RefWidth, and X =
`NoteArea.Center.X-NoteArea.Width/2+NoteFrame.Width+(1-NoteImage.RefWidth)/2*(NoteArea.Width-NoteFrame.Width)` (left-aligned).
Title Y = `NoteImage.RefBottom-NoteArea.Gap`. Info Y also uses `RefBottom`. To move the text block, change `RefWidth`.

`VerticalTopCenterBottom = -1` แปลว่ายึดขอบบนจริง **ยืนยันจากภาพที่ render แล้ว**

## ส่วนอื่นในคอมพ์นี้ที่ใช้ Switch ของ NoteArea
node เหล่านี้เลื่อนหลบไปทางซ้ายตอนกล่อง Note เข้ามา expression อยู่ที่ตัว node เหล่านี้เอง **ไม่ได้อยู่ในบล็อก Note**:

| Node | Expression |
|---|---|
| `Title_Merge.Center` | `Point(0.5-NoteArea.Width*(NoteArea.Switch)*0.8, 0.5)` |
| `Pic_Merge.Center` | `Point(0.5-NoteArea.Width*(NoteArea.Switch*0.8), 0.5)` |
| `Merge5.Center` | `Point(0.5-NoteArea.Width*(NoteArea.Switch*0.7), 0.5)` |
| `GC.RightMargin` (group `B1`; B2–B4 follow through `B1.Input2`) | `0.08+NoteArea.Width*NoteArea.Switch*0.2` |

## เอาไปใช้คอมพ์อื่น
1. copy ทั้งบล็อก ตั้งแต่ `NoteArea` ถึง `Note_Merge` รวม `MediaIn3` ด้วย (หรือวาง `NoteBox.setting` ซึ่งจะได้ชื่อ `NB_*`)
2. ต่อ 3 จุด: `Note_Merge` ช่อง Background ← ภาพฉาก · `NoteImage` ช่อง Foreground ← รูป · output ของ `Note_Merge` → ปลายทาง

**ช่องต่อสำเร็จรูป (Compare Bar Graph ของ Pearl, 2026-10-23):** ใส่ PipeRouter 3 ตัวเป็นจุดเข้า-ออกของบล็อก
copy บล็อกพร้อม 3 ตัวนี้ แล้วต่อสายที่ตัวมันได้เลย (PipeRouter ส่งภาพผ่านเฉยๆ ไม่เปลี่ยนอะไร)
| Node | ต่อกับอะไร |
|---|---|
| `NoteIn_Scene` | ภาพฉากเข้า » `Note_Merge.Background` (ในคอมพ์นี้มาจาก `Pic_Merge`) |
| `NoteIn_Image` | รูปเข้า » `NoteImage.Foreground` (ในคอมพ์นี้มาจาก `NoteImgSwitch2`; ชุด `NoteImg1-3` + `NoteImgSwitch1-2` ไม่ต้อง copy ถ้าใช้รูปเดียว) |
| `NoteOut` | output ของ `Note_Merge` » ปลายทาง (ในคอมพ์นี้ `Merge3.Foreground`) |
3. ถ้าต้องการให้ส่วนอื่นเลื่อนหลบ ให้ใส่ expression แบบในตารางข้างบนที่ node นั้น

## ข้อจำกัด
1. **ต้องเสียบรูปไว้เสมอ** ถ้าไม่มีรูป ตำแหน่งของ Title และ Info จะคำนวณไม่ได้
2. Info ไม่ตัดบรรทัดให้เอง ต้องกด Enter เอง ส่วนที่เกินพื้นที่ดำจะถูก mask ตัดทิ้ง
3. **ใช้ได้ชุดเดียวต่อคอมพ์** เพราะชื่อ node ถูกอ้างตรงๆ ใน expression ถ้าวางซ้ำ ชุดที่สองจะกลายเป็น `NoteArea1` แต่ expression ข้างในยังอ้างตัวแรก
5. **ห้ามลบแอนิเมชันของ `NoteArea.Switch` ทิ้งตรงๆ** (เจอ 2026-10-23) ช่อง Switch จะค้างจนสูตรที่อ่าน `NoteArea.Switch`
   (`Title_Merge`, `Merge5`, `Pic_Merge`, `Note_Merge` และ `GC_3.RightMargin` ในกรุ๊ป `Bnew` ที่บาร์อื่นตามผ่าน `Bnew.Input2`)
   คืนค่าไม่ได้ Console ขึ้น "cannot get Parameter for …" แล้วพังต่อเป็นลูกโซ่ถึง MediaOut1
   วิธีแก้: ใส่ keyframe ให้ Switch ใหม่ แล้วให้ Fusion อ่านสูตรใหม่ทุกตัว ถ้ากด Enter สูตรเดิมแล้วยังไม่หาย
   ให้ใส่สูตรอื่นชั่วคราว (เช่นตัด `*NoteArea.Switch` ออก) แล้วค่อยใส่สูตรเดิมกลับ ถ้าไม่ต้องการแอนิเมชันให้แก้ค่าที่ keyframe แทน
4. Title ต้องเป็นบรรทัดเดียว ถ้า Title มี 2 บรรทัด Info จะทับบรรทัดที่สอง แก้ได้ด้วยการเพิ่ม Title Line Height

## บันทึกการนำไปแทนของเก่า (2026-10-01)
- ย้าย expression 5 จุดข้างบนจาก `Note.Width` / `Note_Merge.Switch` ไปอ้าง `NoteArea` ก่อน แล้วค่อยลบของเก่า
- การลบ node ต้องให้ผู้ใช้ทำเอง (auto mode บล็อกไม่ให้สคริปต์ลบ) ผู้ใช้กด Delete ไปแล้วไม่ติดหลายครั้ง
  **คลิกขวาที่ node → Delete** ได้ผลแน่นอน และต้องเช็คด้วย `FindTool` ทุกครั้งก่อนเปลี่ยนชื่อ
- เปลี่ยนชื่อ node ที่ชื่อว่างแล้วก่อน ส่วนตัวที่ชื่อชน (`NoteTitle`, `NoteInfo`, `NoteImage`, `Note_Merge`) เปลี่ยนหลังลบของเก่าแล้ว
  Fusion แก้ชื่อใน expression ตามให้เองทุกครั้ง

## Multi-image variant (Pearl Main comps, seen 2026-10-01)
Some comps switch the Note content by time instead of one fixed text:
- `NoteArea.Cut1/Cut2/Cut3` (comp frames). `NoteImgSwitch1–3` (Dissolve, `Mix = time >= NoteArea.CutN and 1 or 0`)
  chain 4 images into `NoteImage.Foreground`.
- `NoteTitle` / `NoteInfo` StyledText = `time < NoteArea.Cut1 and "…" or time < NoteArea.Cut2 and "…" or …` (Lua `\n` for new lines).
- Two-line titles: set `NoteArea.TitleLineH` = 2.4 (2 × 1.2) so Info sits under both lines.
- Pearl Main "Eidolon" Adjustment Clip (timeline 60fps, item start 289050): comp frame = 60 × video-seconds − 73121.
  Cuts 1369 / 2677 / 3415 = "Eidolon 2 / 4 / 6" in the SRT; Switch keys 195→225 slide in. Images come from Loaders `E1/E2/E4/E6_Img`
  (shared with the V_BarGraph bars). The previous team-section values are backed up in
  `E:\Youtube\Workspace\WAF\DavinciResolveComponent\backup_PearlMain_Eidolon_NoteBox_team_values.json`.
- Setting `.Clip` on an EXISTING Loader from a script hung the run_inline call (timeout, nothing applied). Rewire with
  `ConnectInput` to a fresh Loader instead.
- Titles are now `Eidolon N :` + name over 3 lines (`TitleLineH` 3.6). **A raw `:` in an expression string breaks it** (Title went nil and red); the colon is written `\058`.
- `6.png` is 1000×1000 vs 2048 for the others, so it goes through `E6_Resize` (2048²) before `NoteImgSwitch3`. The images are MediaIn4–7 (1/2/4/6), added by the user.
