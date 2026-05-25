# -*- coding: utf-8 -*-
"""PoC: fetch one DART filing by company name (no permanent KR<->corp map).

Resolves company_name -> corp_code via OpenDART /api/corpCode.xml on the fly.
If multiple matches, picks the first (and prints them all for review).

Usage:
    python scripts/ifrs17_fetch_one_filing.py  # defaults to "삼성화재" 2024
    python scripts/ifrs17_fetch_one_filing.py 메리츠화재 2024
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.opendart_client import OpenDARTClient  # noqa: E402


def fetch_annual(name: str, year: int) -> Path | None:
    settings.ensure_dirs()
    client = OpenDARTClient.from_settings()

    matches = client.find_corp_codes_by_name(name)
    if not matches:
        print(f"[{name}] no corp_code match")
        return None
    if len(matches) > 1:
        print(f"[{name}] {len(matches)} matches — picking first:")
        for m in matches[:5]:
            print(f"  - {m['corp_code']} {m['corp_name']} (stock={m['stock_code']})")
    corp_code = matches[0]["corp_code"]
    canonical_name = matches[0]["corp_name"]
    print(f"[{name}] using corp_code={corp_code} ({canonical_name})")

    filings = client.list_filings(
        corp_code=corp_code,
        bgn_de=f"{year + 1}0101",
        end_de=f"{year + 1}0601",
    )
    print(f"[{name}] {len(filings)} filings in {year+1}-01..06")
    annual = [f for f in filings
              if "사업보고서" in f.get("report_nm", "")
              and "기재정정" not in f.get("report_nm", "")]
    target = annual[0] if annual else (filings[0] if filings else None)
    if not target:
        print(f"[{name}] no suitable filing")
        return None
    print(f"[{name}] selected: {target['rcept_dt']} {target['report_nm']} "
          f"rcept_no={target['rcept_no']}")

    out_dir = settings.raw_dir / f"{canonical_name}_{target['rcept_no']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "document.zip"
    client.fetch_document_xml(target["rcept_no"], zip_path)
    print(f"[{name}] wrote {zip_path} ({zip_path.stat().st_size:,} bytes)")
    with zipfile.ZipFile(zip_path) as zf:
        for n in zf.namelist():
            print(f"  - {n}")
        zf.extractall(out_dir)
    return out_dir


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "삼성화재"
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2024
    fetch_annual(name, year)
