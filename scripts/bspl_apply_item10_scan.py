#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (A6): BS item 10 (현금및현금성자산) cells whose master value is a different cash-like BS line of the same FS-API response.  Read-only.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_item10_scan.py [out.json]

build_ifrs17_bs._extract_from_list takes, for item 10, the FIRST row of the response list whose account_id is ANY of
(ifrs-full_CashAndCashEquivalents, dart_CashAndDuefromBanks, dart_DueFromBanksAtAmortisedCost); the list is ordered by account_id (dart_* before ifrs-full_*),
so a filer that tags BOTH a cash line and a deposit line gets the deposit line as 'cash'.  This scan covers all three alternatives (the 2026-10-11 follow-up
scan covered dart_CashAndDuefromBanks only) over every cached OFS response and compares with the master cell.
Output: list of {code, quarter, master, cash (ifrs-full_CashAndCashEquivalents), alt_tag, alt_name, alt_value, cash_name, verdict}.
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
REPRT = {"11013": "1Q", "11012": "2Q", "11014": "3Q", "11011": "4Q"}
ALTS = ("dart_CashAndDuefromBanks", "dart_DueFromBanksAtAmortisedCost")
CASH = "ifrs-full_CashAndCashEquivalents"


def num(x):
    if x in (None, "", "-"):
        return None
    try:
        return float(str(x).replace(",", "")) / 1e6
    except ValueError:
        return None


def main():
    from scripts.fetch_dart_fs import resolve_corp
    rows = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    meta, mv = {}, {}
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
    n_resp = 0
    for p in sorted(CACHE.glob("*_OFS.json")):
        m = re.match(r"(\d+)_(\d{4})_(\d+)_OFS", p.stem)
        if not m:
            continue
        cc, year, reprt = m.groups()
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("status") != "000":
            continue
        kr = cc2kr.get(cc)
        if kr is None:
            continue
        q = f"{year}.{REPRT[reprt]}"
        bs = [a for a in (d.get("list") or []) if a.get("sj_div") == "BS" and a.get("account_detail") == "-"]
        n_resp += 1
        # the cash line = the BS row NAMED 현금및현금성자산 (tagged ifrs-full_CashAndCashEquivalents in most filings, untagged in some quarters)
        cash_row = next((a for a in bs if (a.get("account_id") == CASH or (a.get("account_nm") or "").replace(" ", "") == "현금및현금성자산")
                         and num(a.get("thstrm_amount")) is not None), None)
        first = next((a for a in bs if a.get("account_id") in (CASH,) + ALTS and num(a.get("thstrm_amount")) is not None), None)
        if cash_row is None or first is None:
            continue
        cashv = num(cash_row.get("thstrm_amount"))
        m10 = mv.get((kr, 10, q))
        for a in bs:
            if a.get("account_id") in ALTS and num(a.get("thstrm_amount")) is not None:
                av = num(a.get("thstrm_amount"))
                if m10 is not None and abs(m10 - av) < 1e-3 and abs(av - cashv) > 0.5:
                    res.append({"code": kr, "quarter": q, "master": m10, "cash": cashv, "cash_name": cash_row.get("account_nm"),
                                "alt_tag": a.get("account_id"), "alt_name": a.get("account_nm"), "alt_value": av,
                                "first_match": first.get("account_id"), "verdict": "master == alt line, != cash line"})
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "_derived" / "bspl_apply_20261011" / "item10_scan_all_alts.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    by = {}
    for r in res:
        by.setdefault(r["code"], []).append(r["quarter"])
    print(f"OFS responses scanned {n_resp}; master==alt cells {len(res)}")
    for kr, qs in sorted(by.items()):
        print(f"  {kr} {meta[kr]}: {len(qs)} cells {sorted(qs)}")
    print("->", out)


if __name__ == "__main__":
    main()
