# -*- coding: utf-8 -*-
"""Quick smoke test: company-name search via OpenDART master XML.

Verifies the new (no-permanent-map) flow that the user mandated.
Does NOT print the API key.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.opendart_client import OpenDARTClient  # noqa: E402

client = OpenDARTClient.from_settings()
for q in ["메리츠화재", "삼성화재", "삼성생명", "한화생명", "교보생명"]:
    ms = client.find_corp_codes_by_name(q)
    print(f"{q}: {len(ms)} match(es)")
    for m in ms[:6]:
        print(f"  - {m['corp_code']} {m['corp_name']} (stock={m['stock_code']})")
