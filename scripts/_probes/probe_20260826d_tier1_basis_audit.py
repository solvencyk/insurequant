"""Tier-1 (FS-API) basis audit: BASIS_CFS is now empty (46th pass), so tier1_for() always
tries OFS(별도) first. This confirms, for every (company, quarter) currently on the FS-API
path, whether the OFS fetch actually SUCCEEDS (t1 truthy) -- vs silently falling through to
CFS because OFS returned nothing (status != 000 / no income-statement account tags), which
would be an invisible consolidated-basis leak in Tier-1 the census above cannot see (it only
tested Tier-2 dedicated handlers). Offline: reads data/dart/_fs_api_cache/ only, no network.
"""
import json, sys, io
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import scripts.build_pl_breakdown as B
from scripts.fetch_dart_fs import resolve_corp, REPRT, _fetch_raw, _parse

uni = B.load_universe()
filings = B.discover_filings()

out = io.open("scripts/_probes/out_20260826d_tier1_basis.txt", "w", encoding="utf-8")
n_ofs_ok = n_ofs_fail_cfs_used = n_both_fail = 0
cfs_used_rows = []
for code in sorted(filings):
    name, life_flag = uni.get(code, (None, None))
    if name is None:
        continue
    cc = resolve_corp(name)
    if not cc:
        out.write(f"{code} {name}: resolve_corp FAILED\n")
        continue
    for q in sorted(filings[code], key=B._quarter_sort_key):
        reprt = REPRT.get(q[5:])
        if not reprt:
            continue
        year, annual = q[:4], (q[5:] == "4Q")
        try:
            t1_ofs = _parse(_fetch_raw(cc, year, reprt, "OFS"), annual)
        except Exception:
            t1_ofs = None
        if t1_ofs:
            n_ofs_ok += 1
            continue
        try:
            t1_cfs = _parse(_fetch_raw(cc, year, reprt, "CFS"), annual)
        except Exception:
            t1_cfs = None
        if t1_cfs:
            n_ofs_fail_cfs_used += 1
            cfs_used_rows.append((code, name, q))
        else:
            n_both_fail += 1

out.write(f"OFS succeeded: {n_ofs_ok}\n")
out.write(f"OFS failed, CFS fallback used (basis leak in Tier-1): {n_ofs_fail_cfs_used}\n")
out.write(f"both failed (no FS-API tier1 at all -> HTML fallback in real pipeline): {n_both_fail}\n\n")
out.write("=== rows where CFS fallback fired (Tier-1 currently CONSOLIDATED) ===\n")
for code, name, q in cfs_used_rows:
    out.write(f"{code}\t{name}\t{q}\n")
out.close()
print("done", n_ofs_ok, n_ofs_fail_cfs_used, n_both_fail)
