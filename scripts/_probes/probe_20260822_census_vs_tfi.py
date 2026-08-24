# -*- coding: utf-8 -*-
"""Read-only: cross-tabulate current 47_tier2_census RED against the parser's
measured 경과조치 적용여부 sidecar (data/_derived/kics_transition_applicability.json).

2026-08-22 validation iter-5. Modifies nothing."""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from solvency.validation.kics_json_rules import run_validation  # noqa: E402

data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
records = data["records"] if isinstance(data, dict) and "records" in data else data
result = run_validation(records, tolerance=2.0)
findings = result["findings"]

side = json.loads(
    (ROOT / "data/_derived/kics_transition_applicability.json").read_text(encoding="utf-8")
)
tfi = {(r["code"], r["quarter"]): r.get("TFI") for r in side["records"]}
reason = {(r["code"], r["quarter"]): r.get("unknown_reason") for r in side["records"]}

CENSUS = {"47_tier2_census", "47_tier2_census_post"}
reds = [f for f in findings if f.get("status") == "RED" and f.get("rule") in CENSUS]
skips = [f for f in findings if f.get("status") == "SKIP" and f.get("rule") in CENSUS]

print(f"census RED total = {len(reds)}   census SKIP total = {len(skips)}")
print()

print("=== RED by (kind of detail) x TFI ===")
cnt = Counter()
for f in reds:
    code, q = f.get("원보험사코드"), f.get("공시분기")
    det = f.get("detail", "")
    tag = det.split(":")[0] if ":" in det else det[:30]
    cnt[(f["rule"], tag, tfi.get((code, q), "<NO_SIDECAR_KEY>"))] += 1
for k, v in sorted(cnt.items()):
    print(f"  {k[0]:26s} {k[1]:34s} TFI={k[2]:18s} {v}")
print()

print("=== ABSENT-flavoured RED buckets, one line each ===")
rows = []
for f in reds:
    det = f.get("detail", "")
    if "TIER2_TABLE_ABSENT" not in det:
        continue
    code, q = f.get("원보험사코드"), f.get("공시분기")
    rows.append((code, f.get("원수사명"), q, f["rule"],
                 tfi.get((code, q), "<NO_SIDECAR_KEY>")))
for r in sorted(set(rows)):
    print("  " + " | ".join(str(x) for x in r))
print()

print("=== ABSENT-flavoured SKIP buckets (COMPANYWIDE etc) ===")
rows = []
for f in skips:
    det = f.get("detail", "")
    if "TIER2_TABLE_ABSENT" not in det:
        continue
    code, q = f.get("원보험사코드"), f.get("공시분기")
    rows.append((code, f.get("원수사명"), q, f["rule"],
                 tfi.get((code, q), "<NO_SIDECAR_KEY>")))
for r in sorted(set(rows)):
    print("  " + " | ".join(str(x) for x in r))
print()

print("=== non-ABSENT census RED (present but problems) ===")
for f in sorted(reds, key=lambda x: (x["rule"], x.get("원보험사코드", ""), x.get("공시분기", ""))):
    det = f.get("detail", "")
    if "TIER2_TABLE_ABSENT" in det:
        continue
    code, q = f.get("원보험사코드"), f.get("공시분기")
    print(f"  {f['rule']} {code} {f.get('원수사명')} {q} TFI={tfi.get((code, q))}")
    print(f"      {det}")
print()

print("=== sidecar coverage vs master buckets ===")
mb = {(f.get("원보험사코드"), f.get("공시분기")) for f in findings}
missing_key = sorted(k for k in mb if k not in tfi)
print(f"master buckets={len(mb)}  sidecar records={len(tfi)}  master-buckets-with-no-sidecar-key={len(missing_key)}")
for k in missing_key[:40]:
    print("   NO_KEY", k)
print()
print("=== TFI=UNKNOWN buckets (all 24) with reason ===")
for (c, q), v in sorted(tfi.items()):
    if v == "UNKNOWN":
        print(f"  {c} {q}  reason={str(reason.get((c, q)))[:150]}")
