import sys, json, re
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl")
import vlib
ROOT = vlib.ROOT
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/"
W = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0070"}
L = []
# item 4: separate-copy (5. 재무제표 주석) 보험수익 note, row 보험계약마진상각, table with 구분|당분기|전분기 (quarter) or 3개월/누적 (half/Q3)
SPEC = {"2023.1Q": ("FY2024_Q1", 41440), "2023.2Q": ("FY2024_Q2", 43099), "2023.3Q": ("FY2024_Q3", 42167), "2023.4Q": ("FY2024_Q4", 58224)}
for q, (fy, st) in SPEC.items():
    for t in vlib.tables(fy):
        if t["start"] == st:
            hdr = [[c[1] for c in r["cells"]] for r in t["rows"][:3]]
            row = [r for r in t["rows"] if r["cells"] and r["cells"][0][1].strip() == "보험계약마진상각"][0]
            nums = [vlib.num(c[1]) for c in row["cells"][1:]]
            # prior cumulative = last numeric
            val = nums[-1]
            # which section
            lines = vlib.load(fy)
            sec = None
            for j in range(st, 0, -1):
                s = re.sub(r"<[^>]*>", "", lines[j - 1]).strip()
                if re.match(r"^\d+\.\s*(연결)?재무제표 주석", s): sec = s; break
            L.append("%s %s T%d L%d section=%s hdr=%s nums=%s -> prior cum %s | master item4 %s | %s" % (q, fy, st, row["line"], sec, hdr[:3], nums, val, W[(q, 4)]["값"], "OK" if abs(val - W[(q, 4)]["값"]) < 1e-9 else "MISMATCH"))
# item 5: show 위험조정 rows in the original Q1 2023 filing and where 272 appears
f = ROOT + "/data/dart/FY2023_Q1/raw/KR0070_에이비엘생명보험/xml/20230515002903.xml"
lines = open(f, encoding="utf-8", errors="replace").read().split("\n")
for i, ln in enumerate(lines, 1):
    s = re.sub(r"<[^>]*>", "", ln).strip()
    if s in ("272", "(272)"):
        ctx = [re.sub(r"<[^>]*>", "", lines[j]).strip() for j in range(max(0, i - 40), i)]
        ctx = [c for c in ctx if c and not re.match(r"^[\d,().\-]+$", c)]
        L.append("orig FY2023_Q1 L%d value %s ; preceding labels: %s" % (i, s, ctx[-3:]))
open(OUT + "v14_item4_item5.txt", "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
