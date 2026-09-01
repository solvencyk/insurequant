# -*- coding: utf-8 -*-
"""2026-09-01 companion to probe_20260901_sensitivity_fy2026q2_census.py.

14 of the 38 companies under data/dart/FY2026_Q2/raw/ carry meta.json {"no_filing": true} --
this script cross-checks that flag against the LIVE DART filing list (not just trusting the
downloader's cache) so a genuine structural absence isn't confused with a downloader miss.
Also resolves the one company that looked like a possible downloader gap: 에이아이지손해보험
(AIG, KR0029) has NO directory at all under FY2026_Q2/raw (unlike the 14 above, which at least
have a directory + explicit no_filing flag) -- this script confirms AIG genuinely files zero
periodic (pblntf_ty=A: 사업/반기/분기) disclosures, same as AIA -- both only ever file an
annual 감사보고서(연결감사보고서), never a "정기공시". So it is NOT a downloader gap either.

Needs OPENDART_API_KEY in .env (read via src.ifrs17.config.settings). ~1 API call per company
plus corp_code lookups; a few seconds total.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260901_sensitivity_nofiling_dart_verify.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.opendart_client import OpenDARTClient  # noqa: E402

# The 14 companies whose FY2026_Q2/raw/<dir>/meta.json says "no_filing": true.
NO_FILING_FLAGGED = [
    ("KR0004", "예별손해보험"), ("KR0049", "악사손해보험"), ("KR0050", "하나손해보험"),
    ("KR0051", "신한이지손해보험"), ("KR0074", "라이나생명보험"),
    ("KR0075", "비엔피파리바카디프생명보험"), ("KR0076", "아이엠라이프생명보험"),
    ("KR0080", "에이아이에이생명보험"), ("KR0095", "메트라이프생명보험"),
    ("KR0097", "하나생명보험"), ("KR0100", "처브라이프생명보험"),
    ("KR1010", "교보라이프플래닛생명보험"), ("KR1011", "아이비케이연금보험"),
    ("KR1098", "카카오페이손해보험"),
]
# The one company with NO raw dir at all for FY2026_Q2 (not even a no_filing placeholder).
NO_RAW_DIR_AT_ALL = [("KR0029", "에이아이지손해보험")]


def check(client: OpenDARTClient, name: str) -> None:
    hits = client.find_corp_codes_by_name(name)
    exact = [h for h in hits if h["corp_name"] == name]
    chosen = exact[0] if exact else (hits[0] if hits else None)
    if not chosen:
        print(f"  {name}: NO CORP_CODE MATCH ({len(hits)} hits)")
        return
    cc = chosen["corp_code"]
    periodic = client.list_filings(cc, "20260101", "20260831", pblntf_ty="A")
    any_type = client.list_filings(cc, "20260101", "20260831", pblntf_ty=None)
    print(f"  {name} corp_code={cc} stock={chosen.get('stock_code') or '(non-listed)'}: "
          f"periodic(A, 사업/반기/분기)={len(periodic)} any_disclosure_type={len(any_type)} "
          f"in 2026-01~08")
    for f in any_type[:5]:
        print(f"      {f.get('report_nm')} | rcept={f.get('rcept_no')} | dt={f.get('rcept_dt')}")


if __name__ == "__main__":
    client = OpenDARTClient(api_key=settings.resolve_api_key())
    print("=== meta.json no_filing:true companies -- live DART cross-check ===")
    for kr, name in NO_FILING_FLAGGED:
        check(client, name)
    print("\n=== no raw dir at all (possible downloader gap?) ===")
    for kr, name in NO_RAW_DIR_AT_ALL:
        check(client, name)
    print("\nExpected result (2026-09-01): every row shows periodic(A)=0 -- all are audit-only "
          "filers (연결감사보고서/감사보고서 only, stock=non-listed), confirming the FY2026_Q2 "
          "absence is structural, not a downloader miss.")
