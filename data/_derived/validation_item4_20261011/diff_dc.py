import re, sys
sys.stdout.reconfigure(encoding="utf-8")
D = "data/_derived/validation_item4_20261011/"
def parse(fn):
    out = []
    for l in open(D + fn, encoding="utf-8"):
        m = re.match(r"\s+(RED|YELLOW)\s+\[([^\]]+)\]\s+(\S+)\s+(.*)$", l.rstrip())
        if m:
            out.append((m.group(1), m.group(2), m.group(3), m.group(4).strip()))
    return out
a, b = parse(sys.argv[1]), parse(sys.argv[2])
from collections import Counter
ca, cb = Counter(a), Counter(b)
print("before", Counter(x[0] for x in a), "after", Counter(x[0] for x in b))
print("--- gone")
for k in sorted((ca - cb).elements()): print("  ", k)
print("--- new")
for k in sorted((cb - ca).elements()): print("  ", k)
