# -*- coding: utf-8 -*-
"""read-only: dump the rows of the table that starts at line N (1-based) of a filing: label | all cells (text@line)."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
rel, start = sys.argv[1], int(sys.argv[2])
L = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
TAG = re.compile(r"<[^>]+>")


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ")).strip()


a = start - 1
assert re.match(r"\s*<TABLE\b", L[a]), L[a]
depth, b = 0, a
for k in range(a, len(L)):
    if re.match(r"\s*<TABLE\b", L[k]):
        depth += 1
    if re.match(r"\s*</TABLE", L[k]):
        depth -= 1
        if depth == 0:
            b = k
            break
print(f"table L{a+1}-L{b+1}")
k = a
while k <= b:
    if re.match(r"\s*<TR\b", L[k]):
        j = k
        while not re.match(r"\s*</TR", L[j]):
            j += 1
        cells = []
        for q in range(k, j + 1):
            m = re.match(r"\s*<(TD|TE|TH)\b[^>]*>(.*)$", L[q])
            if m:
                rest = m.group(2)
                if re.search(r"</(TD|TE|TH)>\s*$", rest):
                    cells.append(f"{clean(rest)}@{q+1}")
                else:
                    buf, ln, z = [], None, q
                    if clean(rest):
                        buf.append(clean(rest)); ln = q + 1
                    z = q + 1
                    while z <= j and not re.match(r"\s*</(TD|TE|TH)", L[z]):
                        t = clean(L[z])
                        if t:
                            buf.append(t)
                            if ln is None:
                                ln = z + 1
                        z += 1
                    cells.append(f"{' '.join(buf)}@{ln}")
        print(f"L{k+1}: " + " | ".join(cells))
        k = j
    k += 1
