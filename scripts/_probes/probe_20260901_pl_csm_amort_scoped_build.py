"""Scoped rebuild for the PL_CSM_AMORT_VS_WATERFALL RED-7 fix (inbox/parser/20260901T1900Z).

Re-parses ONLY KR0050 (하나손해보험) and KR0076 (아이엠라이프생명보험) via
discover_filings/parse_filing/assemble (mirrors build_pl_breakdown.main()'s per-company
body verbatim, restricted to these 2 codes) and UNION-MERGES the resulting rows into
data/dart/viz/pl_breakdown_master.json + data/_derived/pl_breakdown_coverage.json by
company key -- every other company's rows pass through untouched. This is the "call the
individual builder company-scoped" path CLAUDE.md requires instead of
build_root_masters.main() / build_pl_breakdown.main() (both destructive on this branch).

Does NOT touch CSM_waterfall.json, oci32 provenance, or intentional_nulls -- this ticket
only adds item4 (원수CSM상각) for these 2 companies via 2 new note-table readers in
scripts/pl_breakdown/companies.py (_hana_sonbo_csm_amort / _imelife_csm_amort); nothing
else in their per-company handlers changed, so those 2 companies' other outputs (items
25-32 OCI, extra_items) are expected to be byte-identical to what's already committed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from scripts.build_pl_breakdown import (  # noqa: E402
    _GOLD_CELL_OVERRIDE,
    ITEM_NAMES,
    OCI_ITEMS,
    ZERO_FILL_ITEMS,
    _fs_tier1,
    _quarter_sort_key,
    _xmls_in,
    assemble,
    discover_filings,
    load_universe,
    parse_filing,
)

TARGET_CODES = {"KR0050", "KR0076"}

MASTER_PATH = ROOT / "data" / "dart" / "viz" / "pl_breakdown_master.json"
COV_PATH = ROOT / "data" / "_derived" / "pl_breakdown_coverage.json"


def build_scoped():
    uni = load_universe()
    filings = discover_filings()
    rows = []
    coverage = []

    for code in sorted(c for c in filings if c in TARGET_CODES):
        name, life_flag = uni.get(code, (None, None))
        if name is None:
            name = code
        is_life = (life_flag == "생명보험")
        parsed = {}
        for q in sorted(filings[code], key=_quarter_sort_key):
            dirs = filings[code][q]
            has_xml = any(_xmls_in(d) for d in dirs)
            t1_html, t2 = parse_filing(dirs, is_life, code=code, name=name, quarter=q)
            t1_api = _fs_tier1(name, q, code)
            t1 = t1_api if t1_api else t1_html
            parsed[q] = (t1, t2, has_xml)
        ever_extracted = set()
        for q, (t1, t2, _hx) in parsed.items():
            if t1 is None and t2 is None:
                continue
            probe = assemble(t1, t2, is_life, zero_fill_ok=frozenset())
            for _n in ZERO_FILL_ITEMS:
                if probe[_n] is not None:
                    ever_extracted.add(_n)
        zero_fill_ok = ZERO_FILL_ITEMS - ever_extracted

        for q in sorted(parsed, key=_quarter_sort_key):
            t1, t2, has_xml = parsed[q]
            if t1 is None and t2 is None:
                st = "no_income_statement" if has_xml else "raw_not_extracted"
                coverage.append((code, name, q, st, list(range(1, 25)), "none"))
                continue
            v = assemble(t1, t2, is_life, zero_fill_ok=zero_fill_ok)
            ov = _GOLD_CELL_OVERRIDE.get((code, q))
            if ov:
                for _k, _val in ov.items():
                    v[_k] = _val
                v["_reconciled"] = True
            for n in range(1, 25):
                rows.append({
                    "원보험사코드": code, "원수사명": name, "티커": None,
                    "생손보여부": life_flag, "항목번호": n, "항목명": ITEM_NAMES[n],
                    "공시분기": q,
                    "값": (round(v[n], 6) if isinstance(v[n], float) else v[n]),
                })
            for n in OCI_ITEMS:
                val = v.get(n)
                rows.append({
                    "원보험사코드": code, "원수사명": name, "티커": None,
                    "생손보여부": life_flag, "항목번호": n, "항목명": ITEM_NAMES[n],
                    "공시분기": q,
                    "값": (round(val, 6) if isinstance(val, float) else val),
                })
            if v.get("_reconciled") is not False:
                for ex in (v.get("_extra_items") or []):
                    val = ex["값"]
                    rows.append({
                        "원보험사코드": code, "원수사명": name, "티커": None,
                        "생손보여부": life_flag, "항목번호": ex["항목번호"],
                        "항목명": ex["항목명"], "공시분기": q,
                        "값": (round(val, 6) if isinstance(val, float) else val),
                    })
            missing = [n for n in range(1, 25) if v[n] is None]
            if not missing:
                status = "ok"
            elif t1 is not None:
                status = "partial"
            else:
                status = "no_income_statement"
            rec = v.get("_reconciled")
            t2_status = ("suppressed" if rec is False
                         else "ok" if rec is True
                         else "none" if not t2 else "partial")
            coverage.append((code, name, q, status, missing, t2_status))

    return rows, coverage


def merge_master(fresh_rows):
    existing = json.loads(MASTER_PATH.read_text(encoding="utf-8"))
    kept = [r for r in existing if r["원보험사코드"] not in TARGET_CODES]
    dropped = len(existing) - len(kept)
    merged = kept + fresh_rows
    print(f"master: existing={len(existing)} kept(other companies)={len(kept)} "
          f"dropped(target companies, replaced)={dropped} fresh={len(fresh_rows)} "
          f"final={len(merged)}")
    MASTER_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")


def merge_coverage(fresh_coverage):
    existing = json.loads(COV_PATH.read_text(encoding="utf-8"))
    kept = [r for r in existing if r["code"] not in TARGET_CODES]
    dropped = len(existing) - len(kept)
    fresh = [{"code": c, "name": n, "quarter": q, "status": s, "missing": m, "tier2": t2s}
             for c, n, q, s, m, t2s in fresh_coverage]
    merged = kept + fresh
    print(f"coverage: existing={len(existing)} kept={len(kept)} dropped={dropped} "
          f"fresh={len(fresh)} final={len(merged)}")
    COV_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    rows, coverage = build_scoped()
    print(f"scoped parse: {len(rows)} rows, "
          f"{len({(r['원보험사코드'], r['공시분기']) for r in rows})} company-quarters, "
          f"companies={sorted({r['원보험사코드'] for r in rows})}")
    merge_master(rows)
    merge_coverage(coverage)
