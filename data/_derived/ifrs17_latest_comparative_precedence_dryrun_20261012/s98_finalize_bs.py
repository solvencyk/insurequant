"""Read-only: finalise the BS year-end verdicts after the cross-domain gate ripple check and build cand/IFRS17_BS.RECOMMENDED.json.

Evidence (candrun/RECOMMENDED.ilp_lic.txt vs candrun/LIVE_NOW.ilp_lic.txt): adopting the latest comparative BS item 20 of 롯데손해보험 2023.4Q and 교보생명보험 2023.4Q
creates two NEW R-LIC1 findings - the ILP item 15 (보험계약부채 합계) of those blocks is the ORIGINAL print and no longer ties to the restated BS item 20.
BS and ILP-LIC are one verification unit for these two blocks, so they are '조건부(ILP 동반 필요)' (the ILP latest comparative is not read by this dry run -> not adopted).
All other BS blocks keep '최신 채택(진짜 재작성 †)'.  bs_block_verdicts.csv gets two extra columns (verdict_final, ripple_note).
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COND = {("KR0003", "2023.4Q"), ("KR0073", "2023.4Q")}
rows = list(csv.DictReader(open(HERE / "bs_block_verdicts.csv", encoding="utf-8-sig")))
for r in rows:
    if (r["kr"], r["quarter"]) in COND:
        r["verdict_final"] = "조건부(ILP 동반 필요)"
        r["ripple_note"] = "ILP 항목 15(원 공시값)가 재작성 BS 항목 20과 안 맞아 R-LIC1 YELLOW 신규 발생 - BS+ILP-LIC 동반 채택 필요, ILP 최신 비교 컬럼 미판독"
    else:
        r["verdict_final"] = r["verdict"]
        r["ripple_note"] = ""
cols = list(rows[0].keys())
with open(HERE / "bs_block_verdicts.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print("BS verdict_final:", {v: sum(1 for r in rows if r["verdict_final"] == v) for v in {r["verdict_final"] for r in rows}})

bs_rows = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
final = {(r["kr"], r["quarter"]): r["verdict_final"] for r in rows}
bscan = [r for r in csv.DictReader(open(HERE / "bs_4q_scan.csv", encoding="utf-8-sig")) if r["cls"] == "RESTATED_STALE"]
bidx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in bs_rows}
changed = 0
for r in bscan:
    if final.get((r["kr"], r["quarter"]), "").startswith("최신 채택") and r["later"] not in ("", "None"):
        key = (r["kr"], int(r["item"]), r["quarter"])
        if key in bidx:
            nv = float(r["later"])
            if bidx[key]["값"] != nv:
                bidx[key]["값"] = nv
                changed += 1
(HERE / "cand" / "IFRS17_BS.RECOMMENDED.json").write_text(json.dumps(bs_rows, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("BS RECOMMENDED candidate: cells changed", changed)
