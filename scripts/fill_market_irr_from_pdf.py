"""Recover IRR scenario net-assets (items 41-46) from RAW PDF, gated against the
EXISTING item36 (금리위험액) — not the PDF-disclosed total.

The MD-only loader's IRR branch needs the in-PDF 금리위험액 total to verify, but
some layouts (e.g. 교보생명 transposed 금리위험액 현황 table) don't expose a parseable
total even though the 6 net-asset values are clean. Here we instead reconcile the
derived 금리위험액 against the item36 already in the master, using the validator's
EXACT formula + tolerance (max(2, 0.05*expected)). So anything stored is GREEN by
construction and can never introduce a 36_irr RED. UPSERT (idempotent).

Spec: docs/agents/kics-market-risk-decomposition.md §7.
Usage: PYTHONIOENCODING=utf-8 python scripts/fill_market_irr_from_pdf.py [--dry-run]
"""
from __future__ import annotations
import argparse, io, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from fill_market_subitems_to_disclosure import (  # noqa: E402
    extract_irr_netassets, derive_irr, _parse_value, _to_eok, _meta_for, IRR_SCEN,
)
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

JSON_PATH = REPO / "kics_disclosure.json"


def quarter_to_period(q):
    m = re.match(r"(\d{4})\.(\d)Q", q)
    return f"FY{m.group(1)}_Q{m.group(2)}"


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")
    existing = {(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in rows}

    item36, have41 = {}, {}
    for r in rows:
        if r["항목번호"] == 36:
            v = _parse_value(str(r["값"]))
            if v is not None:
                item36[(r["원보험사코드"], r["공시분기"])] = float(v)
        if r["항목번호"] in (41, 42, 43, 44, 45, 46):
            have41.setdefault((r["원보험사코드"], r["공시분기"]), set()).add(r["항목번호"])

    worklist = sorted(k for k in item36 if len(have41.get(k, set())) < 6)
    print(f"worklist (item36 present, 41-46 incomplete): {len(worklist)}\n")

    new_rows, ok, fail = [], [], []
    for code, q in worklist:
        pdfs = disclosure_pdfs(quarter_to_period(q), code)
        if not pdfs:
            continue
        try:
            vals, _total = extract_irr_netassets(pdfs[0])
        except Exception:
            vals = None
        if not vals:
            continue
        eok_vals = [float(_to_eok(v, "백만원")) for v in vals]
        der = derive_irr(eok_vals)
        it36 = item36[(code, q)]
        tol = max(2.0, 0.05 * abs(der))   # validator-mirrored tolerance
        if abs(der - it36) > tol:
            fail.append((code, q))
            continue
        meta = _meta_for(rows, code)
        if not meta:
            continue
        stored = []
        for k, (item_no, name) in enumerate(IRR_SCEN):
            if (code, item_no, q) in existing:
                continue
            new_rows.append({**meta, "원보험사코드": code, "항목번호": item_no,
                             "항목명": name, "공시분기": q, "값": _to_eok(vals[k], "백만원")})
            stored.append(item_no)
        ok.append((code, q, der, it36, stored))

    print(f"PASS item36-gate (storable): {len(ok)} quarters")
    for code, q, der, it36, stored in ok:
        print(f"  +{code} {q:9s} derived={der:.1f} item36={it36:.1f} items={stored}")
    print(f"skip (derived != item36, would RED): {len(fail)}")
    print(f"\nnew rows: {len(new_rows)}")

    if args.dry_run:
        print("(dry-run; no write)")
        return 0
    if not new_rows:
        print("nothing to write")
        return 0
    rows.extend(new_rows)
    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
