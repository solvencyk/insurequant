# -*- coding: utf-8 -*-
"""One-off: re-fetch Samsung Life annual filing (previous batch hit exception)."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.opendart_client import OpenDARTClient  # noqa: E402


def main():
    settings.ensure_dirs()
    client = OpenDARTClient.from_settings()

    matches = client.find_corp_codes_by_name("삼성생명")
    exact = [m for m in matches if m["corp_name"] == "삼성생명"]
    chosen = (exact or matches)[0]
    corp_code = chosen["corp_code"]
    canonical = chosen["corp_name"]
    print(f"[match] {canonical}  corp_code={corp_code}")

    filings = client.list_filings(corp_code, "20250101", "20250601")
    annual = [
        f for f in filings
        if "사업보고서" in f.get("report_nm", "")
        and "기재정정" not in f.get("report_nm", "")
    ]
    rcept_no = annual[0]["rcept_no"]
    print(f"[filing] rcept_no={rcept_no}  report_nm={annual[0].get('report_nm')}")

    out_dir = settings.raw_dir / f"{canonical}_{rcept_no}"
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "document.zip"
    if not zip_path.is_file():
        client.fetch_document_xml(rcept_no, zip_path)
        print(f"[downloaded] {zip_path}  {zip_path.stat().st_size:,} bytes")
    else:
        print(f"[cached] {zip_path}")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(out_dir)
    for p in sorted(out_dir.glob("*.xml")):
        print(f"  - {p.name}  {p.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
