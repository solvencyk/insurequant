# -*- coding: utf-8 -*-
"""Probe: check registries relevant to KR0005 2026.2Q — transition applicability,
pinned-absence cells, TFI applicability."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

with open(ROOT / "data" / "_derived" / "kics_transition_applicability.json", encoding="utf-8") as f:
    ta = json.load(f)

if isinstance(ta, dict):
    for k, v in ta.items():
        if "KR0005" in str(k):
            print("transition_applicability:", k, "->", v)
elif isinstance(ta, list):
    for row in ta:
        if row.get("원보험사코드") == "KR0005" or row.get("code") == "KR0005":
            print("transition_applicability row:", row)
