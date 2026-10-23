# -*- coding: utf-8 -*-
"""Read-only: dump the '4-2. 포괄손익계산서' rows (label, ACODE, per-ACONTEXT-period values with physical lines) of a Lotte DART xml.  usage: p08_stmt_dump.py <rel>"""
import re, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
rel = sys.argv[1]
L = open(ROOT + rel, encoding="utf-8", errors="replace").read().split("\n")
TAG = re.compile(r"<[^>]+>")
t0 = next(k for k, s in enumerate(L) if s.startswith("<TITLE") and re.search(r"4-2\.\s*포괄손익계산서", s))
t1 = next(k for k in range(t0 + 1, len(L)) if L[k].startswith("<TITLE"))
# THEAD
th = [re.sub(r"\s+", " ", TAG.sub("", L[k])).strip() for k in range(t0, t1) if re.match(r"\s*<TH\b", L[k])]
print("THEAD cells:", th)
# periods from the title-block
for k in range(t0, t1):
    if "기 20" in L[k] and "부터" in L[k]:
        print("period line", k + 1, TAG.sub("", L[k]).strip())
    if "단위" in L[k] and "<TE" not in L[k]:
        print("unit line", k + 1, TAG.sub("", L[k]).strip())
rows = []
k = t0
while k < t1:
    if re.match(r"\s*<TR", L[k]):
        j = k
        while not re.match(r"\s*</TR", L[j]):
            j += 1
        cells = []
        q = k
        while q <= j:
            m = re.match(r"\s*<(TE|TD)\b([^>]*)>", L[q])
            if m:
                attrs = m.group(2)
                acode = re.search(r'ACODE="([^"]*)"', attrs)
                actx = re.search(r'ACONTEXT="([^"]*)"', attrs)
                # text: same line or following lines until </TE>
                txt = TAG.sub("", L[q]).strip()
                p = q
                ln_text = q + 1 if txt else None
                buf = [txt] if txt else []
                while not re.search(r"</(TE|TD)>", L[p]):
                    p += 1
                    t = TAG.sub("", L[p]).strip()
                    if t:
                        buf.append(t)
                        if ln_text is None:
                            ln_text = p + 1
                cells.append(dict(acode=acode.group(1) if acode else "", ctx=(actx.group(1)[:8] if actx else ""), text=" ".join(buf), line=ln_text or q + 1))
                q = p
            q += 1
        if cells:
            rows.append((k + 1, cells))
        k = j
    k += 1
for tr, cells in rows:
    lab = cells[0]
    vals = " | ".join(f"{c['ctx']}:{c['text']}@{c['line']}" for c in cells[1:])
    print(f"TR{tr} L{lab['line']} [{lab['text']}] {cells[1]['acode'] if len(cells) > 1 else ''} => {vals}")
