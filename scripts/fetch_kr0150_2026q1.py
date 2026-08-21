# -*- coding: utf-8 -*-
"""One-off: fetch 서울보증보험(KR0150) 2026.1Q DART body XML.

Same EXCLUDED_SKIP bypass as fetch_kr0150_item10_quarters.py (2025.1Q-3Q).
Requested by inbox/downloader/20260814T0000Z (equity_composition item10-notes
backfill round2) — the 2025.1~3Q ticket's footnote claiming "2026.1Q already
has raw" was mistaken; the directory doesn't exist.
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

PERIODS = ["2026.1Q"]


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
