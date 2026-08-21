# -*- coding: utf-8 -*-
"""One-off: fetch DART body XML for the two universe-filtered outliers needed
by the 법정준비금(IFRS17_BS items 5-8) reserve raw-gap ticket
(inbox/downloader/20260819T0820Z).

- KR0150 서울보증보험 is in `src.ifrs17.universe.EXCLUDED_SKIP`, so it never
  appears in `ifrs17_batch_historical.py --pilot`'s universe lookup. It's
  fetched directly via resolve_corp + process_one_period instead (same
  pattern as scripts/fetch_kr0150_item10_quarters.py), for order A/B/C's 8
  periods (2023.1Q ~ 2024.4Q).
- KR0029 AIG손해보험 fails `resolve_corp("AIG손해보험")` (DART's registered
  name is 에이아이지손해보험; documented NO_CORP_MATCH quirk). Fetched via
  hardcoded corp_code 00983606, for order D's single period (2024.4Q).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.opendart_client import OpenDARTClient, OpenDARTError  # noqa: E402
from scripts.ifrs17_batch_all import resolve_corp  # noqa: E402
from scripts.ifrs17_batch_historical import TARGETS_BY_LABEL, process_one_period  # noqa: E402
from scripts._dart_path_helpers import annual_raw_dir  # noqa: E402

KR0150_PERIODS = [
    "2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q",
    "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q",
]
KR0029_CORP_CODE = "00983606"
KR0029_CANONICAL = "에이아이지손해보험"
# AIG only files 감사보고서/연결감사보고서 (pblntf_ty=F), never 사업보고서 (A001) —
# confirmed via scripts/_diag_aig_2024_filings.py (list_filings with no type
# filter). process_one_period's fetch_rcept_no searches for report_keyword=
# "사업보고서" against pblntf_detail_ty=A001, which never matches, so FY2024_Q4
# needs the known rcept fetched directly (same pattern as the FY2023_Q4 dir
# already on disk, which used rcept 20240403002101 = 감사보고서 (2023.12)).
KR0029_FY2024_RCEPTS = {
    "감사보고서 (2024.12)": "20250409001949",
    "연결감사보고서 (2024.12)": "20250409001951",
}


def main() -> int:
    settings.ensure_dirs()
    client = OpenDARTClient.from_settings()

    print("=== KR0150 서울보증보험 (EXCLUDED_SKIP bypass) ===")
    try:
        chosen = resolve_corp(client, "서울보증보험")
    except OpenDARTError as exc:
        print(f"resolve_corp failed: {exc}")
        return 1
    if not chosen:
        print("resolve_corp -> no match")
        return 1
    canonical = chosen["corp_name"]
    corp_code = chosen["corp_code"]
    print(f"  resolved: {canonical} ({corp_code})")
    for label in KR0150_PERIODS:
        target = TARGETS_BY_LABEL[label]
        r = process_one_period(client, "KR0150", canonical, corp_code, target, skip_extract=True)
        print(f"  {label}: {r.get('status')}  {r}")

    print("\n=== KR0029 에이아이지손해보험 FY2024_Q4 (known-rcept direct fetch, audit report only) ===")
    for report_nm, rcept_no in KR0029_FY2024_RCEPTS.items():
        out_dir = annual_raw_dir(
            canonical_name=KR0029_CANONICAL, rcept_no=rcept_no,
            kr_code="KR0029", corp_code=KR0029_CORP_CODE,
        )
        zip_path = out_dir / "document.zip"
        if zip_path.is_file():
            print(f"  {report_nm} ({rcept_no}): already on disk -> {out_dir}")
            continue
        try:
            client.fetch_document_xml(rcept_no, zip_path)
        except OpenDARTError as exc:
            print(f"  {report_nm} ({rcept_no}): download_error: {exc}")
            continue
        print(f"  {report_nm} ({rcept_no}): fetched -> {out_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
