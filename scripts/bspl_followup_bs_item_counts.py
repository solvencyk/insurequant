#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Row counts per BS item: golden fixture vs git HEAD vs the working master (read-only) -> shows what the BS golden would see."""
import json, subprocess, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
fx = json.loads((ROOT / "tests/fixtures/ifrs17_bs_golden.json").read_text(encoding="utf-8"))
head = json.loads(subprocess.run(["git", "show", "HEAD:IFRS17_BS.json"], cwd=ROOT, capture_output=True).stdout.decode("utf-8"))
cur = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
ch, cc = Counter(str(r["항목번호"]) for r in head), Counter(str(r["항목번호"]) for r in cur)
print("fixture rows", fx["rows"], "HEAD rows", len(head), "working rows", len(cur))
print(f"{'item':>4} {'fixture':>8} {'HEAD':>6} {'now':>6} {'now-HEAD':>9}")
for k in sorted(set(fx["rows_per_item"]) | set(ch) | set(cc), key=int):
    print(f"{k:>4} {fx['rows_per_item'].get(k, 0):>8} {ch.get(k, 0):>6} {cc.get(k, 0):>6} {cc.get(k, 0) - ch.get(k, 0):>9}")
