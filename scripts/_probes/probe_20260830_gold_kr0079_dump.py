# -*- coding: utf-8 -*-
"""Dump ALL KR0079 gold entries (data/_gold/user_csm_cells.json) to a UTF-8 file for
comparison against the post-fix waterfall_for_dir() output. Read-only."""
import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

d = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
lines = []
for e in d.get("set", []):
    if e.get("원보험사코드") == "KR0079":
        lines.append(f"{e.get('공시분기')} item{e.get('항목번호')} 값={e.get('값')} was={e.get('was')} why={(e.get('why') or e.get('note') or '')}")

lines.sort()
out = ROOT / "scripts/_probes/_out_20260830_gold_kr0079_dump.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {out} ({len(lines)} entries)")
