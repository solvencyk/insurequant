# -*- coding: utf-8 -*-
"""Read-only: print the rows of the table that contains physical line N: label, line of label, all value cells with lines.  usage: p09_table_rows.py <rel> <line N>"""
import re, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
rel, N = sys.argv[1], int(sys.argv[2])
L = open(ROOT + rel, encoding="utf-8", errors="replace").read().split("\n")
TAG = re.compile(r"<[^>]+>")
a = N - 1
while a > 0 and not re.match(r"\s*<TABLE\b", L[a], re.I):
    a -= 1
b = N - 1
while b < len(L) - 1 and not re.match(r"\s*</TABLE", L[b], re.I):
    b += 1
print(f"table L{a+1}-{b+1}")
k = a
while k <= b:
    if re.match(r"\s*<TR\b", L[k], re.I):
        j = k
        while not re.match(r"\s*</TR", L[j], re.I):
            j += 1
        cells = []
        q = k
        while q <= j:
            m = re.match(r"\s*<(TD|TE|TH)\b([^>]*)>(.*)$", L[q], re.I)
            if m:
                rest = m.group(3)
                buf = [TAG.sub("", rest).strip()] if TAG.sub("", rest).strip() else []
                tl = q + 1 if buf else None
                p = q
                if not re.search(r"</(TD|TE|TH)>\s*$", rest, re.I):
                    p = q + 1
                    while p <= j and not re.match(r"\s*</(TD|TE|TH)", L[p], re.I):
                        t = TAG.sub("", L[p]).strip()
                        if t:
                            buf.append(t)
                            if tl is None:
                                tl = p + 1
                        p += 1
                cs = re.search(r'COLSPAN="(\d+)"', m.group(2), re.I)
                rs = re.search(r'ROWSPAN="(\d+)"', m.group(2), re.I)
                cells.append((m.group(1).upper(), " ".join(buf), tl or q + 1, int(cs.group(1)) if cs else 1, int(rs.group(1)) if rs else 1))
                q = p
            q += 1
        print(f"TR{k+1}: " + " | ".join(f"{t[:60]}@{l}" + (f"[cs{cs}]" if cs > 1 else "") + (f"[rs{rs}]" if rs > 1 else "") for (_tag, t, l, cs, rs) in cells))
        k = j
    k += 1
