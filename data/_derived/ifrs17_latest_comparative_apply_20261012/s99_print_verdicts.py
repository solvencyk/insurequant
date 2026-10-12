"""Read-only: print selected census verdict groups (conditional / both-impossible / not re-judged / 현행 유지) with their notes."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
DR = ROOT / "data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012"
rows = list(csv.DictReader(open(DR / "census_blocks.csv", encoding="utf-8-sig")))
want = sys.argv[1:] or ["조건부(동반 블록 필요)", "둘 다 불가(현행 유지+목록)", "재판정 안 함(이전 라운드)"]
for r in rows:
    if r["verdict"] in want:
        print(f"[{r['verdict']}] {r['domain']} {r['code']} {r['company']} {r['quarter']} n_diff={r['n_diff']} gold={r['gold_conflict']} joint={r['joint_group']}")
        print("   note:", r["note"][:700])
        print("   blind:", r["blind_spots"], "| closure_cur:", r["closure_current"][:120], "| closure_lat:", r["closure_latest"][:120])
