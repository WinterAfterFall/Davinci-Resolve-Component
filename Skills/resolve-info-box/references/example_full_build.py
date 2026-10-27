# -*- coding: utf-8 -*-
# Generate Lua to build the pop-up box animation in the Fusion comp of the V2 Adjustment Clip.

states = [
 # key,           W,     text  (lines auto -> Height).  arrow = », multiply = ×
 ("T1",  0.30, """การโจมตีปกติ
- ธาตุลม เป้าเดี่ยว
- = 50% Max HP ของ Robin"""),
 ("T2a", 0.36, """สกิลต่อสู้ » เรียก Bessie
- กดครั้งแรก: เรียก Bessie
- Max HP = 70% Max HP Robin
- SPD = 180% SPD Robin"""),
 ("T2b", 0.36, """สกิลต่อสู้ » กดซ้ำ
- ถ้ามี Bessie อยู่: ฟื้น HP 100%
- Robin ได้ Vibes +6"""),
 ("T3a", 0.37, """ระบบ Vibes
- สะสม Vibes ได้สูงสุด 50
- ได้จาก: เพื่อนตี, ฮีล/ชิลด์ครั้งแรก"""),
 ("T3b", 0.37, """Vibes » Deviated Chords
- เพื่อน ATK สูง: บัฟ ATK (ตาม HP Robin)
- เพื่อน ATK ต่ำ: บัฟ CRIT DMG (+40%)
- อยู่ 2 เทิร์น, แรงขึ้นตาม Vibes"""),
 ("T3c", 0.37, """Vibes » สรุปสั้นๆ
- ตัวสาย ATK: Robin บัฟ ATK ให้
- ไม่ใช่สาย ATK: บัฟ CRIT DMG แทน"""),
 ("T4",  0.37, """อัลติ » แบ่ง Vibes
- กดอัลติใส่เพื่อน แล้วเพื่อนออกโจมตี
- Robin ได้ Vibes +2"""),
 ("T5",  0.384, """Improvised Blues (Groove)
- ได้ฮีล/ชิลด์จากเพื่อน: Groove สูงสุด 12
- Vibes ครั้งแรก: Groove 1 = พลังงาน +3"""),
 ("T6a", 0.37, """เรียกฝูงนกเพิ่ม
- Vibes ครบ 6 » เรียก Drummie
- Vibes ครบ 12 » เรียก Paddie"""),
 ("T6b", 0.37, """นกครบ 3 » เข้า Fever
- สลัด CC ออกจาก Robin + ฝูงนก
- เข้า Fever + กางโซนพิเศษทันที"""),
 ("T7a", 0.384, """โซน Fever
- เพื่อนทำดาเมจ: เจาะเกราะ +15% (+Vibes)
- Robin + ฝูงนก อิมมูน CC ตลอด Fever
- Robin ไม่เข้าเทิร์นจนกว่า Fever จบ"""),
 ("T7b", 0.37, """Fever » ฝูงนกบนสนาม
- ศัตรูรับดาเมจเพิ่ม 8% / 12% / 16%
- ตามจำนวนนก (1 / 2 / 3 ตัว)"""),
 ("T8a", 0.384, """สกิลฝูงนก (Memosprite)
- ถึงเทิร์นนก: ร่ายสกิลเองอัตโนมัติ
- ธาตุลม ใส่ศัตรูทุกตัว = 150% Max HP นก"""),
 ("T8b", 0.384, """Fever » ตัวนับถอยหลัง
- ตัวนับ (SPD 140) โผล่บนแถบแอคชั่น
- เพิ่มดาเมจ Robin + ฝูงนก +60%"""),
 ("T8c", 0.384, """Fever » หัก Vibes
- ถึงเทิร์นตัวนับ: หัก Vibes 50%
- Vibes = 0: ฝูงนกหาย, ออกจาก Fever"""),
 ("T9a", 0.384, """E1 » Stray Bird of Summer
- นกจำดาเมจเพื่อน (ที่ไม่ใช่ True) 100%
- ใช้สกิลนก: +True DMG 11% ของที่จำ
- ลงศัตรูเลือดมากสุด, ล้างค่าที่จำ 50%"""),
 ("T9b", 0.37, """E4 » Her Variation on the Theme
- เข้า Fever: ได้ Vibes ฟรี 12 ทันที
- SPD ฝูงนก +20% (+Vibes)"""),
 ("T9c", 0.384, """E6 » A Song Yet Unnamed
- ตัวคูณดาเมจสกิลนก +100% ของเดิม
- ระหว่าง Fever: อัลติ Robin สะสม 2 ครั้ง
- เข้า Fever ครั้งแรก: คืนพลังงาน 140"""),
 ("T10a",0.384, """Ultimate
- เร่งแอคชั่นเพื่อน 1 คน +100%
- คืนพลังงานให้คนนั้น 20% ของสูงสุด"""),
 ("T10b",0.384, """Ultimate » Special Guest
- มอบ Special Guest ให้เพื่อน 2 เทิร์น
- เพื่อน/ซัมมอนตี: แบ่ง Vibes ให้ Robin
- ระหว่างติด เลื่อนแอคชั่นคนอื่นไม่ได้"""),
 ("T11", 0.384, """Trace » Rebuilt Harmony
- Robin + ฝูงนก: CRIT Rate +50% ตรงๆ
- ไม่มีเงื่อนไขพิเศษใดๆ"""),
]

def H(text):
    n = text.count("\n") + 1
    return round(0.102 + (n-1)*0.065, 4)

# transitions: (from_state_index -> to_state_index), type, frames
# switch: (Cs, Ce, Sw, Os, Oe)   soft: (Ws, We, Sw, Ts, Te)
T = [
 ("open",   None, 0,   dict(Os=40,   Oe=100,  Sw=30)),
 ("switch", 0,    1,   dict(Cs=470,  Ce=530,  Sw=531,  Os=532,  Oe=592)),
 ("soft",   1,    2,   dict(Ws=1650, We=1680, Sw=1681, Ts=1682, Te=1712)),
 ("switch", 2,    3,   dict(Cs=2060, Ce=2120, Sw=2121, Os=2122, Oe=2182)),
 ("soft",   3,    4,   dict(Ws=3120, We=3150, Sw=3151, Ts=3152, Te=3182)),
 ("soft",   4,    5,   dict(Ws=4260, We=4290, Sw=4291, Ts=4292, Te=4322)),
 ("switch", 5,    6,   dict(Cs=5250, Ce=5310, Sw=5311, Os=5312, Oe=5372)),
 ("switch", 6,    7,   dict(Cs=5900, Ce=5960, Sw=5961, Os=5962, Oe=6022)),
 ("switch", 7,    8,   dict(Cs=6850, Ce=6910, Sw=6911, Os=6912, Oe=6972)),
 ("soft",   8,    9,   dict(Ws=7690, We=7720, Sw=7721, Ts=7722, Te=7752)),
 ("switch", 9,    10,  dict(Cs=8250, Ce=8310, Sw=8311, Os=8312, Oe=8372)),
 ("soft",   10,   11,  dict(Ws=9380, We=9410, Sw=9411, Ts=9412, Te=9442)),
 ("switch", 11,   12,  dict(Cs=9840, Ce=9900, Sw=9901, Os=9902, Oe=9962)),
 ("soft",   12,   13,  dict(Ws=10760,We=10790,Sw=10791,Ts=10792,Te=10822)),
 ("soft",   13,   14,  dict(Ws=11260,We=11290,Sw=11291,Ts=11292,Te=11322)),
 ("switch", 14,   15,  dict(Cs=11960,Ce=12020,Sw=12021,Os=12022,Oe=12082)),
 ("soft",   15,   16,  dict(Ws=13260,We=13290,Sw=13291,Ts=13292,Te=13322)),
 ("soft",   16,   17,  dict(Ws=13760,We=13790,Sw=13791,Ts=13792,Te=13822)),
 ("switch", 17,   18,  dict(Cs=14620,Ce=14680,Sw=14681,Os=14682,Oe=14742)),
 ("soft",   18,   19,  dict(Ws=15400,We=15430,Sw=15431,Ts=15432,Te=15462)),
 ("switch", 19,   20,  dict(Cs=15870,Ce=15930,Sw=15931,Os=15932,Oe=15992)),
 ("close",  20,   None,dict(Cs=16620,Ce=16680)),
]

switch_kf = []   # (frame, val)
width_kf  = []
height_kf = []
start_kf  = []
end_kf    = []

W0 = states[0][1]; H0 = H(states[0][2])
switch_kf += [(0,0.0)]
width_kf  += [(0,W0)]
height_kf += [(0,H0)]
start_kf  += [(0,0.0)]
end_kf    += [(0,1.0)]

for kind, a, b, f in T:
    Wb = states[b][1] if b is not None else states[a][1]
    Hb = H(states[b][2]) if b is not None else H(states[a][2])
    Wa = states[a][1] if a is not None else states[b][1]
    Ha = H(states[a][2]) if a is not None else H(states[b][2])
    if kind == "open":
        switch_kf += [(f["Os"],0.0),(f["Oe"],1.0)]
        start_kf  += [(f["Sw"],0.0)]
        end_kf    += [(f["Sw"],1.0)]
    elif kind == "switch":
        switch_kf += [(f["Cs"],1.0),(f["Ce"],0.0),(f["Os"],0.0),(f["Oe"],1.0)]
        width_kf  += [(f["Cs"],Wa),(f["Ce"],Wb)]
        height_kf += [(f["Cs"],Ha),(f["Ce"],Hb)]
        start_kf  += [(f["Cs"],0.0),(f["Sw"],0.0)]
        end_kf    += [(f["Cs"],1.0),(f["Sw"],1.0)]
    elif kind == "soft":
        # box stays open; wipe out old text, resize during wipe, type on new
        start_kf  += [(f["Ws"],0.0),(f["We"],1.0),(f["Sw"],0.0),(f["Te"],0.0)]
        end_kf    += [(f["We"],1.0),(f["Sw"],0.0),(f["Ts"],0.0),(f["Te"],1.0)]
        width_kf  += [(f["Ws"],Wa),(f["We"],Wb)]
        height_kf += [(f["Ws"],Ha),(f["We"],Hb)]
    elif kind == "close":
        switch_kf += [(f["Cs"],1.0),(f["Ce"],0.0)]

# StyledText expression chain, boundaries = each state's swap frame (next state starts at its Sw)
bounds = []  # (upper_frame_exclusive, state_index)
swaps = [None]*len(states)
for kind,a,b,f in T:
    if b is not None:
        swaps[b] = f["Sw"]
swaps[0] = T[0][3]["Sw"]  # 30
# state i active for time < swaps[i+1]
expr_parts = []
for i in range(len(states)-1):
    nxt = swaps[i+1]
    txt = states[i][2].replace("\n","\\n")
    expr_parts.append('time < %d and "%s"' % (nxt, txt))
expr_parts.append('"%s"' % states[-1][2].replace("\n","\\n"))
expr = " or ".join(expr_parts)

def dedup(kfs):
    d = {}
    for fr,v in kfs:
        d[fr] = v
    return sorted(d.items())

def emit(inp_path, kfs):
    lines = ['r.Switch = nil'] if False else []
    out = []
    for fr,v in dedup(kfs):
        out.append('%s[%d] = %s' % (inp_path, fr, repr(float(v))))
    return "\n".join(out)

lua = []
lua.append('local comp = fusion:GetCurrentComp()')
lua.append('comp:StartUndo("popup_build")')
lua.append('comp:Lock()')
lua.append('local r = comp:FindTool("rect")')
lua.append('local t = comp:FindTool("Text1")')
lua.append('local okrun, errrun = pcall(function()')
lua.append('-- remove any pre-existing BezierSpline modifiers (from earlier tests)')
lua.append('for i,tool in pairs(comp:GetToolList(false, "BezierSpline")) do pcall(function() tool:Delete() end) end')
lua.append('pcall(function() t.StyledText:SetExpression(nil) end)')
lua.append('')
for inp, kfs, var in [("Switch",switch_kf,"r"),("Width",width_kf,"r"),("Height",height_kf,"r"),
                      ("Start",start_kf,"t"),("End",end_kf,"t")]:
    lua.append('%s.%s = comp:AddTool("BezierSpline", -32768, -32768)' % (var, inp))
    for fr,v in dedup(kfs):
        lua.append('%s.%s[%d] = %s' % (var, inp, fr, repr(float(v))))
    lua.append('')
lua.append('t.Size = 0.037')
lua.append('t.StyledText:SetExpression(')
lua.append('  ' + repr(expr))
lua.append(')')
lua.append('end)')
lua.append('comp:Unlock()')
lua.append('comp:EndUndo(true)')
lua.append('if not okrun then print("ERROR:", tostring(errrun)) end')
lua.append('print("switch kf:", %d)' % len(dedup(switch_kf)))
lua.append('print("width kf:", %d, " height kf:", %d)' % (len(dedup(width_kf)), len(dedup(height_kf))))
lua.append('print("start kf:", %d, " end kf:", %d)' % (len(dedup(start_kf)), len(dedup(end_kf))))
lua.append('print("styledtext @100 =[" .. tostring(comp.Text1.StyledText[100]) .. "]")')
lua.append('print("styledtext @2000 =[" .. tostring(comp.Text1.StyledText[2000]) .. "]")')
lua.append('print("switch @70 =", comp.rect.Switch[70], " @600=", comp.rect.Switch[600], " @16700=", comp.rect.Switch[16700])')
lua.append('print("height @600 =", comp.rect.Height[600], " width @600 =", comp.rect.Width[600])')

src = "\n".join(lua)
open("popup_kf.lua","w",encoding="utf-8").write(src)
print(src)
print("\n\n--- expr repr len:", len(expr))
