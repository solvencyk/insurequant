#!/usr/bin/env python3
"""Census: which quarters exist in each master vs which quarters each gate actually scans.

Read-only probe. No master mutation.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

MASTERS = [
    "PL_breakdown.json",
    "CSM_waterfall.json",
    "IFRS17_BS.json",
    "kics_disclosure.json",
    "data/dart/viz/pl_breakdown_master.json",
    "data/dart/viz/csm_waterfall_master_diag.json",
    "sensitivity_heatmap.json",
    "CSM_amortization.json",
    "dividend.json",
]

print("=" * 78)
print("A. 마스터별 실제 분기 분포")
print("=" * 78)
for p in MASTERS:
    fp = ROOT / p
    if not fp.exists():
        print(f"  {p:48s} (없음)")
        continue
    try:
        d = json.loads(fp.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"  {p:48s} READ FAIL {e}")
        continue
    if isinstance(d, dict):
        rows = d.get("records") or d.get("rows") or d.get("data")
        if rows is None:
            print(f"  {p:48s} dict keys={list(d)[:6]}")
            continue
    else:
        rows = d
    qk = None
    for cand in ("공시분기", "quarter", "분기"):
        if rows and cand in rows[0]:
            qk = cand
            break
    if qk is None:
        print(f"  {p:48s} no quarter key; keys={list(rows[0])[:8] if rows else '?'}")
        continue
    c = Counter(r.get(qk) for r in rows)
    qs = sorted(c)
    print(f"  {p:48s} rows={len(rows):6d} quarters={qs[0]}..{qs[-1]} (n={len(qs)})")
    tail = [q for q in qs if q >= "2025.4Q"]
    print(f"      tail: " + ", ".join(f"{q}={c[q]}" for q in tail))

print()
print("=" * 78)
print("B. scripts/ 안의 분기 리터럴 census (하드코딩 탐지)")
print("=" * 78)
QPAT = re.compile(r"\b20\d\d\.[1-4]Q\b")
hits: dict[str, list[tuple[int, str, list[str]]]] = defaultdict(list)
for f in sorted((ROOT / "scripts").rglob("*.py")):
    if "_probes" in f.parts or "archive" in f.parts:
        continue
    try:
        txt = f.read_text(encoding="utf-8")
    except Exception:
        continue
    for i, line in enumerate(txt.splitlines(), 1):
        found = QPAT.findall(line)
        if found:
            hits[str(f.relative_to(ROOT)).replace("\\", "/")].append((i, line.strip()[:150], found))

for f, rows in sorted(hits.items()):
    maxq = max(q for _, _, qs in rows for q in qs)
    print(f"\n--- {f}   (최대 분기 리터럴 = {maxq}, {len(rows)}줄)")
    for i, line, found in rows:
        print(f"    L{i:<5d} {line}")
