"""Read-only: print csm_block_verdicts.csv rows except 변화 없음 / 추출 불가 in compact form. usage: python s21_show_verdicts.py [verdict-substring]"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
want = sys.argv[1] if len(sys.argv) > 1 else None
rows = list(csv.DictReader(open(HERE / "csm_block_verdicts.csv", encoding="utf-8-sig")))
for r in rows:
    if r["verdict"] in ("변화 없음", "비교 컬럼 추출 불가", "마스터 칸 없음"):
        continue
    if want and want not in r["verdict"]:
        continue
    print(f"{r['verdict']:18s} {r['kr']} {r['name'][:7]:7s} {r['quarter']} items={r['diff_items']:7s} tier={r['tier']:10s} gold={r['gold_cells']:12s} ilp(cur/lat)={r.get('ilp_agrees_current')}/{r.get('ilp_agrees_latest')}")
    print(f"     cur {r['current']}")
    print(f"     lat {r['latest']}")
    if r["current_violations"] or r["latest_violations"]:
        print(f"     viol cur=[{r['current_violations']}] lat=[{r['latest_violations'][:160]}]")
    if r["note"]:
        print("     note:", r["note"][:160])
