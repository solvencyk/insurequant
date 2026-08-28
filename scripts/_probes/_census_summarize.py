#!/usr/bin/env python3
"""Summarize data/_derived/dart_sign_reversal_census.json: dedupe OFS/CFS duplicates,
keep only candidates whose cell is actually live (non-null) in PL_breakdown.json, and
write a compact unique-candidate table plus a same-FY YTD-continuity cross-check score
(does flipping the cumulative field's sign make it consistent with neighboring quarters'
YTD chain, the same reasoning the orchestrator applied by hand for KR0083) to help
prioritize which candidates are worth a raw-XML read."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "data" / "_derived" / "dart_sign_reversal_census.json"
PL_PATH = ROOT / "PL_breakdown.json"


def _qkey(q):
    y, n = q.split(".")
    return (int(y), int(n[0]))


def _prev_q(q):
    y, n = _qkey(q)
    return None if n == 1 else f"{y}.{n - 1}Q"


def main():
    data = json.loads(CENSUS.read_text(encoding="utf-8"))
    direct = data["direct_candidates"]
    pl_rows = json.loads(PL_PATH.read_text(encoding="utf-8"))
    pl_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in pl_rows}
    # (code, item) -> {quarter: 값}  for YTD-continuity cross-check
    ytd_by_code_item = {}
    for r in pl_rows:
        key = (r["원보험사코드"], r["항목번호"])
        ytd_by_code_item.setdefault(key, {})[r["공시분기"]] = r.get("값")

    # dedupe by (kr_code, quarter, item, account_id) -- OFS vs CFS give identical rows
    uniq = {}
    for c in direct:
        key = (c["kr_code"], c["quarter"], c["item"], c["account_id"])
        uniq.setdefault(key, c)

    live = [c for c in uniq.values() if c["kr_code"] and c["master_값"] is not None]
    print(f"unique (code,quarter,item,account) candidates: {len(uniq)}")
    print(f"  of those, LIVE (kr_code resolved + master 값 populated): {len(live)}")
    print()

    rows_out = []
    for c in sorted(live, key=lambda x: (x["kr_code"], x["quarter"], x["item"])):
        code, item, q = c["kr_code"], c["item"], c["quarter"]
        add_mmw = c["thstrm_add_amount"] / 1e6         # cached cumulative, 백만원, AS STORED (wrong-sign candidate)
        amt_mmw = c["thstrm_amount"] / 1e6              # cached 3-month, 백만원
        master_v = c["master_값"]
        matches_cached_add = abs((master_v or 0) - add_mmw) < 0.01

        # same-FY prior-quarter YTD (from OUR master's own 값 series -- independent of
        # this cache row, sourced from whatever filing populated that earlier quarter)
        pq = _prev_q(q)
        prev_ytd = ytd_by_code_item.get((code, item), {}).get(pq) if pq else 0.0
        implied_3mo_asis = None if prev_ytd is None else round(add_mmw - prev_ytd, 3)
        implied_3mo_flipped = None if prev_ytd is None else round(-add_mmw - prev_ytd, 3)
        asis_gap = None if implied_3mo_asis is None else abs(implied_3mo_asis - amt_mmw)
        flipped_gap = None if implied_3mo_flipped is None else abs(implied_3mo_flipped - amt_mmw)
        verdict = "?"
        if asis_gap is not None and flipped_gap is not None:
            tol = max(50.0, abs(amt_mmw) * 0.02)
            if flipped_gap <= tol and asis_gap > tol:
                verdict = "SIGN-BUG-LIKELY"
            elif asis_gap <= tol and flipped_gap > tol:
                verdict = "as-is-consistent(volatility, not a bug)"
            elif asis_gap <= tol and flipped_gap <= tol:
                verdict = "ambiguous(both close)"
            else:
                verdict = "neither-close(check prev-quarter itself)"

        rows_out.append({
            "kr_code": code, "name": c["name"], "quarter": q, "item": item,
            "account_nm": c["account_nm"],
            "cached_thstrm_amount_mmw": round(amt_mmw, 3),
            "cached_thstrm_add_amount_mmw": round(add_mmw, 3),
            "master_값": master_v,
            "matches_cached_add_as_stored": matches_cached_add,
            "prev_q": pq, "prev_q_ytd": prev_ytd,
            "implied_3mo_if_asis": implied_3mo_asis,
            "implied_3mo_if_flipped": implied_3mo_flipped,
            "asis_gap": asis_gap, "flipped_gap": flipped_gap,
            "verdict": verdict,
        })

    for r in rows_out:
        print(f"{r['kr_code']} {r['name']} {r['quarter']} item{r['item']} ({r['account_nm']}): "
              f"master값={r['master_값']} cached_add={r['cached_thstrm_add_amount_mmw']} "
              f"cached_amt={r['cached_thstrm_amount_mmw']} prevQ={r['prev_q']}={r['prev_q_ytd']} "
              f"asis_gap={r['asis_gap']} flipped_gap={r['flipped_gap']} => {r['verdict']}")

    out_path = ROOT / "data" / "_derived" / "dart_sign_reversal_census_summary.json"
    out_path.write_text(json.dumps(rows_out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {out_path}")

    likely = [r for r in rows_out if r["verdict"] == "SIGN-BUG-LIKELY"]
    print(f"\nSIGN-BUG-LIKELY count: {len(likely)}")
    for r in likely:
        print(f"  {r['kr_code']} {r['name']} {r['quarter']} item{r['item']} ({r['account_nm']})")


if __name__ == "__main__":
    main()
