#!/usr/bin/env python3
"""2026-08-26 (47th pass) -- follow-up to probe_20260826_pl_basis_audit_40.py.

That probe only tested companies with a DEDICATED Tier-2 handler (SONBO_HANDLERS /
LIFE_HANDLERS). Companies that fall through to the GENERIC fallback cascade (no dedicated
handler at all -- KR0029/KR0051/KR0150 sonbo; KR0068/KR0074/KR0075/KR0076/KR0095/KR1010/
KR1011 life) were skipped entirely. Some of them (KR0029 AIG, KR0150 서울보증, KR0068
한화생명, KR0074/KR0095/KR1010 in their 2025.4Q filing) DO show real CFS-tagged tables in
the basis census, so the generic cascade's OFS-safety needs its own check -- it is not
automatically covered by the dedicated-handler test.

Method: replicate parse_filing()'s full body (tier1 + the ENTIRE life/sonbo fallback
cascade, verbatim) but apply _prefer_ofs(tables) ONCE at the top, before ANY handler in the
cascade runs -- this is the correct generalisation of the "prefer OFS pool globally, natural
cascade still applies on top" pattern already used for the 4 functions the 46th pass fixed
directly.  Falls back to reporting "no signal" (not a claim) when the OFS-only pool leaves
the whole cascade's key items empty.  Read-only; writes only to scripts/_probes/.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _quarter_sort_key  # noqa: E402
from scripts.pl_breakdown.tier1 import extract_tier1  # noqa: E402
from scripts.pl_breakdown.tier2 import (  # noqa: E402
    extract_tier2_life,
    extract_tier2_sonbo,
    extract_tier2_sonbo_structured,
)
from scripts.pl_breakdown.companies import (  # noqa: E402
    LIFE_HANDLERS,
    SONBO_HANDLERS,
    extract_tier2_aia,
    extract_tier2_kb,
    extract_tier2_life_comprehensive,
    extract_tier2_life_old,
    extract_tier2_old,
    extract_tier2_sonbo_component,
)
import scripts.build_pl_breakdown as B  # noqa: E402

TARGET_CODES_SONBO = {"KR0029", "KR0051", "KR0150"}
TARGET_CODES_LIFE = {"KR0068", "KR0074", "KR0075", "KR0076", "KR0095", "KR1010", "KR1011"}


def _cascade(tables, is_life, code, name, quarter):
    """Verbatim copy of parse_filing()'s dispatch body (build_pl_breakdown.py L313-363),
    operating on whatever `tables` is handed in (may already be OFS-preferred)."""
    t1 = extract_tier1(tables, code=code)
    if is_life:
        handler = LIFE_HANDLERS.get(code)
        if handler is extract_tier2_life_comprehensive:
            t2 = handler(tables, code=code)
        elif handler is extract_tier2_aia:
            t2 = None  # prose-only, table-basis filtering meaningless -- excluded
        else:
            t2 = handler(tables) if handler else {}
        if not t2 or all((t2 or {}).get(i) is None for i in (4, 5)):
            t2o = extract_tier2_life_old(tables)
            if t2o and t2o.get(4):
                t2 = {**(t2 or {}), **t2o}
            else:
                t2g = extract_tier2_life(tables)
                if t2g:
                    t2 = {**(t2 or {}), **t2g}
    else:
        handler = SONBO_HANDLERS.get(code)
        if handler is extract_tier2_kb:
            _api = B._fs_tier1(name, quarter, code)
            _i1 = (_api or {}).get(1) if _api else (t1 or {}).get(1)
            t2 = handler(tables, item1=_i1)
        else:
            t2 = handler(tables) if handler else {}
        if not t2 or all((t2 or {}).get(i) is None for i in (4, 5, 6)):
            t2c = extract_tier2_sonbo_component(tables)
            if t2c and any(t2c.get(i) is not None for i in (4, 5, 6)):
                t2 = {**(t2 or {}), **t2c}
            else:
                t2o = extract_tier2_old(tables)
                if t2o and any(t2o.get(i) is not None for i in (4, 5, 6)):
                    t2 = {**(t2 or {}), **t2o}
                else:
                    t2a = extract_tier2_sonbo(tables)
                    if t2a and any(t2a.get(i) is not None for i in (4, 5, 6)):
                        t2 = {**(t2 or {}), **t2a}
                    else:
                        t2b = extract_tier2_sonbo_structured(tables)
                        if t2b:
                            t2 = {**(t2 or {}), **t2b}
    return t1, (t2 or None)


def main():
    uni = B.load_universe()
    filings = B.discover_filings()
    targets = TARGET_CODES_SONBO | TARGET_CODES_LIFE

    results = []
    for code in sorted(targets):
        if code not in filings:
            continue
        name, life_flag = uni.get(code, (None, None))
        if name is None:
            continue
        is_life = (life_flag == "생명보험")
        for q in sorted(filings[code], key=_quarter_sort_key):
            dirs = filings[code][q]
            tables = []
            for d in dirs:
                for x in B._xmls_in(d):
                    try:
                        tables.extend(_tag_basis(list(_iter_tables_with_context(Path(x))), x))
                    except Exception:
                        pass
            if not tables:
                continue
            # (a) current -- the REAL unmodified dispatch (identical to live master)
            t1_cur, t2_cur = B.parse_filing(dirs, is_life, code=code, name=name, quarter=q)
            # (b) OFS-preferred at the top, natural cascade on top of that pool
            tables_ofs = _prefer_ofs(tables)
            t1_ofs, t2_ofs = _cascade(tables_ofs, is_life, code, name, q)
            key_items = (4, 5) if is_life else (4, 5, 6)
            struct_fail = (not t2_ofs) or all(t2_ofs.get(i) is None for i in key_items)
            diffs = {}
            if not struct_fail and t2_cur:
                for k, v_ofs in t2_ofs.items():
                    if not isinstance(k, int):
                        continue
                    v_cur = t2_cur.get(k)
                    if v_ofs is None or v_cur is None:
                        continue
                    try:
                        if abs(float(v_ofs) - float(v_cur)) > 0.05:
                            diffs[k] = {"current": v_cur, "ofs_preferred": v_ofs}
                    except (TypeError, ValueError):
                        pass
            results.append({
                "code": code, "name": name, "quarter": q,
                "t2_current": t2_cur, "t2_ofs_preferred": (None if struct_fail else t2_ofs),
                "struct_fail": struct_fail, "diffs": diffs,
            })

    out_path = Path("scripts/_probes/out_20260826g_generic_fallback_census.json")
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"total rows: {len(results)}")
    flagged = [r for r in results if r["diffs"]]
    print(f"flagged (diff found): {len(flagged)}")
    for r in flagged:
        print(f"  {r['code']} {r['name']} {r['quarter']}: {r['diffs']}")
    print(f"structural fail (no signal): {sum(1 for r in results if r['struct_fail'])}")


if __name__ == "__main__":
    main()
