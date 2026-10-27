"""Component layout (resolve-basic §1) for an exported Fusion comp.

Main line: from MediaOut1 follow the Background chain back to MediaIn; it sits on one row at the
bottom, left -> right. Each main-line merge's Foreground is a component placed above it, its last
merge in the same column. Inside a component the merges stack top -> bottom (Background comes
from above) and each layer comes in from the left on its merge's row (mask -> source -> merge).
Positions only; writes JSON {name: [x, y]} in .comp pixels (for copy_pos / apply into a file), or with
--cells in FlowView grid cells (1 = one node: 110 px wide, 33 px tall), which is what the MCP
fusion_comp set_position takes. Passing pixels to set_position spreads nodes 110x / 33x too far.

usage: python comp_layout.py [--cells] <in.comp> <out.json>
"""
import json
import re
import sys

COL, ROW = 110, 33
sys.setrecursionlimit(10000)
CELLS = "--cells" in sys.argv
if CELLS:
    sys.argv.remove("--cells")


def block_end(s, i):
    d = 0
    for j in range(s.index("{", i), len(s)):
        if s[j] == "{":
            d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0:
                return j + 1


text = open(sys.argv[1], encoding="utf-8").read()
start = text.index("\n\tTools = ")
end = block_end(text, start)
tools = {}
for m in re.finditer(r"\n\t\t(\w+) = ([\w.]+) \{", text[start:end]):
    a = start + m.start() + 1
    tools[m.group(1)] = (m.group(2), text[a:block_end(text, a)])
owner = {n: n for n in tools}
for n, (_, body) in tools.items():
    for inner in re.findall(r"\n\t{3,}(\w+) = [\w.]+ \{", body):
        owner.setdefault(inner, n)

# inputs[n] = ordered list of (input name, source tool) at this node's own level
inputs = {}
for n, (t, body) in tools.items():
    lst = []
    if t == "GroupOperator":
        srcs = re.findall(r'SourceOp = "(\w+)"', body)
        for s in srcs:
            s = owner.get(s, s)
            if s in tools and s != n and s not in [x for _, x in lst]:
                lst.append(("In", s))
    else:
        ib = re.search(r"\n\t\t\tInputs = \{", body)
        if ib:
            seg = body[ib.start():block_end(body, ib.start() + 1)]
            for m in re.finditer(r"\n\t\t\t\t(\w+) = Input \{\s*SourceOp = \"(\w+)\",\s*Source = \"\w+\"", seg):
                s = owner.get(m.group(2), m.group(2))
                if s in tools and s != n:
                    lst.append((m.group(1), s))
    inputs[n] = lst

used = set()
pos = {}


def get(n, key):
    for k, s in inputs[n]:
        if k == key:
            return s


def size(n, mode):
    """(width cols, height rows) of the subtree drawn for n, without placing."""
    return place(n, 0, 0, mode, dry=True)


def place(n, x, y, mode, dry=False, seen=None):
    """Place subtree with n at (x, y) = its bottom-right cell. Returns (w, h) in cells.
    mode 'comp': Background above (spine), Foreground to the left on the same row.
    mode 'layer': all inputs to the left; first on n's row, others stacked above."""
    seen = set() if seen is None else seen
    if n in seen or (not dry and n in used):
        return (0, 0)
    seen.add(n)
    if not dry:
        used.add(n)
        pos[n] = (x, y)
    t = tools[n][0]
    if mode == "comp" and t == "Merge":
        # spine: collect merges going up through Background
        spine = [n]
        cur = n
        while True:
            bg = get(cur, "Background")
            if bg and tools[bg][0] == "Merge" and bg not in seen:
                spine.append(bg)
                seen.add(bg)
                cur = bg
            else:
                break
        top_bg = get(spine[-1], "Background")
        # heights of each row block, from the bottom merge up
        blocks = []
        for m in spine:
            fg = get(m, "Foreground")
            extra = [s for k, s in inputs[m] if k not in ("Background", "Foreground")]
            fw, fh = place(fg, 0, 0, "layer", True, set(seen)) if fg else (0, 0)
            ew, eh = 0, 0
            for e in extra:
                a, b = place(e, 0, 0, "layer", True, set(seen))
                ew, eh = max(ew, a), eh + b
            blocks.append((m, fg, extra, max(fw, ew), max(1, fh) + eh, max(1, fh)))
        y_cur = y
        width = 1
        for m, fg, extra, fw, h, fh in blocks:
            if not dry:
                used.add(m)
                pos[m] = (x, y_cur)
            if fg:
                place(fg, x - 1, y_cur, "layer", dry, seen)
            ey = y_cur - fh
            for e in extra:
                ew, eh = place(e, x - 1, ey, "layer", dry, seen)
                ey -= eh
            width = max(width, 1 + fw)
            y_cur -= h
        h_total = y - y_cur
        if top_bg:
            bw, bh = place(top_bg, x, y_cur, "comp", dry, seen)
            width, h_total = max(width, bw), h_total + bh
        return (width, h_total)
    # layer mode (or a non-merge in comp mode): inputs to the left, stacked upward
    width, height = 1, 1
    yy = y
    first = True
    for k, s in inputs[n]:
        sub_mode = "comp" if tools[s][0] == "Merge" else "layer"
        w, h = place(s, x - 1, yy, sub_mode, dry, seen)
        if w == 0:
            continue
        width = max(width, 1 + w)
        height = max(height, (y - yy) + h)
        yy -= h
        first = False
    return (width, height)


# main line
out = "MediaOut1" if "MediaOut1" in tools else None
chain = []
cur = out
while cur:
    chain.append(cur)
    nxt = None
    t = tools[cur][0]
    if t == "Merge":
        nxt = get(cur, "Background")
    elif inputs[cur]:
        nxt = inputs[cur][0][1]
    cur = nxt if nxt and nxt not in chain else None
chain.reverse()                        # MediaIn ... MediaOut
used.update(chain)
x = 0
for n in chain:
    side = [s for k, s in inputs[n] if not (s in chain)]
    w = 1
    for s in side:
        mode = "comp" if tools[s][0] == "Merge" else "layer"
        sw, sh = place(s, 0, 0, mode, True, set(used))
        w = max(w, sw)
    x += w
    pos[n] = (x, 0)
    yy = -1
    for s in side:
        mode = "comp" if tools[s][0] == "Merge" else "layer"
        sw, sh = place(s, x, yy, mode)
        yy -= sh
# anything left (unconnected / disabled leftovers): own components to the left, above row 0
rest = [n for n in tools if n not in used and "ViewInfo" in tools[n][1]]
roots = [n for n in rest if not any(s == n for m in rest for _, s in inputs[m])]
x0 = min((p[0] for p in pos.values()), default=0) - 2
for r in roots:
    if r in used:
        continue
    mode = "comp" if tools[r][0] == "Merge" else "layer"
    w, h = place(r, 0, 0, mode, True, set(used))
    place(r, x0, -1, mode)
    x0 -= w + 1
for n in rest:
    if n not in used:
        x0 -= 1
        pos[n] = (x0, -1)
sx, sy = (1, 1) if CELLS else (COL, ROW)
json.dump({n: [p[0] * sx, p[1] * sy] for n, p in pos.items()}, open(sys.argv[2], "w"))
print("placed", len(pos), "of", len([n for n in tools if "ViewInfo" in tools[n][1]]))
