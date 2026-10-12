"""s9c_consolidate.py -- step 9c (READ-ONLY on the repo).  Folds the ~650 small per-filing core-table caches (cache/core_<period>_<code>.json) into ONE file
core_extract_all.json (the raw evidence behind every 'latest' value: pdf, pages, the three printed columns) so the per-filing cache folder need not be kept.
usage: s9c_consolidate.py            -> writes core_extract_all.json
       (s1_core_extract.py --force re-creates the per-filing caches from the PDFs in about 4 minutes)
"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402

utf8_stdout()
out = {}
for f in sorted(CACHE.glob("core_*.json")):
    d = read_json(f)
    key = f"{d['period']}|{d['code']}"
    slim = {k: d.get(k) for k in ("status", "pdf", "pages", "method", "layout", "err", "gapfill_items", "unmatched")}
    slim["cols"] = {c: {it: v for it, v in cols.items()} for c, cols in (d.get("cols") or {}).items()}
    out[key] = {k: v for k, v in slim.items() if v not in (None, [], {})}
write_json_lf(OUT / "core_extract_all.json", out, indent=None)
print("filings:", len(out), "bytes:", (OUT / "core_extract_all.json").stat().st_size)
