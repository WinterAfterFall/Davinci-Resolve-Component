"""List the top-level tools of a .comp that MediaOut1 does not depend on (candidates to disable).

A tool counts as used if MediaOut1 reaches it through SourceOp links (into groups too) or through
an expression that names it. Animation splines are skipped. usage: python -I find_unused.py <comp>
"""
import io
import re
import sys

t = io.open(sys.argv[1], encoding="utf-8", newline="").read().replace("\r\n", "\n")


def block_end(s, i):
    depth = 0
    for j in range(s.index("{", i), len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return j + 1


start = t.index("\n\tTools = ")
end = block_end(t, start)
body = t[start:end]
tools = {}
for m in re.finditer(r"\n\t\t(\w+) = ([\w.]+) \{", body):
    a = m.start() + 1
    tools[m.group(1)] = (m.group(2), body[a:block_end(body, a)])

# links to a group's output name the tool inside the group, so map inner names to their group
owner = {n: n for n in tools}
for n, (_, b) in tools.items():
    for inner in re.findall(r"\n\t{3,}(\w+) = [\w.]+ \{", b):
        owner.setdefault(inner, n)
deps = {n: {owner.get(x, x) for x in re.findall(r'SourceOp = "(\w+)"', b)} - {n} for n, (_, b) in tools.items()}
expr_refs = {n: {owner.get(x, x) for x in re.findall(r"\b([A-Za-z_]\w*)\.",
                                                     " ".join(re.findall(r'Expression = "([^"]*)"', b)))} - {n}
             for n, (_, b) in tools.items()}
used, todo = set(), ["MediaOut1"]
while todo:
    n = todo.pop()
    if n in used or n not in tools:
        continue
    used.add(n)
    todo += list(deps[n]) + list(expr_refs[n])
# expressions anywhere in used tools may name others (already followed); also keep MediaIn1
unused = [n for n in tools if n not in used and tools[n][0] not in ("BezierSpline", "PolyPath", "XYPath")]
print("tools", len(tools), "used", len(used))
for n in unused:
    pt = "\n\t\t\tPassThrough = true," in tools[n][1]
    print("UNUSED", n, tools[n][0], "(already off)" if pt else "")
