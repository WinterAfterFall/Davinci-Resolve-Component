"""Lay out the top-level nodes of a Fusion .comp so every link runs left to right.

Each node goes in a column to the right of all its inputs (layered layout); a node with no
inputs is pulled right to sit just before its first consumer. Inside a column nodes are
ordered by where their inputs sit, so most links come out level or running down.
Only ViewInfo positions change. A link into a group counts from the node feeding the group.

usage: python layout_comp.py <in.comp> <out.comp>     lay out, then report backward links
       python layout_comp.py --check <in.comp>         only report backward links
"""
import re
import sys

COL, ROW = 130, 40
POS = re.compile(r"(\n\t\t\tViewInfo = \w+ \{\s*Pos = \{ )(-?[\d.e-]+), (-?[\d.e-]+)( \})")   # the tool's own, not a group member's


def block_end(s, i):
    depth = 0
    for j in range(s.index("{", i), len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return j + 1


def read(text):
    """top-level tools -> (start, end), and their input links (sources per node)."""
    start = text.index("\n\tTools = ")
    end = block_end(text, start)
    spans = {}
    for m in re.finditer(r"\n\t\t(\w+) = ([\w.]+) \{", text[start:end]):
        a = start + m.start() + 1
        spans[m.group(1)] = (a, block_end(text, a), m.group(2))
    owner = {n: n for n in spans}
    for n, (a, z, _) in spans.items():
        for inner in re.findall(r"\n\t{3,}(\w+) = [\w.]+ \{", text[a:z]):
            owner.setdefault(inner, n)
    nodes = [n for n, (a, z, _) in spans.items() if POS.search(text, a, z) or "ViewInfo" in text[a:z]]
    flow = set(nodes)
    deps = {}
    for n in nodes:
        a, z, _ = spans[n]
        body = text[a:z]
        if spans[n][2] == "GroupOperator":
            # only links that enter the group from outside, not wiring between its own tools
            src = {owner.get(s, s) for s in re.findall(r'SourceOp = "(\w+)"', body)}
        else:
            src = {owner.get(s, s) for s in re.findall(r'SourceOp = "(\w+)"', body)}
        deps[n] = {s for s in src if s in flow and s != n}
    return spans, nodes, deps


def positions(text, spans, nodes):
    out = {}
    for n in nodes:
        a, z, _ = spans[n]
        m = POS.search(text, a, z)
        if m:
            out[n] = (float(m.group(2)), float(m.group(3)))
    return out


def backward(pos, deps):
    bad = []
    for n, srcs in deps.items():
        for s in srcs:
            if s in pos and n in pos:
                (sx, sy), (nx, ny) = pos[s], pos[n]
                if nx < sx or (nx == sx and ny < sy):
                    bad.append((s, n))
    return bad


def layout(nodes, deps):
    cons = {n: set() for n in nodes}
    for n, srcs in deps.items():
        for s in srcs:
            cons[s].add(n)
    col, busy = {}, set()

    def depth(n):
        if n in col:
            return col[n]
        if n in busy:          # a loop through expressions-free links should not happen; break it
            return 0
        busy.add(n)
        col[n] = 1 + max((depth(s) for s in deps[n]), default=-1)
        busy.discard(n)
        return col[n]

    for n in nodes:
        depth(n)
    # pull nodes right, next to their nearest consumer, without passing any of their inputs
    for n in sorted(nodes, key=lambda k: -col[k]):
        if cons[n]:
            col[n] = max(col[n], min(col[c] for c in cons[n]) - 1)
    cols = {}
    for n in nodes:
        cols.setdefault(col[n], []).append(n)
    y = {}
    order = {n: i for i, n in enumerate(nodes)}
    for c in sorted(cols):            # left to right: sit level with your inputs
        want = {n: (sum(y[s] for s in deps[n] if s in y) / len([s for s in deps[n] if s in y])
                    if any(s in y for s in deps[n]) else None) for n in cols[c]}
        placed = sorted(cols[c], key=lambda n: (want[n] is None, want[n] or 0, order[n]))
        last = None
        for n in placed:
            w = want[n] if want[n] is not None else (last + ROW if last is not None else 0)
            y[n] = w if last is None else max(w, last + ROW)
            last = y[n]
    for c in sorted(cols, reverse=True):   # inputs-free nodes: line up with their consumer
        for n in cols[c]:
            if not deps[n] and cons[n]:
                y[n] = min(y[k] for k in cons[n])
        placed = sorted(cols[c], key=lambda n: (y[n], order[n]))
        last = None
        for n in placed:
            if last is not None and y[n] < last + ROW:
                y[n] = last + ROW
            last = y[n]
    return {n: (col[n] * COL, y[n]) for n in nodes}


def write(text, spans, pos):
    for n, (a, z, _) in sorted(spans.items(), key=lambda kv: -kv[1][0]):
        if n not in pos:
            continue
        x, y = pos[n]
        m = POS.search(text, a, z)
        if m:
            text = text[:m.start()] + f"{m.group(1)}{x:g}, {y:g}{m.group(4)}" + text[m.end():]
    return text


if sys.argv[1] == "--check":
    t = open(sys.argv[2], encoding="utf-8").read()
    sp, nd, dp = read(t)
    bad = backward(positions(t, sp, nd), dp)
    print("nodes", len(nd), "backward links", len(bad), bad[:12])
else:
    t = open(sys.argv[1], encoding="utf-8").read()
    sp, nd, dp = read(t)
    print("before: backward links", len(backward(positions(t, sp, nd), dp)))
    p = layout(nd, dp)
    t = write(t, sp, p)
    open(sys.argv[2], "w", encoding="utf-8", newline="\n").write(t)
    sp, nd, dp = read(t)
    bad = backward(positions(t, sp, nd), dp)
    print("after: nodes", len(nd), "backward links", len(bad), bad[:12])
