# -*- coding: utf-8 -*-
"""a15 (read-only, in-process): validate_live_artifacts.check_csm_amort_schedule on the PRE-FIX panel vs the rebuilt panel.
Nothing is written (the baseline file is only read).  Prints the findings that appear / disappear and the baseline lines that are
now STALE (the defect they list no longer exists) -- removing those lines is validation's job, not parser's."""
from __future__ import annotations

import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_live_artifacts as G  # noqa: E402

OLD = ROOT / "data/_derived/amort_fix_backup_20261011/csm_amort_schedule.json.pre_fix"
real_load = G.load


def run(use_old: bool):
    def patched(rel):
        if use_old and rel == "data/dart/viz/csm_amort_schedule.json":
            return json.loads(OLD.read_text(encoding="utf-8"))
        return real_load(rel)
    G.load = patched
    try:
        fd = G.Findings()
        stat = G.check_csm_amort_schedule(fd)
    finally:
        G.load = real_load
    return {f"{r['artifact']}|{r['rule']}|{r['key']}": r for r in fd.rows}, dict(stat)


before, sb = run(True)
after, sa = run(False)
base = G.load_baseline().get("entries", {})
print("stats before:", sb)
print("stats after :", sa)
print(f"findings before {len(before)} | after {len(after)}")
for k in sorted(set(after) - set(before)):
    print("  NEW      ", k, "|", after[k]["detail"], "| baselined:", k in base)
for k in sorted(set(before) - set(after)):
    print("  GONE     ", k, "|", before[k]["detail"], "| was baselined:", k in base)
for k in sorted(set(before) & set(after)):
    if before[k]["detail"] != after[k]["detail"]:
        print("  CHANGED  ", k, "|", before[k]["detail"], "->", after[k]["detail"])
red_after = [k for k in after if k not in base]
stale = sorted(k for k in base if k.startswith("csm_amort_schedule.json|") and k not in after)
print("RED after (not baselined):", red_after)
print("amort baseline lines that no longer fail (BASELINE STALE):", stale)
