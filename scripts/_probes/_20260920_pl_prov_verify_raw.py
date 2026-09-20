#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify the 92 income_statement cells that fall back to raw-HTML Tier-1 (no FS-API cache),
by running the PRODUCTION extract_tier1() over each rcept dir's XML and comparing to the
master.  Also verifies, for the multi-rcept (code,quarter) groups, WHICH dir carries the
income statement.  Offline; reads raw XML only, writes one probe JSON."""
import glob
import io
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis  # noqa: E402
from scripts.pl_breakdown.tier1 import extract_tier1  # noqa: E402

T1_DIRECT = (1, 16, 17, 20, 22, 23, 24)


def _xmls_in(d):
    xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
    return sorted(set(xs), key=os.path.getsize, reverse=True)


def tier1_of(d, code):
    tables = []
    for x in _xmls_in(d):
        try:
            tables.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
        except Exception:
            pass
    if not tables:
        return None
    try:
        return extract_tier1(tables, code=code)
    except Exception:
        return None


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    res = json.loads((ROOT / "data/_derived/_probe_20260920_pl_prov_resolve.json")
                     .read_text(encoding="utf-8"))
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    vals = {}
    for r in rows:
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        vals.setdefault((r.get("원보험사코드"), r.get("공시분기")), {})[it] = r.get("값")

    targets = [e for e in res
               if e["item_block"] == "income_statement"
               and (e.get("resolution") == "RAW_HTML_NO_FS_CACHE"
                    or len(e.get("raw_dirs_with_xml") or []) > 1)]
    if only:
        targets = [e for e in targets if e["quarter"] == only]
    print(f"targets = {len(targets)}")

    out, stat = [], Counter()
    t0 = time.time()
    for i, e in enumerate(targets, 1):
        code, q = e["company_code"], e["quarter"]
        mv = vals.get((code, q), {})
        per_dir = []
        for d in e["raw_dirs_with_xml"]:
            t1 = tier1_of(d, code)
            hit = miss = 0
            if t1:
                for it in T1_DIRECT:
                    a, b = mv.get(it), t1.get(it)
                    if a is None or b is None:
                        continue
                    if abs(a - b) <= max(1.0, abs(a) * 1e-4):
                        hit += 1
                    else:
                        miss += 1
            per_dir.append({"dir": d, "t1_found": bool(t1),
                            "t1_items": sorted(k for k in (t1 or {}) if isinstance(k, int)),
                            "hit": hit, "miss": miss})
        best = max(per_dir, key=lambda p: (p["hit"], -p["miss"]), default=None)
        verdict = ("RAW_TIER1_CONFIRMED" if best and best["hit"] else
                   "RAW_TIER1_PRESENT_NO_MATCH" if best and best["t1_found"] else
                   "RAW_TIER1_ABSENT")
        stat[verdict] += 1
        out.append({"company_code": code, "quarter": q,
                    "resolution": e.get("resolution"), "verdict": verdict,
                    "best_dir": best["dir"] if best else None,
                    "best_hit": best["hit"] if best else 0,
                    "best_miss": best["miss"] if best else 0,
                    "n_nonnull": e["n_nonnull"], "per_dir": per_dir})
        print(f"[{i}/{len(targets)}] {code} {q} {verdict} hit={best['hit'] if best else 0} "
              f"miss={best['miss'] if best else 0} ({time.time()-t0:.0f}s)", flush=True)

    print("\nverdicts:", dict(stat))
    dst = ROOT / f"data/_derived/_probe_20260920_pl_prov_verify_raw{'_'+only if only else ''}.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {dst.relative_to(ROOT)}")


main()
