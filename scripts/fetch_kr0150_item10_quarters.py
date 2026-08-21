# -*- coding: utf-8 -*-
"""One-off: fetch 서울보증보험(KR0150) 2025.1Q-3Q DART body XML.

KR0150 is in `src.ifrs17.universe.EXCLUDED_SKIP` so it's filtered out of
`ifrs17_batch_historical.py --pilot`'s universe lookup (that exclusion exists
because K-ICS 지급여력 disclosure treats it as PAA-only/no-CSM — see
universe.py docstring). DART periodic reports resumed for it 2024.4Q onward
(TODO_downloader.md 2026-08-03 note), so it's still fetchable directly via
resolve_corp + process_one_period, just not through the universe-filtered CLI.
Requested by inbox/downloader/20260813T1954Z (item10 note backfill).
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

PERIODS = ["2025.1Q", "2025.2Q", "2025.3Q"]


def main() -> int:
    settings.ensure_dirs()
    client = OpenDARTClient.from_settings()
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
    print(f"=== KR0150 {canonical} ({corp_code}) ===")
    for label in PERIODS:
        target = TARGETS_BY_LABEL[label]
        r = process_one_period(client, "KR0150", canonical, corp_code, target, skip_extract=True)
        print(f"  {label}: {r.get('status')}  {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
