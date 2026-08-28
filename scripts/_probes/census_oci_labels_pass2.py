#!/usr/bin/env python3
"""Pass 2: candidate account_id mapping for the 7 new OCI items (25-31), applied across the
full 36-company / 356-cell PL_breakdown universe.  Computes per-cell values, the missing-cell
grid, the 24+25=31 identity residual distribution (sanity check that item25/31 are the RIGHT
tags), and dumps raw numeric evidence for the ambiguous hedge-tag companies (KR0073/KR0008)
and the annual-vs-quarterly thstrm_amount/thstrm_add_amount divergence.  Read-only.
Ticket: inbox/parser/20260828T0113Z."""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import resolve_corp, REPRT, CACHE  # noqa: E402

OUT = Path("artifacts/parser/oci_label_census_pass2.json")

# item -> primary account_id (chosen from pass1: highest-coverage, unambiguous standard tag)
ACCT_OCI = {
    25: "ifrs-full_OtherComprehensiveIncome",
    26: "ifrs-full_OtherComprehensiveIncomeNetOfTaxFinancialAssetsMeasuredAtFairValueThroughOtherComprehensiveIncome",
    27: "ifrs-full_OtherComprehensiveIncomeNetOfTaxInsuranceFinanceIncomeExpensesFromInsuranceContractsIssuedExcludedFromProfitOrLossThatWillBeReclassifiedToProfitOrLoss",
    28: "ifrs-full_OtherComprehensiveIncomeNetOfTaxCashFlowHedges",
    29: "ifrs-full_OtherComprehensiveIncomeNetOfTaxGainsLossesFromInvestmentsInEquityInstruments",
    30: "ifrs-full_OtherComprehensiveIncomeNetOfTaxFinanceIncomeExpensesFromReinsuranceContractsHeldExcludedFromProfitOrLoss",
    31: "ifrs-full_ComprehensiveIncome",
}
# secondary (fallback) account_ids per item, tried when primary absent in that filing
ACCT_OCI_FALLBACK = {
    28: ["dart_OtherComprehensiveIncomeNetOfTaxGainsLossesOnHedgingInstrument",
         "dart_GainsValuationDerivativesCashFlowHedge", "dart_LossesValuationDerivativesCashFlowHedge",
         "dart_GainFromDerivativesHeldForHedging", "dart_LossFromDerivativesHeldForHedging"],
}
# account_nm fallback (exact, whitespace-stripped) for "-표준계정코드 미사용-" rows, tried last
NM_FALLBACK = {
    26: ["기타포괄손익-공정가치측정금융자산평가손익"],
    28: ["위험회피목적파생상품평가손익", "위험회피파생상품평가손익"],
}


def _to_num(x):
    if x in (None, "", "-"):
        return None
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return None


def load_universe():
    rows = json.loads(Path("PL_breakdown.json").read_text(encoding="utf-8"))
    uni = {}
    rows_by_code = defaultdict(list)
    for r in rows:
        code = r.get("원보험사코드")
        if code and code not in uni:
            uni[code] = (r.get("원수사명"), r.get("생손보여부"))
        rows_by_code[code].append(r)
    return uni, rows_by_code


def extract_cell(lst, annual):
    """Return {item: (value_mn, source)} for one filing's CIS list."""
    out = {}
    by_id = defaultdict(list)      # account_id -> [row,...] (dup guard)
    by_nm_untagged = defaultdict(list)
    for a in lst:
        if a.get("sj_div") != "CIS":
            continue
        aid = a.get("account_id") or ""
        nm = (a.get("account_nm") or "").strip()
        if aid and "표준계정코드 미사용" not in aid:
            by_id[aid].append(a)
        else:
            by_nm_untagged[nm].append(a)

    def _val(a):
        raw = a.get("thstrm_amount") if annual else (a.get("thstrm_add_amount") or a.get("thstrm_amount"))
        v = _to_num(raw)
        return None if v is None else v / 1e6

    for item, aid in ACCT_OCI.items():
        rows = by_id.get(aid)
        if rows:
            v = _val(rows[0])
            if v is not None:
                out[item] = (round(v, 6), f"id:{aid}")
                continue
        for fid in ACCT_OCI_FALLBACK.get(item, []):
            rows = by_id.get(fid)
            if rows:
                v = _val(rows[0])
                if v is not None:
                    out[item] = (round(v, 6), f"fallback_id:{fid}")
                    break
        if item in out:
            continue
        for nm in NM_FALLBACK.get(item, []):
            rows = by_nm_untagged.get(nm)
            if rows:
                v = _val(rows[0])
                if v is not None:
                    out[item] = (round(v, 6), f"nm:{nm}")
                    break
    return out


def main():
    uni, rows_by_code = load_universe()
    corp_cache = {}
    missing = []          # (code, name, quarter, item, reason)
    identity_residuals = []   # (code, quarter, ni24, oci25, tci31, resid)
    per_cell = {}          # (code, quarter) -> {item: (val, src)}
    cell_status = []       # (code, quarter, "ok_all"/"partial"/"no_cis"/"no_corp")
    evidence_kr0073 = []
    evidence_kr0008 = []
    quarterly_thstrm_probe = []

    for code in sorted(uni):
        name, kind = uni[code]
        cc = corp_cache.get(name)
        if cc is None:
            cc = resolve_corp(name)
            corp_cache[name] = cc
        quarters = sorted({r["공시분기"] for r in rows_by_code[code]})
        for q in quarters:
            year, qn = q[:4], q[5:]
            reprt = REPRT.get(qn)
            annual = (qn == "4Q")
            if not cc or not reprt:
                cell_status.append((code, name, q, "no_corp_or_reprt"))
                for it in ACCT_OCI:
                    missing.append((code, name, q, it, "no_corp_or_reprt"))
                continue
            p = CACHE / f"{cc}_{year}_{reprt}_OFS.json"
            if not p.exists():
                cell_status.append((code, name, q, "ofs_missing"))
                for it in ACCT_OCI:
                    missing.append((code, name, q, it, "ofs_cache_missing"))
                continue
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                cell_status.append((code, name, q, "read_error"))
                for it in ACCT_OCI:
                    missing.append((code, name, q, it, "read_error"))
                continue
            lst = d.get("list") or []
            cis = [a for a in lst if a.get("sj_div") == "CIS"]
            if not cis:
                cell_status.append((code, name, q, "no_cis_rows"))
                for it in ACCT_OCI:
                    missing.append((code, name, q, it, "audit_only_no_xbrl_cis"))
                continue
            vals = extract_cell(lst, annual)
            per_cell[(code, q)] = vals
            for it in ACCT_OCI:
                if it not in vals:
                    missing.append((code, name, q, it, "tag_not_found_in_filing"))
            cell_status.append((code, name, q,
                                "ok_all" if len(vals) == 7 else f"partial_{len(vals)}/7"))

            if 24 in [r["항목번호"] for r in rows_by_code[code] if r["공시분기"] == q]:
                ni24 = next((r["값"] for r in rows_by_code[code]
                            if r["공시분기"] == q and r["항목번호"] == 24), None)
                if ni24 is not None and 25 in vals and 31 in vals:
                    resid = (ni24 + vals[25][0]) - vals[31][0]
                    identity_residuals.append((code, q, ni24, vals[25][0], vals[31][0], round(resid, 3)))

            if code == "KR0073":
                for a in cis:
                    nm = (a.get("account_nm") or "")
                    if "위험회피" in nm or "헤지" in nm:
                        evidence_kr0073.append({
                            "quarter": q, "account_id": a.get("account_id"), "account_nm": nm,
                            "thstrm_amount": a.get("thstrm_amount"),
                            "thstrm_add_amount": a.get("thstrm_add_amount")})
            if code == "KR0008":
                for a in cis:
                    nm = (a.get("account_nm") or "")
                    if "위험회피" in nm or "헤지" in nm:
                        evidence_kr0008.append({
                            "quarter": q, "account_id": a.get("account_id"), "account_nm": nm,
                            "thstrm_amount": a.get("thstrm_amount"),
                            "thstrm_add_amount": a.get("thstrm_add_amount")})
            if not annual and code in ("KR0069", "KR0068", "KR0008"):
                for a in cis:
                    if a.get("account_id") in ACCT_OCI.values():
                        quarterly_thstrm_probe.append({
                            "code": code, "quarter": q, "account_id": a.get("account_id"),
                            "thstrm_nm": a.get("thstrm_nm"),
                            "thstrm_amount": a.get("thstrm_amount"),
                            "thstrm_add_amount": a.get("thstrm_add_amount")})

    n_cells = len(cell_status)
    n_full = sum(1 for c in cell_status if c[3] == "ok_all")
    print(f"total (code,quarter) cells: {n_cells}")
    print(f"  all-7-items found: {n_full}")
    print(f"  status breakdown:")
    from collections import Counter
    ctr = Counter(c[3] for c in cell_status)
    for k, v in sorted(ctr.items(), key=lambda kv: -kv[1]):
        print(f"    {k}: {v}")

    print(f"\ntotal missing (cell,item) pairs: {len(missing)}")
    reason_ctr = Counter(m[4] for m in missing)
    for k, v in sorted(reason_ctr.items(), key=lambda kv: -kv[1]):
        print(f"    {k}: {v}")
    print("\nmissing-by-item counts:")
    item_ctr = Counter(m[3] for m in missing)
    for it in sorted(item_ctr):
        print(f"    item{it}: {item_ctr[it]} missing / {n_cells} cells")

    print(f"\n=== 24+25=31 identity residuals (n={len(identity_residuals)}) ===")
    resids = sorted((abs(r[5]) for r in identity_residuals))
    if resids:
        import statistics
        print(f"  min={resids[0]:.3f} median={statistics.median(resids):.3f} "
              f"p90={resids[int(len(resids)*0.9)]:.3f} max={resids[-1]:.3f}")
        big = [r for r in identity_residuals if abs(r[5]) > 50]
        print(f"  residual > 50 (백만원): {len(big)}")
        for r in big[:30]:
            print(f"    {r}")

    print(f"\n=== KR0073 hedge-tag evidence (raw CIS rows containing 위험회피/헤지) ===")
    for e in evidence_kr0073:
        print(f"  {e}")
    print(f"\n=== KR0008 hedge-tag evidence ===")
    for e in evidence_kr0008:
        print(f"  {e}")
    print(f"\n=== quarterly thstrm_amount vs thstrm_add_amount probe (non-annual quarters) ===")
    for e in quarterly_thstrm_probe[:60]:
        print(f"  {e}")

    print(f"\n=== full missing list (code,name,quarter,item,reason) ===")
    for m in missing:
        print(f"  {m}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "cell_status": [{"code": c, "name": n, "quarter": q, "status": s} for c, n, q, s in cell_status],
        "missing": [{"code": c, "name": n, "quarter": q, "item": it, "reason": r} for c, n, q, it, r in missing],
        "identity_residuals": [{"code": c, "quarter": q, "ni24": a, "oci25": b, "tci31": d, "resid": e}
                                for c, q, a, b, d, e in identity_residuals],
        "kr0073_hedge_evidence": evidence_kr0073,
        "kr0008_hedge_evidence": evidence_kr0008,
        "quarterly_thstrm_probe": quarterly_thstrm_probe,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
