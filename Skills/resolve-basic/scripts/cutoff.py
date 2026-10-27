"""Which top-level nodes still render in a piece, once disabled tools pass through.

A disabled Merge passes only its Background; any other disabled tool passes only its first image
input. Prints how many nodes are reached from MediaOut1 and the still-enabled nodes that are cut
off (not computed at render). With --reached it also lists the reached nodes, to confirm a cut piece
computes only the components it shows (resolve-basic §4).

usage: python cutoff.py [--reached] <comp>
"""
import re
import sys

SHOW_REACHED = "--reached" in sys.argv
if SHOW_REACHED:
    sys.argv.remove("--reached")


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


def own_header(body):
    """the tool's own attribute lines before its Inputs block (PassThrough sits there)."""
    i = body.find("\n\t\t\tInputs = ")
    return body if i < 0 else body[:i]


disabled = {n for n, (_, b) in tools.items() if re.search(r"\n\t\t\tPassThrough = true", own_header(b))}
inputs = {}
for n, (t, body) in tools.items():
    lst = []
    if t == "GroupOperator":
        for s in re.findall(r'SourceOp = "(\w+)"', body):
            s = owner.get(s, s)
            if s in tools and s != n and ("In", s) not in lst:
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

seen = set()
stack = ["MediaOut1"]
while stack:
    n = stack.pop()
    if n in seen:
        continue
    seen.add(n)
    ins = inputs[n]
    if n in disabled:
        if tools[n][0] == "Merge":
            ins = [x for x in ins if x[0] == "Background"]
        else:
            ins = ins[:1]
    stack += [s for _, s in ins]
cut = [n for n in tools if n not in seen and n not in disabled and "ViewInfo" in tools[n][1]]
print("disabled", len(disabled), "reached", len(seen), "cut", len(cut))
print(",".join(cut))
if SHOW_REACHED:
    print("reached:", ",".join(sorted(seen)))
