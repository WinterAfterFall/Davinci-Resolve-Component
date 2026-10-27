"""Pre-export check of a Fusion .comp (export it first with timeline_item_fusion export_comp).

Looks for what tends to break or black out a render of an Adjustment / Fusion clip:
  - comp RenderRange outside GlobalRange, or reversed
  - MediaIn GlobalIn/GlobalOut not matching the comp range (typical after cutting a clip)
  - Loader clips: missing file, TrimIn > TrimOut, GlobalStart > GlobalEnd, and a clip range that
    does not cover the comp range with nothing (Loop / HoldLastFrame / Extend) to fill the gap
  - links (SourceOp) to tools that do not exist
  - expressions naming tools that do not exist
  - links or expressions into tools that are PassThrough (disabled): fine to read controls from,
    but an image taken from a disabled tool is a pass-through of its input, check it is intended

usage: python -I check_render.py <comp> [<comp> ...]     exit code 1 if any ERROR
"""
import os
import re
import sys

BUILTINS = {"self", "comp", "math", "string", "table", "os", "fu", "app", "bmd", "Point", "Text",
            "Input", "Output", "Background", "Foreground", "Image", "time", "iif", "fusion"}


def block_end(s, i):
    depth = 0
    for j in range(s.index("{", i), len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return j + 1


def check(path):
    t = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    out = []

    def say(level, msg):
        out.append((level, msg))

    rr = re.search(r"\n\tRenderRange = \{ (-?\d+), (-?\d+) \}", t)
    gr = re.search(r"\n\tGlobalRange = \{ (-?\d+), (-?\d+) \}", t)
    r0, r1 = (int(rr.group(1)), int(rr.group(2))) if rr else (None, None)
    if rr and r0 > r1:
        say("ERROR", f"RenderRange reversed {r0}..{r1}")
    if rr and gr and not (int(gr.group(1)) <= r0 and r1 <= int(gr.group(2))):
        say("ERROR", f"RenderRange {r0}..{r1} outside GlobalRange {gr.group(1)}..{gr.group(2)}")

    start = t.index("\n\tTools = ")
    end = block_end(t, start)
    names, passthrough, blocks = set(), set(), {}
    for m in re.finditer(r"\n\t{2,}(\w+) = ([\w.]+) \{", t[start:end]):
        names.add(m.group(1))
    for m in re.finditer(r"\n\t\t(\w+) = ([\w.]+) \{", t[start:end]):
        a = start + m.start() + 1
        blocks[m.group(1)] = (m.group(2), t[a:block_end(t, a)])
        if "\n\t\t\tPassThrough = true," in blocks[m.group(1)][1]:
            passthrough.add(m.group(1))

    for n, (ttype, b) in blocks.items():
        if n in passthrough:
            continue
        if ttype == "Loader" and n.startswith("MediaIn"):
            gi = re.search(r"GlobalIn = Input \{ Value = (-?\d+)", b)
            go = re.search(r"GlobalOut = Input \{ Value = (-?\d+)", b)
            if rr and gi and go and (int(gi.group(1)), int(go.group(1))) != (r0, r1):
                say("WARN", f"{n}: GlobalIn/Out {gi.group(1)}..{go.group(1)} != comp range {r0}..{r1}")
        for c in re.finditer(r"Clip \{(.*?)\n\t+\}", b, re.S):
            cb = c.group(1)
            fn = re.search(r'Filename = "([^"]*)"', cb)
            if fn and fn.group(1) and not os.path.exists(fn.group(1).replace("\\\\", "\\")):
                say("ERROR", f"{n}: file missing {fn.group(1)}")

            def num(key):
                m2 = re.search(rf"\b{key} = (-?\d+)", cb)
                return int(m2.group(1)) if m2 else None

            ti, to, gs, ge = num("TrimIn"), num("TrimOut"), num("GlobalStart"), num("GlobalEnd")
            if ti is not None and to is not None and to and ti > to:
                say("ERROR", f"{n}: TrimIn {ti} > TrimOut {to}")
            if gs is not None and ge is not None and gs > ge:
                say("ERROR", f"{n}: clip GlobalStart {gs} > GlobalEnd {ge}")
            fills = (re.search(r"Loop = Input \{ Value = 1", b) or re.search(r"HoldLastFrame = Input \{ Value = [1-9]", b)
                     or (num("ExtendFirst") or 0) > 0 or (num("ExtendLast") or 0) > 0)
            if rr and not fills and ((gs is not None and gs > r0) or (ge is not None and ge < r1)):
                say("WARN", f"{n}: clip range {gs}..{ge} does not cover comp {r0}..{r1} (black frames)")

        for s in set(re.findall(r'SourceOp = "(\w+)"', b)):
            if s not in names:
                say("ERROR", f"{n}: linked to missing tool {s}")
            elif s in passthrough:
                say("INFO", f"{n}: takes an image from disabled {s} (gets {s}'s input instead)")
        for e in re.findall(r'Expression = "([^"]*)"', b):
            for ref in set(re.findall(r"(?<![\w.])([A-Za-z_]\w*)\.\w", e)):
                if ref in BUILTINS:
                    continue
                if ref not in names:
                    say("ERROR", f"{n}: expression names missing tool {ref}: {e[:70]}")
                elif ref in passthrough:
                    say("INFO", f"{n}: expression reads disabled {ref} (controls still readable)")
    return out


bad = False
for p in sys.argv[1:]:
    res = check(p)
    errs = [r for r in res if r[0] == "ERROR"]
    bad = bad or bool(errs)
    print(f"== {os.path.basename(p)}: {len(errs)} error, {sum(r[0] == 'WARN' for r in res)} warn, "
          f"{sum(r[0] == 'INFO' for r in res)} info")
    for level, msg in sorted(set(res)):
        print(f"  {level:5} {msg}")
sys.exit(1 if bad else 0)
