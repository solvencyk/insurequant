"""Read-only: the PL write plan (cells to put into data/_gold/user_pl_cells.json) from the restated blocks.

Source of values: restated_blocks_alt.json 'restated_alt' (Tier-1 = FS-API comparative columns; Tier-2 = production Kyobo handler on the PRIOR cumulative
column, with the same row also accepted under the label '발생한보험서비스수익').  Only cells whose value differs from the live master (CHANGED) or is
empty in the live master (FILL) are planned.  Judgement flags are written into the plan:
  ALT_LABEL_ITEM6   item 6/7 of 2023.4Q and 2024.1Q need the '…수익' label reading (production reader returns None there)
  TAG_DRIFT_EXCLUDED 2024.2Q items 29/32: FS-API tag drift (raw statement prints 14,941,109,245원 for the equity-FVOCI line = master item 29) -> not a restatement
Outputs pl_plan.json and prints counts.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
TOL = 5e-4
TARGETS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"]
EXCLUDE = {("2024.2Q", 29): "TAG_DRIFT_EXCLUDED", ("2024.2Q", 32): "TAG_DRIFT_EXCLUDED"}
ALT6 = {("2023.4Q", 6), ("2023.4Q", 7), ("2024.1Q", 6), ("2024.1Q", 7)}

alt = json.loads((HERE / "restated_blocks_alt.json").read_text(encoding="utf-8"))
root = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
names, cur = {}, {}
for r in root:
    if r["원보험사코드"] == "KR0073":
        names[r["항목번호"]] = r["항목명"]
        cur.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")

plan, skipped = [], []
for q in TARGETS:
    rb = alt[q]["restated_alt"]
    for i in range(1, 33):
        old, new = cur[q].get(i), rb.get(str(i))
        if new is None:
            if old is not None:
                skipped.append({"quarter": q, "item": i, "reason": "restated value unreadable, old kept", "old": old})
            continue
        if old is not None and abs(old - new) <= TOL:
            continue
        flag = EXCLUDE.get((q, i))
        if flag:
            skipped.append({"quarter": q, "item": i, "reason": flag, "old": old, "restated_reading": new})
            continue
        flags = []
        if (q, i) in ALT6:
            flags.append("ALT_LABEL_ITEM6")
        plan.append({"quarter": q, "item": i, "name": names[i], "old": old, "new": new, "cls": "FILL" if old is None else "CHANGED", "flags": flags})

# 2024.2Q: items 29/32 excluded => the OCI sum identity (25 = 26+27+28+29+30+32) must still hold with the kept old values
(HERE / "pl_plan.json").write_text(json.dumps({"plan": plan, "skipped": skipped}, ensure_ascii=False, indent=1), encoding="utf-8")
by_q = {}
for c in plan:
    by_q.setdefault(c["quarter"], {"CHANGED": 0, "FILL": 0})[c["cls"]] += 1
print("planned cells:", len(plan), by_q)
print("skipped:", json.dumps(skipped, ensure_ascii=False))
