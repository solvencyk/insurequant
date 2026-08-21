# -*- coding: utf-8 -*-
"""One-off: FY2022-2024 annual raw for the 5 insurers that only had FY2025_Q4
on disk (inbox/downloader/20260819T0620Z, owner-reported via IFRS17.html —
악사손해보험 등 5사가 2024/2025년 2개년밖에 안 보임).

All 5 are non-listed and file 감사보고서/연결감사보고서 only, never 사업보고서
(confirmed via unfiltered list_filings — same pattern discovered for AIG in
inbox/downloader/20260819T0820Z). `process_one_period`'s A001/사업보고서 search
would return no_filing for every one of them, so rcept_no is looked up directly
here instead (same technique as scripts/fetch_reserve_gap_kr0150_kr0029.py's
AIG branch).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.opendart_client import OpenDARTClient, OpenDARTError  # noqa: E402
from scripts._dart_path_helpers import annual_raw_dir  # noqa: E402

# {KR_code: (canonical_name, corp_code, {report_label: rcept_no})}
# rcepts resolved via list_filings(pblntf_ty=None) 2026-08-20; see changelog.
COMPANIES: dict[str, tuple[str, str, dict[str, str]]] = {
    "KR0049": ("악사손해보험", "00383198", {
        "감사보고서 (2022.12)": "20230406001727",
        "감사보고서 (2023.12)": "20240402002008",
        "감사보고서 (2024.12)": "20250407003441",
    }),
    "KR0050": ("하나손해보험", "00471891", {
        "감사보고서 (2022.12)": "20230331000892",
        "연결감사보고서 (2022.12)": "20230331000894",
        "감사보고서 (2023.12)": "20240325000106",
        "연결감사보고서 (2023.12)": "20240325000107",
        "감사보고서 (2024.12)": "20250324000432",
        "연결감사보고서 (2024.12)": "20250324000433",
    }),
    "KR0051": ("신한이지손해보험", "00499426", {
        "감사보고서 (2022.12)": "20230328000350",
        "감사보고서 (2023.12)": "20240327000673",
        "감사보고서 (2024.12)": "20250328002305",
    }),
    "KR0076": ("아이엠라이프생명보험", "00124063", {
        "감사보고서 (2022.12)": "20230327000753",
        "감사보고서 (2023.12)": "20240405002220",
        "감사보고서 (2024.12)": "20250404003437",
    }),
    "KR1010": ("교보라이프플래닛생명보험", "00992622", {
        "감사보고서 (2022.12)": "20230330000275",
        "연결감사보고서 (2022.12)": "20230330000278",
        "감사보고서 (2023.12)": "20240328001011",
        "연결감사보고서 (2023.12)": "20240328001012",
        "감사보고서 (2024.12)": "20250328001411",
        "연결감사보고서 (2024.12)": "20250328001412",
    }),
}


def main() -> int:
    settings.ensure_dirs()
    client = OpenDARTClient.from_settings()

    n_fetched, n_skip, n_err = 0, 0, 0
    for kr, (canonical, corp_code, rcepts) in COMPANIES.items():
        print(f"=== {kr} {canonical} ({corp_code}) ===")
        for report_nm, rcept_no in rcepts.items():
            out_dir = annual_raw_dir(
                canonical_name=canonical, rcept_no=rcept_no,
                kr_code=kr, corp_code=corp_code,
            )
            zip_path = out_dir / "document.zip"
            if zip_path.is_file():
                print(f"  {report_nm} ({rcept_no}): already on disk -> {out_dir}")
                n_skip += 1
                continue
            try:
                client.fetch_document_xml(rcept_no, zip_path)
            except OpenDARTError as exc:
                print(f"  {report_nm} ({rcept_no}): download_error: {exc}")
                n_err += 1
                continue
            print(f"  {report_nm} ({rcept_no}): fetched -> {out_dir}")
            n_fetched += 1

    print(f"\n=== summary: fetched={n_fetched} already_had={n_skip} errors={n_err} ===")
    return 1 if n_err else 0


if __name__ == "__main__":
    raise SystemExit(main())
