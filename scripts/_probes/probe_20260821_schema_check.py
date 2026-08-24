# -*- coding: utf-8 -*-
"""row 스키마 확인: 필드 순서/타입, 항목번호 43~46(가장 최근 신설 항목) 사례로 패턴 확인."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
for r in rows:
    if r["원보험사코드"] == "KR0100" and r["공시분기"] == "2024.4Q" and int(r["항목번호"]) == 1:
        print("샘플 item1:", json.dumps(r, ensure_ascii=False))
        print("keys order:", list(r.keys()))
        print("항목번호 type:", type(r["항목번호"]))
        break

for r in rows:
    if r["원보험사코드"] == "KR0100" and r["공시분기"] == "2024.4Q" and int(r["항목번호"]) == 41:
        print("샘플 item41:", json.dumps(r, ensure_ascii=False))
        break

genders = {}
for r in rows:
    genders.setdefault(r["원보험사코드"], (r.get("생손보여부"), r.get("티커"), r.get("원수사명")))
print("\n생손보여부/티커 몇 예:")
for c in ["KR0100", "KR0083", "KR1011", "KR0104", "KR0001", "KR1000"]:
    print(" ", c, genders.get(c))
