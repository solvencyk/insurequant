"""ready_cells_merge: one file with every READY candidate cell (PL + CSM) -> ready_cells_ALL.csv  (READ-ONLY)"""
import csv, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
H = M.MEASURE
cols = ["sheet", "scenario", "code", "company", "quarter", "item", "item_name", "old", "new", "delta", "gold_overlap_old_gold_value", "later_filing", "source_table", "cite(label|line|text)", "how"]
out = []
for scn in ("R0_KBlife_2024Q1_fix", "R1", "R1b_KB_siblings", "R2", "R2b_Lotte_2023_1Q2Q"):
    for r in csv.DictReader(open(H / f"ready_cells_{scn}.csv", encoding="utf-8-sig")):
        r["sheet"] = "PL"
        r["source_table"] = ""
        if scn == "R0_KBlife_2024Q1_fix":   # same-filing master-error fix (abs() on 총 재보험수익): cites from the ORIGINAL filing's income statement
            r["later_filing"] = "data/dart/FY2024_Q1/raw/KR0099_케이비라이프생명보험/xml/20240516001445.xml (SAME filing; no later filing involved)"
            r["cite(label|line|text)"] = {"8": "재보험영업수익|L25538|(568) ; 재보험영업비용|L25589|1,400 => -568-1,400 = -1,968",
                                          "2": "보험영업수익|L25521|202,164 (item3 unchanged) + item8 -1,968",
                                          "12": "item8 -1,968 - (9+10+11 = -808, unchanged)"}.get(r["item"], "")
            r["how"] = "master error: extract_tier2_kblife _jang_rerev/_jang_recost read with abs(); 재보험수익 is negative (-568)"
        out.append({c: r.get(c, "") for c in cols})
for r in csv.DictReader(open(H / "ready_csm_cells.csv", encoding="utf-8-sig")):
    out.append({c: r.get(c, "") for c in cols})
with open(H / "ready_cells_ALL.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(out)
from collections import Counter
print(len(out), Counter(r["sheet"] for r in out), "with cite:", Counter((r["sheet"], bool(r["cite(label|line|text)"])) for r in out))
