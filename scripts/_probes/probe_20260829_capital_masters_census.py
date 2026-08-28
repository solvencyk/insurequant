# -*- coding: utf-8 -*-
"""Read-only census for inbox/parser/20260829T0100Z (capital masters -> xlsx, phase 1 design).

Computes, from the live root JSONs (no mutation):
  1. tier1/tier2 utilization_pct outlier census (which companies fall outside [0,100]).
  2. forward_capital.json status / bond_coverage / confidence.level distribution.
  3. call_source census on data/bonds/capital_securities_fy2025.json, joined to which
     insurer codes actually carry a non-"disclosed" (call-option-not-in-filing) bond
     that is `outstanding` (i.e. actually feeds the forward simulation's deduction list,
     per forward_capital_simulation.py::load_outstanding_bonds -- only bonds with a
     truthy outstanding_mn are included).

Read-only. No file writes. Run with the venv python.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]


def load(name):
    return json.loads((REPO / name).read_text(encoding="utf-8"))


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ---------------------------------------------------------------- tier1/tier2
t1 = load("kics_tier1_utilization.json")
t2 = load("kics_tier2_utilization.json")

section("TIER1 utilization_pct outliers (outside [0,100])")
t1_rows = t1["results"]
print(f"count field={t1['count']}  len(results)={len(t1_rows)}")
t1_out = [r for r in t1_rows if not (0.0 <= (r.get("utilization_pct") or 0) <= 100.0)]
print(f"outliers (utilization_pct, primary SCRx15% limit): {len(t1_out)}")
for r in sorted(t1_out, key=lambda r: -r["utilization_pct"]):
    print(f"  {r['company']:16s} {r['code']}  utilization_pct={r['utilization_pct']:>8.1f}  "
          f"strict={r['utilization_pct_strict']:>8.1f}  quality_flag={r['quality_flag']}")

t1_strict_out = [r for r in t1_rows if not (0.0 <= (r.get("utilization_pct_strict") or 0) <= 100.0)]
print(f"\noutliers (utilization_pct_strict, SCRx10% limit): {len(t1_strict_out)}")

qf1 = {}
for r in t1_rows:
    qf1[r.get("quality_flag")] = qf1.get(r.get("quality_flag"), 0) + 1
print(f"tier1 quality_flag distribution: {qf1}")
isrc1 = {}
for r in t1_rows:
    isrc1[r.get("issued_source")] = isrc1.get(r.get("issued_source"), 0) + 1
print(f"tier1 issued_source distribution: {isrc1}")

section("TIER2 utilization_pct outliers (outside [0,100]) -- the '4개사' the ticket refers to")
t2_rows = t2["results"]
print(f"count field={t2['count']}  len(results)={len(t2_rows)}")
t2_out = [r for r in t2_rows if not (0.0 <= (r.get("utilization_pct") or 0) <= 100.0)]
print(f"outliers (utilization_pct, primary numerator/SCRx50%): {len(t2_out)}")
for r in sorted(t2_out, key=lambda r: -r["utilization_pct"]):
    print(f"  {r['company']:16s} {r['code']}  utilization_pct={r['utilization_pct']:>8.1f}  "
          f"numerator_eok={r['numerator_eok']:>10.1f}  tier2_limit_eok={r['tier2_limit_eok']:>10.1f}  "
          f"quality_flag={r['quality_flag']}")

print("\n(sanity) all tier2 utilization_pct sorted desc, top 8:")
for r in sorted(t2_rows, key=lambda r: -(r.get("utilization_pct") or 0))[:8]:
    print(f"  {r['company']:16s} {r['code']}  utilization_pct={r['utilization_pct']:>8.1f}")

qf2 = {}
for r in t2_rows:
    qf2[r.get("quality_flag")] = qf2.get(r.get("quality_flag"), 0) + 1
print(f"\ntier2 quality_flag distribution: {qf2}")

proxy_hi = [r for r in t2_rows if (r.get("proxy_utilization_pct") or 0) > 100]
print(f"tier2 proxy_utilization_pct > 100: {len(proxy_hi)} "
      f"(this is the OLD broken-proxy metric the definition.replaces note warns about -- "
      f"kept in the JSON for reference, not the headline number)")

# ---------------------------------------------------------------- forward_capital
section("FORWARD_CAPITAL status / bond_coverage / confidence census")
fc = load("kics_forward_capital.json")
print(f"type={type(fc).__name__}  len={len(fc)}")

status_dist = {}
cov_dist = {}
conf_dist = {}
years_seen = set()
proj_key_sets = set()
for r in fc:
    status_dist[r.get("status")] = status_dist.get(r.get("status"), 0) + 1
    cov_dist[r.get("bond_coverage")] = cov_dist.get(r.get("bond_coverage"), 0) + 1
    conf = r.get("confidence") or {}
    conf_dist[conf.get("level")] = conf_dist.get(conf.get("level"), 0) + 1
    for p in r.get("projections", []):
        years_seen.add(p.get("year"))
        proj_key_sets.add(tuple(sorted(p.keys())))

print(f"status distribution: {status_dist}")
print(f"bond_coverage distribution: {cov_dist}")
print(f"confidence.level distribution: {conf_dist}")
print(f"years across all projections: {sorted(years_seen)}")
print(f"distinct projection-dict key sets: {len(proj_key_sets)}")
for ks in proj_key_sets:
    print(f"  {ks}")

top_keys = set()
baseline_keys = set()
confidence_keys = set()
for r in fc:
    top_keys.update(r.keys())
    baseline_keys.update((r.get("baseline") or {}).keys())
    confidence_keys.update((r.get("confidence") or {}).keys())
print(f"\ntop-level keys across all rows: {sorted(top_keys)}")
print(f"baseline dict keys: {sorted(baseline_keys)}")
print(f"confidence dict keys: {sorted(confidence_keys)}")

not_ok = [r for r in fc if r.get("status") != "ok"]
print(f"\nrows with status != 'ok': {len(not_ok)}")
for r in not_ok:
    print(f"  {r['insurer_code']} {r['insurer_name']}  status={r.get('status')}")

low_conf = [r for r in fc if (r.get("confidence") or {}).get("level") == "low"]
print(f"\nrows with confidence.level == 'low': {len(low_conf)}")
for r in low_conf:
    print(f"  {r['insurer_code']} {r['insurer_name']}")

# ---------------------------------------------------------------- bond call_source census
section("BONDS call_source census (data/bonds/capital_securities_fy2025.json)")
bonds_doc = load("data/bonds/capital_securities_fy2025.json")
print(f"n_companies={bonds_doc.get('n_companies')}  as_of={bonds_doc.get('as_of')}")

total_bonds = 0
src_dist = {}
per_company_nondisclosed_outstanding = {}
for c in bonds_doc["companies"]:
    code = c["code"]
    name = c["company"]
    for b in c.get("bonds", []):
        total_bonds += 1
        src = b.get("call_source")
        src_dist[src] = src_dist.get(src, 0) + 1
        outstanding = bool(b.get("outstanding_mn"))
        if src != "disclosed" and outstanding:
            per_company_nondisclosed_outstanding.setdefault((code, name), []).append(
                (b.get("name"), src, b.get("outstanding_mn"))
            )

print(f"total bonds={total_bonds}")
print(f"call_source distribution: {src_dist}")

print(f"\ncompanies with >=1 OUTSTANDING bond whose call_source != 'disclosed' "
      f"(these actually feed forward_capital_simulation's call-date deduction with a "
      f"derived/estimated call date, not a filed one): "
      f"{len(per_company_nondisclosed_outstanding)}")
for (code, name), bonds in sorted(per_company_nondisclosed_outstanding.items()):
    print(f"  {name:16s} {code}  bonds affected={len(bonds)}")
    for bname, src, out_mn in bonds:
        print(f"      {src:55s} outstanding_mn={out_mn:>10}  {bname}")

# cross-check: are any bonds missing call_date outright (the literal `or legal_maturity`
# fallback in forward_capital_simulation.py L150)?
missing_call_date = 0
for c in bonds_doc["companies"]:
    for b in c.get("bonds", []):
        if not b.get("call_date"):
            missing_call_date += 1
print(f"\nbonds with call_date falsy/missing (literal code-level fallback to legal_maturity): "
      f"{missing_call_date}")

print("\nDONE")
