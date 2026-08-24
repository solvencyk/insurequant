# -*- coding: utf-8 -*-
"""probe_20260822_backlog_quarter_dist.py -- read-only. Inspect
scripts/_probes/_tier2_backlog_lists.json: which bucket has KR0009/2023.1Q,
and does 2023.1Q dominate the "no_table"/"intermittent_38" backlog (would
support an initial-quarter-format hypothesis for the TFI table gap)."""
from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

P = Path(r"C:\Users\sangwook.cho\Desktop\insurequant\scripts\_probes\_tier2_backlog_lists.json")
d = json.loads(P.read_text(encoding="utf-8"))

for key, lst in d.items():
    print(f"=== bucket '{key}'  n={len(lst)} ===")
    if isinstance(lst, list) and lst and isinstance(lst[0], dict) and "quarter" in lst[0]:
        qc = Counter(x["quarter"] for x in lst)
        for q in sorted(qc):
            print(f"    {q}: {qc[q]}")
        hit = [x for x in lst if x.get("code") == "KR0009"]
        if hit:
            print(f"    KR0009 entries: {hit}")
    else:
        print(f"    sample: {lst[:3]}")
    print()
