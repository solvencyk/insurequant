#!/usr/bin/env python3
"""Pass 1 census: every distinct (account_id, account_nm) seen under sj_div=='CIS' in the
OFS FS-API cache, across the full PL_breakdown 36-company universe and every (year, reprt)
combo that actually has a cache file on disk.  No assumptions about which account_id maps to
which of the 7 new OCI items -- this is the raw census the mapping gets designed from.
Read-only: does not touch any master JSON.  Ticket: inbox/parser/20260828T0113Z."""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.fetch_dart_fs import resolve_corp, REPRT, CACHE  # noqa: E402

OUT = Path("artifacts/parser/oci_label_census_pass1.json")


def load_universe():
    rows = json.loads(Path("PL_breakdown.json").read_text(encoding="utf-8"))
    uni = {}
    for r in rows:
        code = r.get("원보험사코드")
        if code and code not in uni:
            uni[code] = (r.get("원수사명"), r.get("생손보여부"))
    return uni


def quarters_for(code, rows_by_code):
    return sorted({r["공시분기"] for r in rows_by_code.get(code, [])})


def main():
    uni = load_universe()
    all_rows = json.loads(Path("PL_breakdown.json").read_text(encoding="utf-8"))
    rows_by_code = defaultdict(list)
    for r in all_rows:
        rows_by_code[r["원보험사코드"]].append(r)

    # account_id (or, if blank, "NM:"+account_nm) -> {account_nm variants: count}, companies, quarters
    census = defaultdict(lambda: {"count": 0, "nms": defaultdict(int), "codes": set(), "quarters": set()})
    per_company_quarter_status = []  # (code, name, quarter, cache_status)
    corp_cache = {}
    n_ofs_missing = 0
    n_ofs_present = 0
    n_no_cis_rows = 0

    for code in sorted(uni):
        name, kind = uni[code]
        cc = corp_cache.get(name)
        if cc is None:
            cc = resolve_corp(name)
            corp_cache[name] = cc
        quarters = quarters_for(code, rows_by_code)
        for q in quarters:
            year = q[:4]
            reprt = REPRT.get(q[5:])
            if not reprt or not cc:
                per_company_quarter_status.append((code, name, q, "no_corp_or_reprt"))
                continue
            p = CACHE / f"{cc}_{year}_{reprt}_OFS.json"
            if not p.exists():
                n_ofs_missing += 1
                per_company_quarter_status.append((code, name, q, "ofs_cache_missing"))
                continue
            n_ofs_present += 1
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                per_company_quarter_status.append((code, name, q, f"read_error:{e}"))
                continue
            if d.get("status") not in ("000", "013"):
                per_company_quarter_status.append((code, name, q, f"api_status:{d.get('status')}"))
                continue
            lst = d.get("list") or []
            cis = [a for a in lst if a.get("sj_div") == "CIS"]
            if not cis:
                n_no_cis_rows += 1
                per_company_quarter_status.append((code, name, q, "ofs_present_no_cis_rows"))
                continue
            per_company_quarter_status.append((code, name, q, f"ok:{len(cis)}_cis_rows"))
            for a in cis:
                aid = a.get("account_id") or ""
                nm = (a.get("account_nm") or "").strip()
                detail = a.get("account_detail") or ""
                key = aid if aid and "표준계정코드 미사용" not in aid else f"NM:{nm}"
                rec = census[key]
                rec["count"] += 1
                rec["nms"][nm] += 1
                rec["codes"].add(code)
                rec["quarters"].add(q)
                rec.setdefault("account_detail_variants", defaultdict(int))
                rec["account_detail_variants"][detail] += 1

    # keyword filter for candidate OCI-relevant rows
    KEYWORDS = ("포괄", "위험회피", "지분", "채무", "재분류", "재측정", "재평가",
                "재보험", "보험계약", "환산")
    interesting = {k: v for k, v in census.items()
                   if any(kw in nm for kw in KEYWORDS for nm in v["nms"])}

    print(f"universe companies: {len(uni)}")
    print(f"company-quarter cells checked: {len(per_company_quarter_status)}")
    print(f"  ofs cache present: {n_ofs_present}  missing: {n_ofs_missing}  "
          f"present-but-no-CIS-rows: {n_no_cis_rows}")
    print(f"distinct account_id/NM keys under CIS (all): {len(census)}")
    print(f"distinct keys matching OCI keyword filter: {len(interesting)}")
    print()
    print("=== keyword-filtered census (account_id | account_nm variants | #codes | #rows) ===")
    for key, v in sorted(interesting.items(), key=lambda kv: -kv[1]["count"]):
        nms = ", ".join(f"{nm}({c})" for nm, c in sorted(v["nms"].items(), key=lambda x: -x[1]))
        print(f"{key}")
        print(f"    nm={nms}  codes={len(v['codes'])}  rows={v['count']}  "
              f"quarters={len(v['quarters'])}")
        print(f"    detail_variants={dict(v.get('account_detail_variants', {}))}")
        print(f"    company_codes={sorted(v['codes'])}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    dump = {
        "universe_size": len(uni),
        "cells_checked": len(per_company_quarter_status),
        "ofs_present": n_ofs_present, "ofs_missing": n_ofs_missing,
        "ofs_present_no_cis": n_no_cis_rows,
        "census_all": {k: {"count": v["count"], "nms": dict(v["nms"]),
                            "codes": sorted(v["codes"]), "n_quarters": len(v["quarters"]),
                            "account_detail_variants": dict(v.get("account_detail_variants", {}))}
                       for k, v in census.items()},
        "per_company_quarter_status": [
            {"code": c, "name": n, "quarter": q, "status": s}
            for c, n, q, s in per_company_quarter_status],
    }
    OUT.write_text(json.dumps(dump, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
