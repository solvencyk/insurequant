#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (A6): build the BS spec that replaces item 10 (현금및현금성자산) cells holding the 예치금 / 현금및예치금 line by the cash line.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_make_spec_item10.py [out.json]

Input = data/_derived/bspl_apply_20261011/item10_scan_all_alts.json (bspl_apply_item10_scan.py).  New value = the FS-API OFS balance-sheet row named
현금및현금성자산 of the same response (amount / 1e6).  Cross-check printed in the basis: the management-disclosure summary line 현금및예치금 (억원, when the
Stage-B candidate exists) must equal cash + deposit line within the 억 rounding.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
CACHE = ROOT / "data" / "dart" / "_fs_api_cache"
SCAN = ROOT / "data" / "_derived" / "bspl_apply_20261011" / "item10_scan_all_alts.json"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "_derived" / "bspl_apply_20261011" / "spec_A6_item10.json"
REPRT = {"1Q": "11013", "2Q": "11012", "3Q": "11014", "4Q": "11011"}


def num(x):
    try:
        return float(str(x).replace(",", "")) / 1e6
    except ValueError:
        return None


def main():
    from scripts.fetch_dart_fs import resolve_corp
    scan = json.loads(SCAN.read_text(encoding="utf-8"))
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    names = {r["원보험사코드"]: r["원수사명"] for r in bs}
    cells, checks = [], []
    for r in sorted(scan, key=lambda x: (x["code"], x["quarter"])):
        code, q = r["code"], r["quarter"]
        cc = resolve_corp({"KR0029": "AIG"}.get(code, names[code]))
        year, qq = q.split(".")
        p = CACHE / f"{cc}_{year}_{REPRT[qq]}_OFS.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        rows = [a for a in d["list"] if a.get("sj_div") == "BS" and a.get("account_detail") == "-"]
        cash = next(a for a in rows if (a.get("account_id") == "ifrs-full_CashAndCashEquivalents" or (a.get("account_nm") or "").replace(" ", "") == "현금및현금성자산")
                    and num(a.get("thstrm_amount")) is not None)
        new = round(num(cash["thstrm_amount"]), 6)
        alt = next(a for a in rows if a.get("account_id") == r["alt_tag"])
        old = r["master"]
        assert abs(num(alt["thstrm_amount"]) - old) < 1e-3, (code, q)
        # disclosure cross-check: summary 현금및예치금 (억원) vs cash + deposit line
        cand = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates" / f"{code}.json"
        xnote = ""
        if cand.exists():
            for c in json.loads(cand.read_text(encoding="utf-8"))["candidates"]:
                if c["item"] == 10 and c["quarter"] == q and c.get("rule", "").endswith("현금및예치금") and c.get("unit") == "억원":
                    tot = new + old if r["alt_tag"] == "dart_CashAndDuefromBanks" and "현금및예치금" not in (alt.get("account_nm") or "") else None
                    if "현금및예치금" in (alt.get("account_nm") or ""):
                        tot = old                 # the alt line IS the 현금및예치금 total
                    if tot is not None:
                        ok = abs(tot - c["value_mn"]) <= 60.0          # 억 rounding of the summary table (+-0.5억 = 50백만원)
                        checks.append((code, q, ok))
                        xnote = "" if not ok else (f" 교차확인: 정기경영공시 {q} 요약 재무상태표 p{c['page']} 「현금 및 예치금」 {c['value_mn'] / 100:,.0f}억원 대 "
                                 f"{'현금및현금성자산 + 예치금 줄' if 'Due' in r['alt_tag'] or r['alt_tag'] == 'dart_CashAndDuefromBanks' else '합'} {tot / 100:,.1f}억원 "
                                 f"(억 반올림 안에서 일치).")
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        basis = (f"정정 2026-10-11(round 3, A6): 마스터 옛 값 {old:,.6f}백만원은 DART 재무제표 API(별도) 응답의 「{alt.get('account_nm')}」({r['alt_tag']}) 줄이다. "
                 f"build_ifrs17_bs._extract_from_list 는 항목 10 에 대안 태그 3개(ifrs-full_CashAndCashEquivalents · dart_CashAndDuefromBanks · "
                 f"dart_DueFromBanksAtAmortisedCost) 중 응답 목록의 첫 행을 집는데 목록이 account_id 알파벳 순이라 dart_* 줄이 먼저 잡힌다. 이 회사는 현금 줄과 예치금 줄을 "
                 f"따로 태깅해 예치금 줄이 현금으로 들어갔다. 마스터 항목 10 의 정의(항목명 현금및현금성자산, 같은 회사 2023.1Q·2Q 와 다른 상장사 전 분기는 현금 줄)에 맞춰 "
                 f"같은 응답의 「{cash.get('account_nm')}」 {new:,.6f}백만원으로 정정. 원천: data/dart/_fs_api_cache/{p.name}(sha256 {sha[:12]}...).{xnote} "
                 f"원인 코드(build_ifrs17_bs.py)는 이 라운드 범위 밖이라 안 고침.")
        cells.append({"key": f"{code}|10|{q}", "item": 10, "quarter": q, "action": "replace", "old": old, "new": new, "line": "현금및현금성자산",
                      "pdf": f"data/dart/_fs_api_cache/{p.name}", "page": None, "pdf_sha256": sha, "basis": basis,
                      "method": "round3_fix:fs_api_ofs_cash_line", "scale": "원 -> 백만원"})
    OUT.write_text(json.dumps({"_what": "A6 BS item 10: 예치금/현금및예치금 line -> 현금및현금성자산 line", "cells": cells}, ensure_ascii=False, indent=1),
                   encoding="utf-8", newline="\n")
    for c in cells:
        print(f"{c['key']:<18} {c['old']:>16,.6f} -> {c['new']:>16,.6f}")
    print(f"{len(cells)} cells -> {OUT}; disclosure cross-checks {sum(1 for _c, _q, ok in checks if ok)}/{len(checks)} ok")
    for code, q, ok in checks:
        if not ok:
            print("  cross-check FAILED:", code, q)


if __name__ == "__main__":
    main()
