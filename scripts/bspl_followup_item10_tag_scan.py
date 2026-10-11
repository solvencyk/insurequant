#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 2 side finding: BS item 10 (현금및현금성자산) alternative-tag order.

build_ifrs17_bs._extract_from_list takes, for item 10, the FIRST row of the FS-API list whose account_id is ANY of
(ifrs-full_CashAndCashEquivalents, dart_CashAndDuefromBanks, dart_DueFromBanksAtAmortisedCost) -- the tuple order is not honoured, the
list order (alphabetical by account_id: dart_* before ifrs-full_*) decides.  A filer that tags BOTH lines (cash AND a separate 예치금 line)
therefore gets the 예치금 line as 'cash'.  This scans every cached OFS/CFS FS-API response for filers that have both tags with a value
and compares the master cell.  Read-only.   Output: data/_derived/bspl_followup_20261011/item10_tag_scan.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

CACHE = ROOT / "data" / "dart" / "_fs_api_cache"
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "item10_tag_scan.json"
REPRT = {"11013": "1Q", "11012": "2Q", "11014": "3Q", "11011": "4Q"}


def num(x):
    if x in (None, "", "-"):
        return None
    try:
        return float(str(x).replace(",", "")) / 1e6
    except ValueError:
        return None


def main():
    from scripts.fetch_dart_fs import resolve_corp  # noqa: E402
    rows = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    meta = {}
    mv = {}
    for r in rows:
        meta.setdefault(r["원보험사코드"], r["원수사명"])
        mv[(r["원보험사코드"], r["항목번호"], r["공시분기"])] = r["값"]
    cc2kr = {}
    for kr, name in meta.items():
        try:
            cc = resolve_corp({"KR0029": "AIG"}.get(kr, name))
        except Exception:
            cc = None
        if cc:
            cc2kr[cc] = kr
    res = []
    for p in sorted(CACHE.glob("*_OFS.json")):
        m = re.match(r"(\d+)_(\d{4})_(\d+)_OFS", p.stem)
        if not m:
            continue
        cc, year, reprt = m.groups()
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("status") != "000":
            continue
        bs = [a for a in (d.get("list") or []) if a.get("sj_div") == "BS" and a.get("account_detail") == "-"]
        first = None
        cash = dep = None
        for a in bs:
            aid = a.get("account_id")
            if aid in ("ifrs-full_CashAndCashEquivalents", "dart_CashAndDuefromBanks", "dart_DueFromBanksAtAmortisedCost"):
                if first is None and num(a.get("thstrm_amount")) is not None:
                    first = (aid, a.get("account_nm"), num(a.get("thstrm_amount")))
                if aid == "ifrs-full_CashAndCashEquivalents":
                    cash = num(a.get("thstrm_amount"))
                elif aid == "dart_CashAndDuefromBanks":
                    dep = num(a.get("thstrm_amount"))
        if cash is None or dep is None:
            continue
        kr = cc2kr.get(cc)
        q = f"{year}.{REPRT.get(reprt)}"
        m10 = mv.get((kr, 10, q))
        res.append({"corp_code": cc, "code": kr, "quarter": q, "cash_CashAndCashEquivalents": cash, "dep_CashAndDuefromBanks": dep,
                    "builder_first_match": first, "master_item10": m10,
                    "master_equals_dep": (m10 is not None and abs(m10 - dep) < 1e-3),
                    "master_equals_cash": (m10 is not None and abs(m10 - cash) < 1e-3)})
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"OFS responses with BOTH tags valued: {len(res)}")
    by = {}
    for r in res:
        by.setdefault(r["code"], []).append(r)
    for kr, lst in sorted(by.items(), key=lambda kv: str(kv[0])):
        print(f"{kr} {meta.get(kr)}: {len(lst)} filings, master==예치금 {sum(1 for r in lst if r['master_equals_dep'])}, "
              f"master==현금및현금성자산 {sum(1 for r in lst if r['master_equals_cash'])}")


if __name__ == "__main__":
    main()
