# Popup Text Box With Title: วิธีใช้

กล่องกรมท่าขอบทองกลางจอ มีกล่องหัวข้อเล็กซ้อนด้านบน และช่องให้เสียบเนื้อหาเข้าไปในกล่อง
ไฟล์: `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Macros\Popup Text Box With Title.setting`
(ชื่อ instance เมื่อวาง: `PopupTextBoxWithTitle1`) ใช้เป็นกรอบหัวเรื่องในฉากกราฟวงกลม (skill `resolve-pie-chart`)
และใช้กับเนื้อหาอธิบายกลางจอ (เช่น หัวข้อ 1–5 ของคลิป 2 ไกด์ Pearl Ult)

## โครงสร้างข้างใน
- `Main` (Group): กล่องหลัก ตัวคุมคือ `Main_CC` (Visible / MaxW / MaxH / MaxShadow / BorderWidth / Center)
- `Title` (Group): กล่องหัวข้อ ตัวคุมคือ `Title_CC` (Visible ของตัวเอง) + `TextTitle` (Text+)
- `Merge2_1` (ใน Main): เอาเนื้อหาจากช่อง Insert ใส่ในกล่อง (mask ด้วยขนาดกล่อง)
- `Merge2` (ใน Title): เอาตัวหนังสือหัวข้อใส่ในกล่องหัวข้อ

## ช่องต่อสาย
- **Insert** (MainInput1): เนื้อหาที่จะโชว์ในกล่อง เป็นภาพเต็มเฟรม 1920×1080 ส่วนที่อยู่นอกกล่องจะถูกตัดทิ้ง

## ค่าที่ปรับได้ (published)
| ค่า | ต้นทาง | ค่าเริ่มต้น | หมายเหตุ |
|---|---|---|---|
| Xaxis / Yaxis | Main | 0.5 / 0.5 | ตำแหน่งกล่อง |
| Border width | Main_CC.BorderWidth | 0.02 | |
| **Visible** (กล่องหลัก) | Main_CC.Visible | 1 | **ตัวคุมเปิด/ปิด** 0 → 1: 0–0.2 เส้นขยายแนวนอน, 0.3 สูงเต็ม, 0.65–1 เนื้อหาค่อยๆ ขึ้น |
| MaxW / MaxH | Main_CC | 0.7 / 0.6 | ขนาดตอนกางสุด |
| MaxShadow | Main_CC | 0.354 | เงา |
| Color (RGBA) | Color_1 | กรมท่า 0.071/0.129/0.271 | |
| สีขอบ | OuterStroke_1 | ทอง 0.898/0.694/0.290 | |
| **Blend เนื้อหา** (Input15) | Merge2_1.BlendClone | 1 | **ใช้เฟดเนื้อหาข้างในตอนเปลี่ยนเนื้อหา** (ดูกฎด้านล่าง) |
| BoxPadding | Title | 0.02 | |
| ขนาดกล่องหัวข้อ | Title_CC.MaxW / MaxH | 0.268 / 0.104 | |
| Visible (หัวข้อ) | Title_CC.Visible | 0 | เปิด/ปิดกล่องหัวข้อแยกจากกล่องหลัก |
| **Text Blend** (Input21) | Merge2.BlendClone | 1 | เฟดตัวหนังสือหัวข้อตอนเปลี่ยนหัวข้อ |
| StyledText / Font / Style / Color / Size (0.08) / Tracking / Line spacing / Anchor | TextTitle | | ตัวหนังสือหัวข้อ |

## วิธีใช้
1. วางใน Fusion Composition หรือ Adjustment Clip (Select Tool → "Popup Text Box With Title")
2. ใส่หัวข้อใน StyledText และต่อเนื้อหาเข้า Insert
3. **เปิด:** คีย์เฟรม Visible ของกล่องหลัก 0 → 1 แล้วตามด้วย Visible ของหัวข้อ
4. **ปิด:** คีย์เฟรม Visible กลับเป็น 0 (หัวข้อก่อน แล้วกล่องหลัก)

## กฎ: เปลี่ยนเนื้อหาในช่วงสั้นๆ ให้ใช้ Blend ไม่ใช่ Visible (ผู้ใช้กำหนด 2026-10-22)
ถ้าเนื้อหาต้องเปลี่ยนและช่วงเวลาระหว่างเนื้อหาเก่ากับใหม่สั้นมาก **อย่าปิด/เปิดกล่องด้วย Visible**
ให้ค้างกล่องไว้ แล้วเฟดเนื้อหาข้างในด้วย **Blend เนื้อหา (Merge2_1 BlendClone)** แทน:
- **ขาออก 30 เฟรม** (Blend 1 → 0) → สลับเนื้อหาตอน Blend = 0 → **ขาเข้า 30 เฟรม** (Blend 0 → 1) รวม 60 เฟรมต่อการเปลี่ยนหนึ่งครั้ง (60 fps)
- ถ้าหัวข้อเปลี่ยนด้วย ใช้ **Text Blend** ของหัวข้อแบบเดียวกันในช่วงเวลาเดียวกัน

**ข้อควรรู้ทางเทคนิค:** ปกติ Merge2_1.Blend ถูกขับด้วย expression จาก Main_CC.Visible (เนื้อหาโผล่ตอน Visible > 0.65)
การคีย์เฟรม Blend เนื้อหาจะแทนที่ expression นั้น ดังนั้นต้องคีย์ Blend เป็น 0 เองก่อนปิดกล่อง และ 0 ตอนเปิดกล่องแล้วค่อยเฟดขึ้น

## พื้นกล่องโปร่งใส แต่ขอบทอง 100% (2026-10-23)
ขอบทองของ `OuterStroke_1` คือสำเนาของพื้น (`Color_1`) ที่ถูกขยาย (ErodeDilate) วางไว้**ข้างหลัง**พื้น
ห้ามลด alpha ของ `Color_1` เพราะขอบจะจางตาม และสีทองจะทะลุพื้นขึ้นมา วิธีที่ใช้:
- เพิ่ม Merge `BoxRing` (Background = `PipeRouter1_1`, Foreground = `Shadow1_1`, Operator **Held Out**) = เหลือแต่วงขอบ + เงานอกกล่อง
- `Merge1_1.Background` ← `BoxRing` แล้วตั้ง **`Merge1_1.Blend` = ความทึบของพื้น** (0.7 = ทึบ 70%)
- กล่องหัวข้อ (`Title`) กับเนื้อหาใน Insert ไม่โดนผล ยัง 100%

## ใช้จริง: คลิป 2 ไกด์ Pearl Ult (2026-10-22)
- Adjustment Clip บน V2 (เริ่ม 1:08.35 = เฟรม 220101) คอมพ์สร้างด้วย `component\gen_popup_clip2.py` แล้ว import เข้าคลิป
- กล่องชื่อ `PTB_Clip2` (ตัว macro เดิม แก้แค่ Main_CC.Visible / Merge2_1.Blend / Merge2.Blend / TextTitle / Title_CC.MaxW 0.38 / ขนาดหัวข้อ 0.042)
  เนื้อหา `P2_*` เป็นโซ่ Text+ และกล่องสี่เหลี่ยม ต่อตรงเข้า `Merge2_1.Foreground` ทุกค่าขับด้วย expression ตามเวลา (ไม่มีคีย์เฟรม)
- เปิด 1:11.0 · สลับเนื้อหาที่ 1:17.9 / 1:35.6 / 1:56.6 / 2:18.6 / 2:35.6 (Blend 30+30) · ปิด 3:22.2
- ใน `.comp` การต่อสายเข้า/ออก Group ให้อ้าง node ข้างในโดยตรง (เช่น `Merge5` เป็นทางออกของ macro, `Merge2_1.Foreground` เป็นทางเข้า Insert)

## ใช้จริง: คลิป 4 ไกด์ Pearl Ult (2026-10-23)
- Adjustment Clip บน V2 (เริ่มที่เฟรม 266669) สร้างคอมพ์ด้วย `component\gen_clip4.py` แล้ว import เข้าคลิป
- ช่วงแรกใช้ Popup ตัวนี้ (`PTB_Clip4`, เนื้อหา `P4_S*`) จากนั้นภาพ `Black Board.png` สไลด์เข้าจากขวาแล้วเป็นพื้นหลัง
  มีเนื้อหาชอล์ก 3 หน้า (`P4_B1/B2/B3*`, ฟอนต์ TH Mali Grade6, เขียนทีละตัวด้วย Text+ End)
- แต่ละส่วนต่อเข้าผ่าน Merge ตัวเดียว (`P4_PopOver`, `P4_BoardOver`, `P4_Page1-3`) ที่ Blend = 0 นอกช่วงเวลาของมัน
- เวลาอ้างจาก SRT: เวลาใน srt = เวลาใน 4.mp4 + 841.4 วินาที (เทียบจากช่วงเงียบในเสียง)
