#!/usr/bin/env python3
"""Census: DART FS-API sign-reversal defect (inbox/parser/20260828T1200Z KR0083 2024.3Q).

The KR0083 2024.3Q bug: thstrm_add_amount (cumulative) has the OPPOSITE sign from
thstrm_amount (3-month) for the same account_id in the same cached response, while
thstrm_amount matches the raw XML table and |thstrm_add_amount| also matches the raw
table's magnitude -- i.e. only the cumulative field's SIGN is corrupted at the API
layer, not its magnitude. This script scans every data/dart/_fs_api_cache/*.json file
for the same signature (opposite sign + |cumulative| > |3-month|, both non-zero) on the
account_ids our PL builder (scripts/fetch_dart_fs.py) actually maps into a schema item,
then cross-references each candidate against the LIVE root PL_breakdown.json to see
which candidates are real, populated, currently-wrong-signed cells.

This is a DISCRIMINANT, not a verdict: legitimate quarter-to-quarter sign flips (e.g. a
volatile investment-income line that lost money in H1 but gained more than that back in
Q3 alone) trip the same heuristic. Candidates must be confirmed against the raw filing
XML (or the FS-API's own row, cross-checked with the printed table in the XML) before
any cell is corrected -- this script only narrows the search space.

Offline (data/dart/_fs_api_cache/*.json + data/dart/FY*/raw/*/meta.json + PL_breakdown.json).

Usage:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/census_dart_sign_reversal.py
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from scripts.fetch_dart_fs import ACCT, ACCT_OCI, ACCT_OCI_28_FALLBACK, FIN, IS_PREFIX  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "dart" / "_fs_api_cache"
RAW_ROOT = ROOT / "data" / "dart"
PL_PATH = ROOT / "PL_breakdown.json"

REPRT_TO_Q = {"11013": "1Q", "11012": "2Q", "11014": "3Q", "11011": "4Q"}

# account_id -> our item number, for the DIRECT 1:1 maps (ACCT + ACCT_OCI + the item28
# name-tag fallback). FIN (item19 component) and IS_PREFIX (item3/8 component) tags are
# not 1:1 with a single item, so they're reported separately, unmapped to an item#.
ACCOUNT_TO_ITEM = {}
for _n, _aid in ACCT.items():
    ACCOUNT_TO_ITEM[_aid] = _n
for _n, _aid in ACCT_OCI.items():
    ACCOUNT_TO_ITEM[_aid] = _n
for _aid in ACCT_OCI_28_FALLBACK:
    ACCOUNT_TO_ITEM.setdefault(_aid, 28)

FIN_IDS = set(FIN.values())
IS_PREFIX_IDS = set(IS_PREFIX.values())


def _to_num(x):
    if x in (None, "", "-"):
        return None
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return None


def _build_meta_index():
    """(corp_code, quarter) -> (KR_code, canonical_name), scanned from every raw filing's
    meta.json -- the same local, no-network bridge the prior OCI census used."""
    idx = {}
    for meta_path in RAW_ROOT.glob("FY*/raw/*/meta.json"):
        try:
            m = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        cc, q = m.get("corp_code"), m.get("period")
        if not cc or not q:
            continue
        kr_code = meta_path.parent.name.split("_", 1)[0]
        idx[(cc, q)] = (kr_code, m.get("canonical"))
    return idx


def _load_pl_index():
    rows = json.loads(PL_PATH.read_text(encoding="utf-8"))
    return {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}


def main():
    meta_idx = _build_meta_index()
    pl_idx = _load_pl_index()

    cache_files = sorted(CACHE.glob("*.json"))
    n_files = n_rows_scanned = 0
    direct_candidates = []
    component_candidates = []

    for f in cache_files:
        # filename: <corp_code>_<year>_<reprt_code>_<OFS|CFS>.json
        stem = f.stem
        parts = stem.split("_")
        if len(parts) != 4:
            continue
        corp_code, year, reprt_code, fs_div = parts
        qn = REPRT_TO_Q.get(reprt_code)
        if qn is None:
            continue
        quarter = f"{year}.{qn}"
        n_files += 1
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        lst = d.get("list") if isinstance(d, dict) else None
        if not lst:
            continue
        for r in lst:
            if r.get("sj_div") not in ("IS", "CIS"):
                continue
            aid = r.get("account_id") or ""
            if aid not in ACCOUNT_TO_ITEM and aid not in FIN_IDS and not any(
                aid.startswith(p) for p in IS_PREFIX_IDS
            ):
                continue
            n_rows_scanned += 1
            amt = _to_num(r.get("thstrm_amount"))
            add = _to_num(r.get("thstrm_add_amount"))
            if amt is None or add is None or amt == 0 or add == 0:
                continue
            if (amt > 0) == (add > 0):
                continue                      # same sign -> not a candidate
            # NOTE: the ticket's stated discriminant also requires |cumulative| > |3-month|,
            # but KR0083 2024.3Q item28 (a CONFIRMED bug, verified against raw XML in the
            # ticket) fails that magnitude test (|add|=5,322,135,208 < |amt|=8,612,492,159 --
            # Q1+Q2 offset in the opposite direction, a legitimate cumulative-smaller-than-
            # quarterly pattern that can coexist with a genuine sign bug). Magnitude is left
            # OUT of the pre-filter here; the YTD-continuity cross-check in
            # _census_summarize.py (does flipping the cached cumulative's sign make it
            # consistent with the master's own prior-quarter YTD?) is the real discriminant.
            kr_code, name = meta_idx.get((corp_code, quarter), (None, None))
            rec = {
                "file": f.name, "corp_code": corp_code, "quarter": quarter,
                "fs_div": fs_div, "account_id": aid, "account_nm": r.get("account_nm"),
                "kr_code": kr_code, "name": name,
                "thstrm_amount": amt, "thstrm_add_amount": add,
            }
            if aid in ACCOUNT_TO_ITEM:
                item = ACCOUNT_TO_ITEM[aid]
                rec["item"] = item
                cell = pl_idx.get((kr_code, item, quarter)) if kr_code else None
                rec["master_값"] = cell.get("값") if cell else None
                rec["master_값_당분기"] = cell.get("값_당분기") if cell else None
                direct_candidates.append(rec)
            else:
                component_candidates.append(rec)

    print(f"cache files scanned: {n_files}")
    print(f"IS/CIS rows in our account_id set: {n_rows_scanned}")
    print(f"DIRECT (1:1 item) candidates: {len(direct_candidates)}")
    print(f"COMPONENT (item19/3/8 subcomponent) candidates: {len(component_candidates)}")
    print()

    print("=== DIRECT candidates (account_id maps 1:1 to a PL item) ===")
    for c in sorted(direct_candidates, key=lambda x: (x["kr_code"] or "?", x["quarter"], x["item"])):
        live = "LIVE-CELL" if c["master_값"] is not None else "cell=None/absent"
        matches_add = (c["master_값"] is not None and c["master_값"] == c["thstrm_add_amount"] / 1e6)
        tag = "MASTER-MATCHES-WRONG-SIGN-ADD" if matches_add else ""
        print(f"  {c['kr_code']} {c['name']} {c['quarter']} item{c['item']} "
              f"({c['account_nm']}): th_amt={c['thstrm_amount']:.0f} th_add={c['thstrm_add_amount']:.0f} "
              f"| master 값={c['master_값']} 값_당분기={c['master_값_당분기']} [{live}] {tag}")

    print()
    print("=== COMPONENT candidates (feed item19 via FIN, or item3/8 via IS_PREFIX) ===")
    for c in sorted(component_candidates, key=lambda x: (x["kr_code"] or "?", x["quarter"], x["account_id"])):
        print(f"  {c['kr_code']} {c['name']} {c['quarter']} ({c['account_id']} / {c['account_nm']}): "
              f"th_amt={c['thstrm_amount']:.0f} th_add={c['thstrm_add_amount']:.0f}")

    out = {
        "direct_candidates": direct_candidates,
        "component_candidates": component_candidates,
    }
    out_path = ROOT / "data" / "_derived" / "dart_sign_reversal_census.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
