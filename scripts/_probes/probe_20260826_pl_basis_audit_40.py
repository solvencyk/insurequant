#!/usr/bin/env python3
"""2026-08-26 (47th pass) -- PL bases census over the remaining ~40 companies not yet
audited by the 46th pass (KR0001/KR0069/KR0094 fixed; KR0068/KR0071/KR0072/KR0083/KR0104
spot-confirmed unchanged at 2025.4Q only).

Read-only diagnostic.  Does NOT write to PL_breakdown.json or any pl_breakdown/* module.

Method (mirrors the safe pattern already proven in the 46th pass for the 4 shared Tier-2
functions): for every (company, quarter) filing with a DEDICATED Tier-2 handler
(SONBO_HANDLERS / LIFE_HANDLERS in scripts/pl_breakdown/companies.py), call the handler
twice --
  (a) t2_current = the REAL parse_filing() dispatch, unmodified -- this is exactly what is
      in the live PL_breakdown.json today (mod later _GOLD_CELL_OVERRIDE cells, which are
      cross-checked separately).
  (b) t2_ofs = the SAME dedicated handler, but called on _prefer_ofs(tables) first; if that
      leaves the handler's key items (4,5 for 생보 / 4,5,6 for 손보) all None -- i.e. the
      OFS-only pool was too thin for THIS handler's caption/shape matching, a structural
      artifact, not a basis signal -- t2_ofs is None (no claim made).
A non-null t2_ofs that DIFFERS from t2_current on some item n is the diagnostic signal:
"this dedicated handler is picking a 연결(CFS)-tagged table over an available, different
별도(OFS)-tagged alternative."  It is not by itself proof OFS is correct -- basis tagging
itself (common.py::_tag_basis) is heuristic (ATOC line-position split) -- so every flagged
(code, quarter, item) still needs the cross-check methods (XBRL ACONTEXT tag / summary
income-statement multi-year table) before being treated as a fix.

Also separately audits Tier-1: confirms BASIS_CFS is empty (global fix already applied) and
that the FS-API primary fetch (OFS) actually SUCCEEDS for every company/quarter currently
using it (a silent CFS same-quarter fallback, per fetch_dart_fs.py's own fallback comment,
would be invisible in the master otherwise).

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260826_pl_basis_audit_40.py
Writes scripts/_probes/out_20260826_pl_basis_census.json (full census) and prints a summary.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _quarter_sort_key  # noqa: E402
from scripts.pl_breakdown.companies import (  # noqa: E402
    LIFE_HANDLERS,
    SONBO_HANDLERS,
    extract_tier2_aia,
)
import scripts.build_pl_breakdown as B  # noqa: E402

ALREADY_AUDITED = {"KR0001", "KR0069", "KR0094"}  # 46th pass: fixed via general code paths
SPOT_CONFIRMED_2025Q4_ONLY = {"KR0068", "KR0071", "KR0072", "KR0083", "KR0104"}  # 46th pass


def _xmls_in(d):
    return B._xmls_in(d)


def _collect_tables(dirs):
    tables = []
    for d in dirs:
        for x in _xmls_in(d):
            try:
                tables.extend(_tag_basis(list(_iter_tables_with_context(Path(x))), x))
            except Exception:
                pass
    return tables


def _call_dedicated(handler, tables, is_life, name, quarter, code):
    """Call ONLY the dedicated handler (no fallback chain) -- mirrors the first branch of
    build_pl_breakdown.py::parse_filing for codes with a registered handler."""
    if handler is None:
        return None
    if is_life:
        if handler is B.extract_tier2_life_comprehensive:
            return handler(tables, code=code)
        if handler is extract_tier2_aia:
            return None  # AIA is prose-only (reads dirs text directly, ignores `tables`) --
            # table-basis filtering is meaningless for it; excluded from this diagnostic.
        return handler(tables)
    else:
        if handler is B.extract_tier2_kb:
            _api = B._fs_tier1(name, quarter, code)
            _i1 = (_api or {}).get(1)
            return handler(tables, item1=_i1)
        return handler(tables)


def basis_tag_counts(tables):
    c = {"OFS": 0, "CFS": 0, None: 0}
    for t in tables:
        c[getattr(t, "_basis", None)] = c.get(getattr(t, "_basis", None), 0) + 1
    return c


def main():
    uni = B.load_universe()
    filings = B.discover_filings()

    census = []  # one row per (code, quarter) with a dedicated handler
    for code in sorted(filings):
        name, life_flag = uni.get(code, (None, None))
        if name is None:
            continue
        is_life = (life_flag == "생명보험")
        handler = LIFE_HANDLERS.get(code) if is_life else SONBO_HANDLERS.get(code)
        for q in sorted(filings[code], key=_quarter_sort_key):
            dirs = filings[code][q]
            tables = _collect_tables(dirs)
            if not tables:
                continue
            btag = basis_tag_counts(tables)

            # (a) current -- the REAL dispatch (dedicated handler if registered, else the
            # full fallback chain exactly as parse_filing runs it live).
            t1_html, t2_current = B.parse_filing(dirs, is_life, code=code, name=name, quarter=q)

            row = {
                "code": code, "name": name, "quarter": q, "is_life": is_life,
                "has_dedicated_handler": handler is not None,
                "handler_name": getattr(handler, "__name__", None),
                "basis_tag_counts": btag,
                "t2_current": t2_current,
            }

            if handler is not None:
                tables_ofs = _prefer_ofs(tables)
                t2_pref = _call_dedicated(handler, tables_ofs, is_life, name, q, code)
                key_items = (4, 5) if is_life else (4, 5, 6)
                structural_fail = (not t2_pref) or all(t2_pref.get(i) is None for i in key_items)
                row["t2_ofs_preferred"] = None if structural_fail else t2_pref
                row["ofs_structural_fail"] = structural_fail
                if not structural_fail and t2_current:
                    diffs = {}
                    for k, v_ofs in t2_pref.items():
                        if not isinstance(k, int):
                            continue
                        v_cur = t2_current.get(k)
                        if v_ofs is None or v_cur is None:
                            continue
                        try:
                            if abs(float(v_ofs) - float(v_cur)) > 0.05:
                                diffs[k] = {"current": v_cur, "ofs_preferred": v_ofs}
                        except (TypeError, ValueError):
                            pass
                    row["diffs"] = diffs
                else:
                    row["diffs"] = {}
            else:
                row["t2_ofs_preferred"] = None
                row["ofs_structural_fail"] = None
                row["diffs"] = {}

            census.append(row)

    out_path = Path("scripts/_probes/out_20260826_pl_basis_census.json")
    out_path.write_text(json.dumps(census, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- summary ----
    flagged = [r for r in census if r["diffs"]]
    by_company = {}
    for r in flagged:
        by_company.setdefault(r["code"], {"name": r["name"], "quarters": []})
        by_company[r["code"]]["quarters"].append((r["quarter"], sorted(r["diffs"].keys())))

    print(f"total (code,quarter) rows with a filing: {len(census)}")
    n_dedicated = sum(1 for r in census if r["has_dedicated_handler"])
    print(f"rows with a dedicated handler: {n_dedicated}")
    n_structfail = sum(1 for r in census if r.get("ofs_structural_fail"))
    print(f"rows where OFS-preferred pool structurally failed (no signal): {n_structfail}")
    print(f"rows FLAGGED (current != ofs_preferred on >=1 item, tol 0.05): {len(flagged)}")
    print()
    print("=== flagged companies (code: name -> [(quarter, [items])]) ===")
    for code in sorted(by_company):
        info = by_company[code]
        print(f"{code}\t{info['name']}\t{len(info['quarters'])} quarters")
        for q, items in info["quarters"]:
            print(f"    {q}: items {items}")

    print()
    print("=== companies with a dedicated handler but ZERO flags (candidate 'already fine / moot') ===")
    handler_codes = sorted({r["code"] for r in census if r["has_dedicated_handler"]})
    flagged_codes = set(by_company.keys())
    for code in handler_codes:
        if code not in flagged_codes and code not in ALREADY_AUDITED:
            name = uni.get(code, (code, None))[0]
            print(f"{code}\t{name}")


if __name__ == "__main__":
    main()
