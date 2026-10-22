# -*- coding: utf-8 -*-
"""Note 50 (separate basis) '재작성이 포괄손익계산서에 미치는 영향' tables of FY2025 Q1/Q2/Q3 filings -> rows (label, before, after, delta, line) in 백만원 (rounded print)."""
import re, sys, json
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
import KR0083_xml as X
RE_TAG = re.compile(r"<[^>]+>")
def num(t):
    t = t.replace(",", "").strip()
    if t in ("", "-"): return 0.0 if t == "-" else None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try: v = float(t)
    except ValueError: return None
    return -v if neg else v
def read(fy):
    lines = X.load_lines(fy)
    # locate note 50 heading (separate basis) = the 2nd occurrence of '회계정책의 변경' note start with '50.'
    start = [i for i, l in enumerate(lines) if "50. 회계정책의 변경" in l][0]
    t0 = [i for i in range(start, len(lines)) if "재무제표의 소급재작성이 포괄손익계산서에 미치는 영향" in lines[i]][0]
    t1 = [i for i in range(t0, len(lines)) if "재무제표의 소급재작성이 현금흐름표에 미치는 영향" in lines[i]][0]
    rows, cur, cell = [], None, None
    for i in range(t0, t1):
        l = lines[i]
        if l.startswith("<TR"):
            cur = []
        elif l.startswith("</TR"):
            if cur: rows.append(cur)
            cur = None
        if cur is not None:
            if l.startswith("<TD") or l.startswith("<TH"):
                cell = [i + 1, ""]
            if cell is not None:
                cell[1] += " " + RE_TAG.sub("", l)
                if "</TD>" in l or "</TH>" in l:
                    cur.append((cell[1].replace("\u3000", " ").strip(), cell[0])); cell = None
    return t0 + 1, t1 + 1, rows
out = {}
L = []
for fy in ("FY2025_Q1", "FY2025_Q2", "FY2025_Q3"):
    a, b, rows = read(fy)
    L.append(f"=== {fy} {X.FILES[fy]} L{a}-L{b}")
    out[fy] = []
    for r in rows:
        txt = [t for t, _ in r]
        if len(r) == 5 and num(r[1][0]) is not None:
            d = dict(label=re.sub(r"\s+", " ", txt[0]).strip(), before=num(txt[1]), after=num(txt[3]), delta=num(txt[4]), line_before=r[1][1], line_after=r[3][1], line_delta=r[4][1], label_line=r[0][1])
            out[fy].append(d)
            L.append(f"  L{d['label_line']} {d['label']:<28} before={d['before']} (L{d['line_before']}) after={d['after']} (L{d['line_after']}) delta={d['delta']} (L{d['line_delta']})")
        else:
            L.append(f"  ?? {txt[:6]}")
open("KR0083_note50.json", "w", encoding="utf-8", newline="\n").write(json.dumps(out, ensure_ascii=False, indent=1))
open("KR0083_note50.txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
