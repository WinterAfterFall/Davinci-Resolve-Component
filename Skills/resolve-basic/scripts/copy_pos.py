"""Copy node positions (ViewInfo Pos) from a layout comp into another comp, nothing else.

usage: python copy_pos.py <layout.comp> <target.comp> <out.comp>
"""
import re
import sys

POS = re.compile(r"(\n\t\t\tViewInfo = \w+ \{\s*Pos = \{ )(-?[\d.e-]+), (-?[\d.e-]+)( \})")   # the tool's own, not a group member's


def blocks(t):
    """name -> (start, end) of each top-level tool block."""
    out = {}
    for m in re.finditer(r"\n\t\t(\w+) = [\w.]+ \{", t):
        z = t.find("\n\t\t}", m.end())
        out[m.group(1)] = (m.start(), z)
    return out


src = open(sys.argv[1], encoding="utf-8").read()
dst = open(sys.argv[2], encoding="utf-8").read()
pos = {}
for n, (a, z) in blocks(src).items():
    m = POS.search(src, a, z)
    if m:
        pos[n] = (m.group(2), m.group(3))
moved, added = 0, 0
for n, (a, z) in sorted(blocks(dst).items(), key=lambda kv: -kv[1][0]):   # back to front keeps offsets
    if n not in pos:
        continue
    x, y = pos[n]
    m = POS.search(dst, a, z)
    if m:
        dst = dst[:m.start()] + f"{m.group(1)}{x}, {y}{m.group(4)}" + dst[m.end():]
        moved += 1
    else:
        sep = "" if dst[z - 1] == "," else ","
        dst = dst[:z] + f"{sep}\n\t\t\tViewInfo = OperatorInfo {{ Pos = {{ {x}, {y} }} }}," + dst[z:]
        added += 1
open(sys.argv[3], "w", encoding="utf-8", newline="\n").write(dst)
print("moved", moved, "added", added, "of", len(pos))
