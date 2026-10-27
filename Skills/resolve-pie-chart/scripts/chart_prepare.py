# -*- coding: utf-8 -*-
"""
chart_prepare.py -- plan a WAF pie chart and prepare the exported chart comp for it.

    python chart_prepare.py inspect <exported.comp>
    python chart_prepare.py prepare spec.json

The chart lives in a Fusion Composition built from the user's template: a PopupTextBoxWithTitle panel
("Damage Source" header) over a MultiMerge whose layers are PieChartV2 instances (one per slice).
Fusion suffixes inner tool names on paste (CC, CC_3, CC_4, ...), so every instance is mapped by reading
which tools its group references.

spec.json
{
  "comp_in":  "<ExportFusionComp of the chart clip>",
  "comp_out": "<prepared comp to ImportFusionComp>",
  "cfg_out":  "<Lua table for chart_apply.lua>",
  "item_id":  "<unique id of the chart timeline item>",
  "header":   "Damage Source",             # optional: panel title
  "position": 0.25,                        # PieChartV2 Position: 0..1 = 0..360 deg, 0 = +X axis, CCW
  "ccw": 1,                                # CounterClockwise
  "height": 0.283,                         # circle radius control
  "slices": [ {"label": "En ESkill", "percent": 59.2, "color": null, "angle": null,
               "title_size": null, "label_size": null, "line1": null, "line2": null}, ... ]
}

Star Rail convention:
  Percent = the real number; slices sorted largest -> smallest, stacked bottom -> top, same Position;
  Value   = 100 - sum of every percent larger than this slice   (70/20/10 -> Value 100/30/10).
"""
import json, re, sys

TITLE_SIZES = [0.079, 0.0655, 0.0555, 0.0492, 0.045, 0.042]
LABEL_SIZES = [0.0686, 0.055, 0.05, 0.0468, 0.044, 0.042]
LINE2 = [0.198, 0.202, 0.23, 0.254, 0.26, 0.27]
COLORS = ["#C68D1C", "#E9AC30", "#FFB149", "#FFD48A", "#FFE7BF", "#FFF3DE"]
ROLES = ("CC", "RW", "MatteControl1", "Ellipse1", "Color", "LineAngle", "Line1", "Line2", "Title", "PC")


def match_brace(text, start):
    i = text.index("{", start)
    depth, in_str, esc = 0, False, False
    for j in range(i, len(text)):
        c = text[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j
    raise ValueError("unbalanced braces")


def top_tools(t):
    out = {}
    for m in re.finditer(r"\n\t\t(\w+) = ([A-Za-z][\w.]*) \{", t):
        out[m.group(1)] = (m.group(2), m.start(), match_brace(t, m.start()) + 1)
    return out


def inspect(t):
    tools = top_tools(t)
    pies, header = [], None
    for name, (ty, s, e) in tools.items():
        if ty != "GroupOperator":
            continue
        blk = t[s:e]
        roles = {}
        for src in re.findall(r'SourceOp = "(\w+)"', blk):
            roles.setdefault(re.sub(r"(_\d+)+$", "", src), src)
        mo = re.search(r'MainOutput1 = InstanceOutput \{\s*SourceOp = "(\w+)"', blk)
        if all(r in roles for r in ("CC", "RW", "PC")):
            pies.append({"group": name, "out": mo.group(1), **{r: roles.get(r) for r in ROLES}})
        else:
            for tm in re.finditer(r"\n\t+(\w+) = TextPlus \{", blk):
                tb = blk[tm.start():match_brace(blk, tm.start()) + 1]
                m = re.search(r'StyledText = Input \{ Value = "((?:[^"\\]|\\.)*)"', tb)
                if m and header is None:
                    header = {"group": name, "tool": tm.group(1), "text": m.group(1)}
    layers = {}
    mm_name = next((n for n, (ty, _, _) in tools.items() if ty == "MultiMerge"), None)
    if mm_name:
        _, s, e = tools[mm_name]
        for k, src in re.findall(r'\["Layer(\d+)\.Foreground"\] = Input \{\s*SourceOp = "(\w+)"', t[s:e]):
            layers[int(k)] = src
    by_out = {p["out"]: p for p in pies}
    stacked = [by_out[layers[k]] for k in sorted(layers) if layers[k] in by_out]
    spare = [p for p in pies if p not in stacked]
    return {"multimerge": mm_name, "layers": layers, "stacked": stacked, "spare": spare, "header": header}


def prepare(spec):
    t = open(spec["comp_in"], encoding="utf-8", newline="").read()
    info = inspect(t)
    if not info["multimerge"]:
        sys.exit("no MultiMerge in this comp -- not the WAF chart template")
    slices = sorted(spec["slices"], key=lambda s: -float(s["percent"]))
    n = len(slices)
    use = list(info["stacked"])
    mm = info["multimerge"]
    tools = top_tools(t)
    _, ms, me = tools[mm]
    mm_blk = t[ms:me]

    # connect spare instances as extra top layers
    driver = use[0]["CC"] if use else None
    while len(use) < n:
        if not info["spare"]:
            sys.exit("template has %d pie instances, %d slices requested -- add instances in Fusion first" % (len(use), n))
        p = info["spare"].pop(0)
        k = max(info["layers"] or {0: 0}) + 1
        info["layers"][k] = p["out"]
        new_in = '["Layer%d.Foreground"] = Input {\n\t\t\t\t\tSourceOp = "%s",\n\t\t\t\t\tSource = "Output",\n\t\t\t\t},\n\t\t\t\t' % (k, p["out"])
        name_re = re.compile(r"LayerName%d = Input \{ Value = \"[^\"]*\", \}" % k)
        if name_re.search(mm_blk):
            mm_blk = name_re.sub(new_in + 'LayerName%d = Input { Value = "%s Layer", }' % (k, p["out"]), mm_blk, count=1)
        else:
            mm_blk = re.sub(r"(\n\t\t\t\},\n\t\t\tViewInfo)", ",\n\t\t\t\t" + new_in.rstrip("\t\n") + r"\1", mm_blk, count=1)
        lo = re.search(r"LayerOrder = Input \{ Value = ScriptVal \{ \{ \[0\] = ([\d, ]+) \} \}", mm_blk)
        if lo:
            order = [int(x) for x in lo.group(1).split(",")]
            if k not in order:
                order.append(k)
                mm_blk = mm_blk.replace(lo.group(0), "LayerOrder = Input { Value = ScriptVal { { [0] = %s } }" % ", ".join(map(str, order)))
        use.append(p)
        # the new slice follows the first slice's Switch animation
        gs, ge = tools[p["group"]][1], tools[p["group"]][2]
        gblk = t[gs:ge]
        cm = re.search(r"\n\t+%s = EllipseMask \{" % re.escape(p["CC"]), gblk)
        cs, ce = cm.start(), match_brace(gblk, cm.start()) + 1
        cblk = gblk[cs:ce]
        sw = re.search(r"Switch = Input \{(?:[^{}]|\{[^{}]*\})*\},", cblk)
        cblk = cblk[:sw.start()] + 'Switch = Input { Value = 0, Expression = "%s.Switch", },' % driver + cblk[sw.end():]
        gblk = gblk[:cs] + cblk + gblk[ce:]
        t = t[:gs] + gblk + t[ge:]
        tools = top_tools(t)
        _, ms, me = tools[mm]
        t = t[:ms] + mm_blk + t[me:]
        tools = top_tools(t)
        _, ms, me = tools[mm]
        mm_blk = t[ms:me]

    # more instances than slices: disconnect the extra top layers
    extra = use[n:]
    for p in extra:
        k = next(k for k, v in info["layers"].items() if v == p["out"])
        mm_blk = re.sub(r'\["Layer%d\.Foreground"\] = Input \{\s*SourceOp = "\w+",\s*Source = "Output",\s*\},\s*' % k, "", mm_blk, count=1)
    if extra:
        t = t[:ms] + mm_blk + t[me:]
    use = use[:n]
    open(spec["comp_out"], "w", encoding="utf-8", newline="").write(t)

    # values, angles, looks
    theta0 = float(spec.get("position", 0.25)) * 360.0
    sign = 1 if int(spec.get("ccw", 1)) == 1 else -1
    before = 0.0
    vals = []
    for s in slices:
        vals.append(round(100.0 - before, 4))
        before += float(s["percent"])
    cfg_slices = []
    for i, (s, p) in enumerate(zip(slices, use)):
        hi, lo = vals[i] / 100.0, (vals[i + 1] / 100.0 if i + 1 < n else 0.0)
        a_lo, a_hi = theta0 + sign * 360 * lo, theta0 + sign * 360 * hi
        mid = s.get("angle")
        if mid is None:
            mid = (theta0 + sign * 360 * (hi + lo) / 2 + 180) % 360 - 180
        pick = lambda key, table: s.get(key) if s.get(key) is not None else table[min(i, len(table) - 1)]
        col = (s.get("color") or COLORS[min(i, len(COLORS) - 1)]).lstrip("#")
        cfg_slices.append({
            "tools": {r: p[r] for r in ROLES}, "group": p["group"], "label": s["label"], "percent": float(s["percent"]),
            "value": vals[i], "angle": round(mid, 2), "wedge": [round(min(a_lo, a_hi), 1), round(max(a_lo, a_hi), 1)],
            "rgb": [round(int(col[j:j + 2], 16) / 255.0, 6) for j in (0, 2, 4)],
            "title_size": pick("title_size", TITLE_SIZES), "label_size": pick("label_size", LABEL_SIZES),
            "line1": s.get("line1") or 0.164, "line2": pick("line2", LINE2),
        })
    cfg = {"item_id": spec["item_id"], "comp": spec["comp_out"], "position": spec.get("position", 0.25),
           "ccw": spec.get("ccw", 1), "height": spec.get("height", 0.283), "slices": cfg_slices,
           "header": spec.get("header"), "header_tool": info["header"] and info["header"]["tool"]}
    open(spec["cfg_out"], "w", encoding="utf-8").write("return " + lua(cfg) + "\n")
    for c in cfg_slices:
        print("%-14s %-12s percent %5.1f value %6.2f angle %7.2f  wedge %s" % (c["group"], c["label"], c["percent"], c["value"], c["angle"], c["wedge"]))
    print("layers:", info["layers"], "disconnected:", [p["group"] for p in extra])


def lua(v):
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "nil"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, list):
        return "{ " + ", ".join(lua(x) for x in v) + " }"
    if isinstance(v, dict):
        return "{ " + ", ".join('["%s"] = %s' % (k, lua(x)) for k, x in v.items()) + " }"
    raise TypeError(v)


if __name__ == "__main__":
    if sys.argv[1] == "inspect":
        info = inspect(open(sys.argv[2], encoding="utf-8", newline="").read())
        print(json.dumps(info, ensure_ascii=False, indent=1))
    else:
        prepare(json.load(open(sys.argv[2], encoding="utf-8")))
