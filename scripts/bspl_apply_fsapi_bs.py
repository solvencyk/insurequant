#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (parser/ifrs17): print the FS-API balance-sheet rows of one filer-quarter (read-only).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_fsapi_bs.py KR1000 2024.4Q [OFS|CFS] [--all]
Prints account_id, account_nm, thstrm_amount (백만원) for the BS rows (account_detail '-'); with --all also the detail rows.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

CACHE = ROOT / "data" / "dart" / "_fs_api_cache"
REPRT = {"1Q": "11013", "2Q": "11012", "3Q": "11014", "4Q": "11011"}


def main():
    from scripts.fetch_dart_fs import resolve_corp
    code, q = sys.argv[1], sys.argv[2]
    basis = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] in ("OFS", "CFS") else "OFS"
    allrows = "--all" in sys.argv
    rows = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    name = next(r["원수사명"] for r in rows if r["원보험사코드"] == code)
    cc = resolve_corp({"KR0029": "AIG"}.get(code, name))
    year, qq = q.split(".")
    p = CACHE / f"{cc}_{year}_{REPRT[qq]}_{basis}.json"
    print(code, name, "corp", cc, "file", p.name, "exists", p.exists())
    if not p.exists():
        return
    d = json.loads(p.read_text(encoding="utf-8"))
    print("status", d.get("status"), d.get("message"))
    for a in d.get("list") or []:
        if a.get("sj_div") != "BS":
            continue
        if not allrows and a.get("account_detail") != "-":
            continue
        v = a.get("thstrm_amount")
        try:
            mv = f"{float(str(v).replace(',', '')) / 1e6:>16,.3f}"
        except Exception:
            mv = f"{str(v):>16}"
        print(f"{str(a.get('ord')):>4} {str(a.get('account_id'))[:52]:<52} {str(a.get('account_nm'))[:30]:<30} {mv}")


if __name__ == "__main__":
    main()
