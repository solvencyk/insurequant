"""Surgical patch: add item32 (기타 포괄손익(미분류)) rows to data/dart/viz/pl_breakdown_master.json
WITHOUT re-running build_pl_breakdown.py::main() (raw XML is partially git-purged on this
branch -- a full rediscover-from-raw rebuild risks collapsing company/quarter coverage, per
CLAUDE.md / SKILL.md "destructive rebuild" warning).

For every (code, quarter) already present in the master, calls fetch_dart_fs.tier1_for()
(pure FS-API-cache read, no raw XML, no network -- same call build_pl_breakdown.py::main()
would make) to get item32 (+ provenance), and appends ONE new row per (code, quarter) that
has item25 in the master already -- an explicit null row when item32 can't be computed
(source gap, e.g. 삼성화재), matching the existing items-25-31 convention
("SKIP-on-missing is forbidden").

Does not touch any existing row (items 1-31 untouched, byte-for-byte).  Backs up the master
first.  Also writes the item32 provenance file (same shape build_pl_breakdown.py::main() now
writes, so a future full rebuild's output matches this patch's)."""
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.build_pl_breakdown import ITEM_NAMES  # noqa: E402
from scripts.fetch_dart_fs import resolve_corp, tier1_for  # noqa: E402

MASTER = Path("data/dart/viz/pl_breakdown_master.json")
PROV = Path("data/_derived/pl_oci_item32_provenance.json")

rows = json.loads(MASTER.read_text(encoding="utf-8"))
backup = MASTER.with_name(MASTER.name + f".bak_{datetime.now():%Y%m%d}_item32")
if not backup.exists():
    shutil.copy2(MASTER, backup)
    print(f"backup -> {backup}")
else:
    print(f"backup already exists, not overwriting -> {backup}")

by_cq = defaultdict(dict)
meta_by_cq = {}
for r in rows:
    key = (r["원보험사코드"], r["공시분기"])
    by_cq[key][r["항목번호"]] = r
    meta_by_cq[key] = r  # any row carries 원수사명/티커/생손보여부

targets = [(code, q) for (code, q), items in by_cq.items() if 25 in items]
print(f"candidate (code,quarter) with item25 row present: {len(targets)}")
if any(32 in by_cq[k] for k in targets):
    already = [k for k in targets if 32 in by_cq[k]]
    print(f"ABORT: item32 rows already exist for {len(already)} cells: {already[:5]}...")
    sys.exit(1)

new_rows = []
oci32_prov = []
n_value = n_null = n_no_corp = n_no_t1 = 0
for code, q in sorted(targets):
    meta = meta_by_cq[(code, q)]
    name, ticker, life = meta["원수사명"], meta["티커"], meta["생손보여부"]
    cc = resolve_corp(name)
    if not cc:
        n_no_corp += 1
        v32, prov32 = None, None
    else:
        t1 = tier1_for(name, q, code)
        if not t1:
            n_no_t1 += 1
            v32, prov32 = None, None
        else:
            v32, prov32 = t1.get(32), t1.get("_oci32_src")
    new_rows.append({
        "원보험사코드": code, "원수사명": name, "티커": ticker,
        "생손보여부": life, "항목번호": 32, "항목명": ITEM_NAMES[32],
        "공시분기": q,
        "값": (round(v32, 6) if isinstance(v32, float) else v32),
    })
    if v32 is not None:
        n_value += 1
    else:
        n_null += 1
    if prov32:
        oci32_prov.append({"원보험사코드": code, "원수사명": name, "공시분기": q, "구성": prov32})

print(f"new item32 rows: {len(new_rows)}  (value={n_value} null={n_null} "
      f"no_corp={n_no_corp} no_t1={n_no_t1})")

merged = rows + new_rows
MASTER.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"wrote {MASTER}: {len(rows)} -> {len(merged)} rows (+{len(new_rows)})")

PROV.parent.mkdir(parents=True, exist_ok=True)
PROV.write_text(json.dumps(oci32_prov, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"item32 provenance: {len(oci32_prov)} company-quarters -> {PROV}")
