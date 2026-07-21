# -*- coding: utf-8 -*-
"""One-off: download FY2025 annual DART filings for the 10 non-life (손보)
insurers, reusing the existing OpenDARTClient. Download + verify only — no
extraction or build (parsing is the orchestrator's job).

Verification: count occurrences of '계약의 유형' in the largest XML. FY2025
annual reports carry the LOB analysis note (보험수익/보험서비스비용 by
계약의 유형: 장기/자동차/일반); FY2024 reports lack it.

Artifacts mirror the existing layout:
  data/dart/raw/<canonical>_<rcept_no>/document.zip
  data/dart/raw/<canonical>_<rcept_no>/<rcept_no>.xml (+ _00760, _00761 ...)

Usage:
  python scripts/ifrs17_download_fy2025_nonlife.py
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.opendart_client import OpenDARTClient, OpenDARTError  # noqa: E402

# Canonical DART corp_name for each of the 10 손보 insurers. These names match
# the existing FY2024 raw dirs, so find_corp_codes_by_name(exact) resolves them.
COMPANIES: list[str] = [
    "삼성화재해상보험",
    "현대해상",
    "DB손해보험",
    "KB손해보험",
    "메리츠화재해상보험",
    "한화손해보험",
    "롯데손해보험",
    "흥국화재",
    "NH농협손해보험",
    "코리안리",
]

# Pre-validated by the reference doc: 현대해상 FY2025 = 20260312001448.
KNOWN_RCEPT: dict[str, str] = {
    "현대해상": "20260312001448",
}

# FY2025 annual reports are filed early 2026.
BGN_DE = "20260101"
END_DE = "20260601"


def pick_corp(client: OpenDARTClient, name: str) -> dict | None:
    matches = client.find_corp_codes_by_name(name)
    if not matches:
        return None
    exact = [m for m in matches if m["corp_name"] == name]
    if exact:
        return exact[0]
    # Prefer a listed one (has stock_code).
    listed = [m for m in matches if m.get("stock_code")]
    return listed[0] if listed else matches[0]


def pick_annual_filing(filings: list[dict]) -> dict | None:
    """Latest 사업보고서 (FY2025), excluding 기재정정/첨부정정 amendments first;
    fall back to any 사업보고서 if only amendments exist."""
    annual = [f for f in filings if "사업보고서" in f.get("report_nm", "")]
    if not annual:
        return None
    clean = [f for f in annual if "정정" not in f.get("report_nm", "")]
    pool = clean or annual
    pool.sort(key=lambda f: f.get("rcept_dt", ""), reverse=True)
    return pool[0]


def pick_audit_filing(filings: list[dict]) -> dict | None:
    """Fallback for non-listed: latest standalone 감사보고서 (exclude 연결)."""
    standalone = [
        f for f in filings
        if f.get("report_nm", "").startswith("감사보고서")
        and "연결" not in f.get("report_nm", "")
    ]
    standalone.sort(key=lambda f: f.get("rcept_dt", ""), reverse=True)
    return standalone[0] if standalone else None


def count_marker_in_largest_xml(out_dir: Path) -> tuple[str, int, int]:
    """Return (largest_xml_name, size_bytes, '계약의 유형' count)."""
    xmls = sorted(out_dir.glob("*.xml"))
    if not xmls:
        return ("", 0, 0)
    largest = max(xmls, key=lambda p: p.stat().st_size)
    text = largest.read_text(encoding="utf-8", errors="replace")
    return (largest.name, largest.stat().st_size, text.count("계약의 유형"))


def run_one(client: OpenDARTClient, name: str) -> dict:
    chosen = pick_corp(client, name)
    if not chosen:
        return {"company": name, "status": "no_corp_match"}
    corp_code = chosen["corp_code"]
    canonical = chosen["corp_name"]

    # Resolve the FY2025 filing.
    filing_type = ""
    if name in KNOWN_RCEPT:
        rcept_no = KNOWN_RCEPT[name]
        filing_type = "사업보고서"
    else:
        filings = client.list_filings(corp_code, BGN_DE, END_DE)  # pblntf_ty=A
        target = pick_annual_filing(filings)
        if target:
            filing_type = "사업보고서"
        else:
            # Non-listed fallback: 감사보고서 (pblntf_ty=F).
            f_filings = client.list_filings(corp_code, BGN_DE, END_DE, pblntf_ty="F")
            target = pick_audit_filing(f_filings)
            filing_type = "감사보고서"
        if not target:
            return {"company": name, "canonical": canonical,
                    "corp_code": corp_code, "status": "no_fy2025_filing"}
        rcept_no = target["rcept_no"]

    out_dir = settings.raw_dir / f"{canonical}_{rcept_no}"
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "document.zip"
    if not zip_path.is_file():
        try:
            client.fetch_document_xml(rcept_no, zip_path)
        except OpenDARTError as exc:
            return {"company": name, "canonical": canonical,
                    "corp_code": corp_code, "rcept_no": rcept_no,
                    "filing_type": filing_type,
                    "status": f"download_error: {exc}"}
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(out_dir)
    except zipfile.BadZipFile as exc:
        return {"company": name, "canonical": canonical,
                "corp_code": corp_code, "rcept_no": rcept_no,
                "filing_type": filing_type, "status": f"bad_zip: {exc}"}

    xml_name, xml_size, marker_count = count_marker_in_largest_xml(out_dir)
    status = "ok" if marker_count > 0 else "FLAG_no_lob_note"
    return {
        "company": name, "canonical": canonical, "corp_code": corp_code,
        "rcept_no": rcept_no, "filing_type": filing_type,
        "main_xml": xml_name, "main_xml_size": xml_size,
        "marker_count": marker_count, "status": status,
        "save_path": str(out_dir.relative_to(REPO)),
    }


def main() -> int:
    settings.ensure_dirs()
    client = OpenDARTClient.from_settings()
    print(f"[fy2025-nonlife] {len(COMPANIES)} companies")

    results = []
    for i, name in enumerate(COMPANIES, 1):
        print(f"\n[{i}/{len(COMPANIES)}] === {name} ===")
        try:
            r = run_one(client, name)
        except OpenDARTError as exc:
            r = {"company": name, "status": f"dart_error: {exc}"}
        print(f"  {r.get('canonical', '?')} rcept={r.get('rcept_no', '-')} "
              f"type={r.get('filing_type', '-')} "
              f"size={r.get('main_xml_size', '-')} "
              f"'계약의 유형'={r.get('marker_count', '-')} "
              f"status={r.get('status')}")
        results.append(r)

    print("\n" + "=" * 70)
    print("REPORT")
    print("=" * 70)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
