# -*- coding: utf-8 -*-
"""Read-only: does the sidecar TFI flag actually predict 47/48/49 presence?

The orchestrator's new criterion assumes 47/48/49 live ONLY in the
[공통적용 경과조치] table, so TFI=X => rows legitimately absent. That assumption
must be measured, not asserted. Also checks sidecar md_path freshness on disk.

2026-08-22 validation iter-5. Modifies nothing."""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from solvency.validation.kics_json_rules import _group_records, TIER2_ITEMS  # noqa: E402

data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
records = data["records"] if isinstance(data, dict) and "records" in data else data
buckets = _group_records(records)

side = json.loads(
    (ROOT / "data/_derived/kics_transition_applicability.json").read_text(encoding="utf-8")
)
srec = {(r["code"], r["quarter"]): r for r in side["records"]}

print("=== CONTINGENCY: TFI value  x  47/48/49 presence (적용전 column) ===")
cnt = Counter()
for b in buckets:
    r = srec.get((b.code, b.quarter))
    tfi = r.get("TFI") if r else "<NO_KEY>"
    n = sum(1 for i in TIER2_ITEMS if i in b.values)
    kind = "ALL3" if n == 3 else ("NONE" if n == 0 else f"PARTIAL{n}")
    cnt[(tfi, kind)] += 1
tfis = sorted({k[0] for k in cnt})
kinds = ["ALL3", "PARTIAL1", "PARTIAL2", "NONE"]
print(f"{'TFI':12s}" + "".join(f"{k:>10s}" for k in kinds) + "     total")
for t in tfis:
    row = [cnt.get((t, k), 0) for k in kinds]
    print(f"{t:12s}" + "".join(f"{v:10d}" for v in row) + f"{sum(row):10d}")
print()

print("=== same, 적용후 column ===")
cnt = Counter()
for b in buckets:
    r = srec.get((b.code, b.quarter))
    tfi = r.get("TFI") if r else "<NO_KEY>"
    n = sum(1 for i in TIER2_ITEMS if i in b.values_post)
    kind = "ALL3" if n == 3 else ("NONE" if n == 0 else f"PARTIAL{n}")
    cnt[(tfi, kind)] += 1
for t in tfis:
    row = [cnt.get((t, k), 0) for k in kinds]
    print(f"{t:12s}" + "".join(f"{v:10d}" for v in row) + f"{sum(row):10d}")
print()

print("=== TFI=X buckets that DO carry 47/48/49 (counter-examples to the criterion) ===")
n = 0
for b in sorted(buckets, key=lambda x: (x.code, x.quarter)):
    r = srec.get((b.code, b.quarter))
    if not r or r.get("TFI") != "X":
        continue
    have = [i for i in TIER2_ITEMS if i in b.values]
    if have:
        n += 1
        vals = {i: b.values.get(i) for i in have}
        print(f"  {b.code} {b.quarter} present={have} vals={vals}")
print(f"  -> {n} counter-example buckets")
print()

print("=== TFI=NA buckets: what do they look like? ===")
for (c, q), r in sorted(srec.items()):
    if r.get("TFI") != "NA":
        continue
    b = next((x for x in buckets if x.code == c and x.quarter == q), None)
    have = [i for i in TIER2_ITEMS if b and i in b.values]
    ev = json.dumps(r.get("evidence", {}), ensure_ascii=False)[:220]
    print(f"  {c} {q} in_master={b is not None} present={have}")
    print(f"      evidence={ev}")
print()

print("=== sidecar md_path freshness on disk ===")
miss = 0
for (c, q), r in sorted(srec.items()):
    p = r.get("md_path")
    if not p:
        miss += 1
        continue
    fp = ROOT / str(p).replace("\\", "/")
    if not fp.exists():
        miss += 1
        if miss <= 15:
            print(f"  MISSING {c} {q} {p}")
print(f"  -> {miss} / {len(srec)} sidecar records whose md_path is absent on disk")
