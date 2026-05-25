# -*- coding: utf-8 -*-
"""Smoke-test the OpenDART API key (read from .env or env var).

Fails loudly if:
  - network is down
  - key is revoked / over quota
  - DART response shape changed

The key value is never printed.

Usage:
    set OPENDART_API_KEY=<your_key>   (or write into .env at repo root)
    python scripts/ifrs17_verify_api_key.py
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.opendart_client import OpenDARTClient, OpenDARTError  # noqa: E402


def main() -> int:
    settings.ensure_dirs()
    try:
        client = OpenDARTClient.from_settings()
    except Exception as exc:
        print(f"[FAIL] client init: {exc}")
        return 2

    try:
        ping = client.ping()
        print(f"[PING] status={ping['status']} message={ping['message']!r} "
              f"sample_count={ping['sample_count']}")
        if ping["status"] != "000":
            print("[FAIL] API key did NOT return status=000.")
            return 1
    except OpenDARTError as exc:
        print(f"[FAIL] ping raised OpenDARTError: {exc}")
        return 1
    except Exception:
        print("[FAIL] unexpected exception during ping:")
        traceback.print_exc()
        return 2

    print("[OK] OpenDART API key works.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
