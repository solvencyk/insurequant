"""Read-only: YTD monotonicity scan of the PL master. For flow items whose sign is stable inside a fiscal year, |YTD| must not shrink from Qn to Qn+1.
A shrink flags a candidate for 3-month-as-cumulative (or a plain misread). Output printed + scan_monotone.csv."""
import csv, json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
rows = json.load(open(R + "PL_breakdown.json", encoding="utf-8"))
names, ser = {}, defaultdict(dict)
for r in rows:
    names[r["원보험사코드"]] = r["원수사명"]
    if r["값"] is not None:
        ser[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
out = []
for (code, item), s in sorted(ser.items(), key=lambda x: (x[0][0], str(x[0][1]))):
    for y in (2023, 2024, 2025, 2026):
        qs = [f"{y}.{n}Q" for n in (1, 2, 3, 4)]
        for a, b in zip(qs, qs[1:]):
            if a in s and b in s:
                va, vb = s[a], s[b]
                if va is None or vb is None:
                    continue
                if abs(va) < 50:
                    continue
                same = (va > 0) == (vb > 0)
                # flag: same sign and |YTD| shrinks by more than 3% (+ minimal absolute 20 backed by 백만원), or magnitude drops below 70% regardless of sign
                if same and abs(vb) < abs(va) * 0.97 and abs(va) - abs(vb) > 20:
                    out.append((code, names[code], item, a, va, b, vb, round(vb / va, 3)))
with open("scan_monotone.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["code", "name", "item", "q_from", "ytd_from", "q_to", "ytd_to", "ratio"])
    w.writerows(out)
print("flags:", len(out))
from collections import Counter
print(Counter(o[2] for o in out).most_common(40))
print(Counter(o[3][5] + "->" + o[5][5] for o in out))
# show Q1->Q2 and Q2->Q3 flags for items that are monotone by nature
nat = {1, 4, 5, 9, 10, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24}
for o in out:
    if o[3][5] in "12" and o[2] in nat:
        print(o)
