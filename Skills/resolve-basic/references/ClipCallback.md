# ClipCallback: พูดถึงคลิปเก่า (ปก + ชื่อ → เลื่อนซ้าย → ข้อความ write on ทีละบรรทัด)

ไฟล์: `component\ClipCallback.setting` (Group, ชื่อภายในขึ้นต้นด้วย `CC_`) สร้างจาก
`gen_clipcallback.py` (2026-10-22) ใช้ครั้งแรกในคลิปที่อ้างถึง "Guide Pearl"
**สถานะ: ยังไม่ได้ทดสอบใน Resolve**

## ภาพที่ได้ (สไตล์ C + เบลอฟุตเทจ)
1. T0−6 → T0+24: ฟุตเทจเบลอ (BlurMax) สีซีดลง (SatMin) contrast ลด (ConMin) ฟุตเทจยังเล่นต่อตามปกติ
2. T0+6 → +27: ปกเปิดด้วย mask แนวตั้งที่ขยายจากกลางออกไปสองข้าง · +21 → +36: เส้นทองลากจากกลาง · +30 → +45: ชื่อลอยขึ้นและค่อยๆ ชัด
3. T0+MoveAt → +36 เฟรม: ปก + เส้น + ชื่อเลื่อนไป MoveX และย่อเหลือ MoveScale (ease in-out) พร้อมกับแผงกรมท่า (ขอบทองซ้าย) เลื่อนเข้ามาจากขวา
4. T0+L{i}At → +LineDur: บรรทัด i ขึ้นแบบ wipe ซ้าย→ขวา ขอบนุ่ม (ทีละบรรทัด ไม่ใช่ทีละตัวอักษร เพราะสระ/วรรณยุกต์ไทยจะลอยแยก)
5. T0+OutAt → +24: overlay ทั้งหมดจางออก · +12 → +42: ฟุตเทจคืนความคมชัดและสี

ค่าเริ่มต้น (60 fps): T0 = 840 (วินาทีที่ 14 ถ้าเฟรม 0 ของคอมพ์ตรงกับต้นไทม์ไลน์), MoveAt 144 (เลื่อนเสร็จที่ +180 = วินาทีที่ 17),
L1..L5At 180/270/360/450/540, LineDur 30, OutAt 900

**เลขเฟรมของคอมพ์ไม่ใช่เฟรมไทม์ไลน์เสมอไป:** คอมพ์ของคลิปนับเป็นเฟรมของไฟล์ต้นฉบับ เช่น trailer 30 fps บนไทม์ไลน์ 60 fps
คอมพ์นับ 0–2023 (1 เฟรมคอมพ์ = 2 เฟรมไทม์ไลน์) ให้อ่านช่วงเฟรมด้วย `fusion_comp get_frame_range` ก่อนเสมอ
ไฟล์มีช่อง `FPS` (ค่าเริ่มต้น 60) ที่ปรับระยะเวลาภายในตาม แต่ค่าเฟรมที่ผู้ใช้ตั้ง (T0, MoveAt, L*At, LineDur, OutAt) ต้องคิดเป็นเฟรมของคอมพ์เอง

ใช้จริงครั้งแรก (Timeline 1, คลิป trailer บน V1, คอมพ์ 30 fps, ตั้งเมื่อ 2026-10-22): T0 420 (วินาทีที่ 14), MoveAt 72,
L1–L5 90/135/180/225/270, LineDur 15, OutAt 450 ตัวที่วางในคอมพ์นั้นเป็นเวอร์ชันก่อนมีช่อง FPS
จึงแก้ expression ของ pBlurIn/pBlurOut/pCover/pLine/pTitle/pMove/pOut บน CC_Ctrl เป็นค่าครึ่งหนึ่งโดยตรง

## ต่อสาย
- `Footage` (MainInput1) ← MediaIn ของฟุตเทจ (ถ้าไม่ต่อ = overlay บนพื้นใส ใช้ใน Fusion Composition/Adjustment ได้แต่ไม่มีเบลอ)
- `Cover image` (MainInput2) ← MediaIn ของภาพปก (เช่น pearl.jpg 1280×720)
- Output → MediaOut1

## Controls (บน Group, ต้นทางอยู่ที่ `CC_Ctrl`)
- Timing: T0, MoveAt, L1At–L5At, LineDur, OutAt (เฟรมของคอมพ์ / เฟรมหลัง T0)
- Look: BlurMax, SatMin, ConMin, PanelAlpha / BarAlpha (ความทึบของกล่องกรมท่ากับเส้นทองด้านซ้าย ค่าเริ่มต้น 0 ทั้งคู่ = ไม่มี ตามที่ผู้ใช้ขอ 2026-10-22
  เหลือแค่ข้อความลอยบนฟุตเทจที่เบลอ)
- Layout: CoverW, CoverY, MoveX, MoveScale, PanelX/Y/W/H, LineStep
- ข้อความ: Title, Line 1–5 และขนาดของแต่ละตัว (Quark Bold) Title 0.09 / Line 0.072 (ขยาย 2 เท่าเมื่อ 2026-10-22)
  บรรทัดละประมาณ 20 ตัวอักษรฐานที่ขนาด 0.072 · แผงขยายเป็น W 0.46 / H 0.86, LineStep 0.15
- สไตล์ตัวอักษร (ทุก Text+, ใน Shading) ตามภาพอ้างอิง "Robin Summer": ตัวขาว + เงาแข็งชิดตัวเอียงขวาล่าง 27° ไม่มีเส้นขอบ
  element 2 Outline ปิดไว้ (Thickness 0.02) · element 3 Depth เงาแข็งกรมท่าเข้ม #06142A ระยะ 0.035 ·
  element 4 Soft Shadow ดำ 35% ระยะ 0.06 Softness 8 อยู่หลังสุด (PriorityBack 5) มุมกับระยะตั้งใน `STROKE_ANGLE` / `off()` ของ generator
  ค่าตั้งต้นของ Text+ ใน Resolve 21: element 2 = Red Outline (Thickness 0.02, priority 7), 3 = Black Shadow
  (Offset 0.05,−0.05, Softness 5, priority 6), 4 = Blue Border (ElementShape 2)
- หน้า Calc ของ `CC_Ctrl` (pX/eX) เป็น expression คำนวณ progress อย่าแก้

## Expression / ความปลอดภัย
- ทุกแอนิเมชันเป็น expression ของ `time` บน `CC_Ctrl` ไม่มีคีย์เฟรม
- `CC_CoverPlace.HalfH` อ่าน `Foreground.Height` ได้เพราะ Background ของมันคือ `CC_Ctrl` (แผ่นใสแยก) และ Foreground คือปกที่เสียบเข้ามาตรงๆ
  ตัวที่อ่าน HalfH (`CC_GoldLineMask`, `CC_Title`) ไม่ได้ส่งภาพกลับเข้า `CC_CoverPlace` จึงไม่มีวง
- ห้าม `GetInput` ของ `CC_CoverPlace.HalfH` / `Size` จากสคริปต์ (การอ่านค่านี้จะสั่งเรนเดอร์) ให้ใช้ `GetExpression`

## สมมติฐานที่ยังไม่ได้ทดสอบ
- ความสูงของ RectangleMask คิดเป็นหน่วยของความกว้างภาพ (จึงคูณ 0.5625 กับค่าที่เป็นหน่วยความสูง)
- `HorizontalLeftCenterRight = -1` + `HorizontalJustificationNew = 3` ทำให้ Text+ ชิดซ้ายที่ Center (ค่าเดียวกับ Text1 ของ Info Box)
- ชื่อ input `Saturation` / `Contrast` ของ BrightnessContrast และ `XBlurSize` ของ Blur

## เปลี่ยนแปลง 2026-10-22 (รอบหลัง)
- เอาแผงกรมท่า เส้นทอง และ Text+ 5 ตัวออกทั้งหมด เหลือ **Text+ ตัวเดียว `CC_Text`** (ช่อง "Text" บน Group)
  ผู้ใช้จะบอกเองว่าเว้นบรรทัดตรงไหน แต่ละบรรทัด (ขึ้นบรรทัดใหม่ด้วย Enter / `
`) ขึ้นตามเวลา L1At–L6At
- การ write on ทีละบรรทัดทำด้วย RectangleMask 6 ตัว `CC_Row1..6` ต่อกันเป็นโซ่ทาง EffectMask (รวมกันแบบ Merge)
  แถว i อยู่ระหว่าง `TextTop-(i-1)*LineStep` ถึง `TextTop-i*LineStep` แถวแรกเผื่อขึ้นไป 0.05 ให้สระบน
  **LineStep ต้องเท่ากับระยะบรรทัดจริงของ Text+** (เดา 0.15 ที่ Size 0.072) ถ้าไม่ตรง ส่วนบนหรือล่างของบรรทัดจะโผล่ก่อนหรือหลังเวลา
- วัดได้จากภาพทดสอบแผงรอบแรก: ความสูงของ RectangleMask เป็นหน่วยความสูงภาพ (ไม่ต้องคูณ 0.5625)
  และ Background ที่ตั้ง TopLeftAlpha = 0 แต่ RGB ไม่เป็น 0 ยังบวกสีออกมา (ไม่ premultiply) จึงต้องลบ tool ทิ้งแทน

## เปลี่ยนแปลง 2026-10-22 (รอบล่าสุด, ใช้งานจริงแล้ว)
- ใช้ใน Timeline 1: **Adjustment Clip บน V2** (0–67 วินาที, คอมพ์ 60 fps เฟรม 0 = ต้นไทม์ไลน์) ค่า default T0 840 / MoveAt 144 / WriteAt 180 ตรงวินาทีที่ 14 / 17
- ข้อความ: Text+ ตัวเดียว `CC_Text` จัดกลางที่ (TextX 0.75, TextY 0.5), Size 0.085, LineSpacing 1.3,
  write on ด้วย **Write On ของ Text+ เอง** (`End` = `CC_Ctrl.pWrite` ไล่ 0→1 จาก T0+WriteAt ยาว WriteDur 300 เฟรม) ไม่มี row mask แล้ว
- พื้นหลังครึ่งขวามืดลงตาม write on: `CC_DimMask` (ขอบนุ่ม DimSoft 0.12) → `CC_DimFill` ดำ → `CC_OverDim` Blend = DimMax(0.45) × eDim
  eDim = smoothstep(pWrite) × (1−pOut) ภาพทดสอบที่ 19 และ 22.5 วินาที: ข้อความอ่านชัดขึ้นมาก ฝั่งซ้ายไม่โดน
- ฟอนต์ Open Sans Sukhumvit Bold แสดงภาษาไทยถูกต้องใน Text+ (สระ/วรรณยุกต์ไม่ลอย)

## ค่าที่ใช้จริงล่าสุด (V2 Adjustment Clip, 60 fps)
- T0 180 (ปกขึ้นวินาทีที่ 3) · MoveAt 804 (เลื่อนซ้าย 16.4–17.0) · WriteAt 840 (write on 17–22) · OutAt 1440 (ออก 27) · TextX 0.72
- ช่วงขาเข้ายาวขึ้น 2 เท่า (`INTRO = 2` ใน generator): เบลอเข้า T0−0.2 → +0.8 วิ, ปก +0.2 → +0.9, เส้นทอง +0.7 → +1.2, ชื่อ +1.0 → +1.5
- มุมปกมน: `CC_CoverMask` สูงเท่าปก (CoverW × CoverAspect × 16/9) และ CornerRadius = CoverRadius 0.12
  ความสูงคิดจาก CoverAspect ไม่อ่านจากภาพ เพราะ mask นี้ส่งเข้า CC_CoverPlace (อ่าน HalfH จะเป็นวง) ใน V2 ที่ใช้อยู่ใส่ 0.5625 ตรงๆ ใน expression
