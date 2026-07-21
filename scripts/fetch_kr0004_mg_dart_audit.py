# -*- coding: utf-8 -*-
"""Fetch 엠지손해보험(KR0004 = 구 MG, 現 예별손해보험) annual 감사보고서 from DART.

KR0004 is 비상장 → no 정기보고서(pblntf_ty=A), so it was outside the IFRS17 DART
universe. But as a 외부감사법 주식회사 it files annual 감사보고서(pblntf_ty=F), which
carries the IFRS17 보험계약 주석 (CSM 등) — same path as the 5 audit-only foreign-affiliate
life insurers (ifrs17_ingest_audit_annual). DART entity name = '엠지손해보험'
(corp_code 00962861); the new '예별손해보험' corp (01974696) has 0 filings yet.

Saves each filing to the canonical audit-annual raw layout:
  data/dart/FY<year>_Q4/raw/KR0004_엠지손해보험_<rcept>/document.zip + <rcept>_<sfx>.xml
별도(00760) = primary (build_csm_waterfall_master uses 별도, drops 연결 00761).
"""
import io
import sys
import zipfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ifrs17.opendart_client import OpenDARTClient

ROOT = Path("data/dart").resolve()
NAME = "엠지손해보험"

# (rcept_no, fiscal_year, kind) — from DART probe (corp_code 00962861).
# Scope (owner 2026-06-16): 별도만, FY2023~ (IFRS17 effective 2023; FY2022=IFRS4 제외,
# 연결 제외 — build_csm_waterfall_master는 별도 00760 사용). 8건 중 3건만 보존.
FILINGS = [
    ("20240408000665", 2023, "별도"),  # 감사보고서 (2023.12)
    ("20250408000587", 2024, "별도"),  # 감사보고서 (2024.12)
    ("20260406003175", 2025, "별도"),  # 감사보고서 (2025.12)
]


def main() -> int:
    client = OpenDARTClient.from_settings()
    results = []
    for rcept, year, kind in FILINGS:
        period = f"FY{year}_Q4"
        d = ROOT / period / "raw" / f"KR0004_{NAME}_{rcept}"
        d.mkdir(parents=True, exist_ok=True)
        zpath = d / "document.zip"
        try:
            client.fetch_document_xml(rcept, zpath)
        except Exception as e:
            print(f"  [{period} {kind} {rcept}] fetch FAIL: {str(e)[:70]}")
            results.append((period, kind, rcept, False, "fetch err"))
            continue
        # unzip the XML member(s) alongside, preserving DART's inner name (carries _00760/_00761)
        xmls = []
        try:
            with zipfile.ZipFile(zpath) as zf:
                for info in zf.infolist():
                    if info.filename.lower().endswith(".xml"):
                        (d / info.filename).write_bytes(zf.read(info.filename))
                        xmls.append(info.filename)
        except zipfile.BadZipFile:
            print(f"  [{period} {kind} {rcept}] bad zip")
            results.append((period, kind, rcept, False, "bad zip"))
            continue
        kb = zpath.stat().st_size // 1024
        print(f"  [{period} {kind} {rcept}] -> {d.name}/ ({kb}KB zip, xml={xmls})")
        results.append((period, kind, rcept, True, ",".join(xmls)))

    print("\n== SUMMARY ==")
    for period, kind, rcept, ok, info in results:
        print(f"  {period} {kind} {rcept}: {'OK' if ok else 'FAIL'}  {info}")
    print(f"  {sum(1 for *_, ok, _ in results if ok)}/{len(results)} ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
