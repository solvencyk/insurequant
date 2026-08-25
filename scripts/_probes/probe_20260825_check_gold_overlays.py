# -*- coding: utf-8 -*-
"""16건 관련 회사가 owner gold overlay(user_pl_cells.json / user_pl_confirmed_cells.json)에
이미 있는지 확인. 있으면 그 셀은 절대 덮지 않는다(작업지시 §4).

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_check_gold_overlays.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

COMPANIES = [
    "에이비엘생명보험", "동양생명", "케이디비생명보험", "DB생명보험", "DB손해보험",
    "메리츠화재해상보험", "흥국화재", "교보라이프플래닛생명보험",
    "비엔피파리바카디프생명보험", "한화생명", "한화손해보험", "KB라이프생명",
    "에이아이에이생명보험",
]


def main() -> int:
    ovr = json.loads((ROOT / "data" / "_gold" / "user_pl_cells.json").read_text(encoding="utf-8"))
    conf = json.loads((ROOT / "data" / "_gold" / "user_pl_confirmed_cells.json").read_text(encoding="utf-8"))

    print("=== user_pl_cells.json (override 값 레지스트리) ===")
    print("keys:", list(ovr.keys()))
    for s in ovr.get("set", []):
        nm = s.get("원수사명") or ""
        if any(c in nm for c in COMPANIES) or s.get("원보험사코드") in ():
            print(" SET", s)

    print("\n=== user_pl_confirmed_cells.json (owner 확정 레지스트리) ===")
    print("keys:", list(conf.keys()))
    cells = conf.get("cells", [])
    print("cells type:", type(cells), "len:", len(cells) if hasattr(cells, "__len__") else "?")
    if isinstance(cells, list):
        for c in cells:
            s = json.dumps(c, ensure_ascii=False)
            if any(co in s for co in COMPANIES):
                print(" CONFIRMED", s)
    elif isinstance(cells, dict):
        for k, v in cells.items():
            if any(co in k for co in COMPANIES):
                print(" CONFIRMED", k, "->", v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
