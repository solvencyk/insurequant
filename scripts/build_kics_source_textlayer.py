#!/usr/bin/env python3
"""Measure the RAW text layer of every K-ICS 정기경영공시 PDF -> data/_derived/kics_source_textlayer.json.

왜 필요한가 (2026-08-21, owner 적대적 재검증 ④): 게이트의 '적용후 세부 결측(후=전)' 버킷 246칸을
전부 **구조적으로 정당**한 것으로 세고 있었는데, 그 안에 **스캔본이라 애초에 판독 불가능한 셀**이
섞여 있었다. 판독불가는 "검증했더니 정당" 이 아니라 "검증 자체를 못 함" 이다 — 정당 버킷에 섞이면
그 숫자가 곧 false-green 이 된다.

**신호는 반드시 raw PDF 의 텍스트 레이어에서 뽑는다.** docling MD 길이로 대신하면 안 된다 —
MD 가 페이지를 통째로 떨어뜨린 것을 "원천에 없다"로 오독하는 것이 바로 이번에 적발된 면제 2건의
실패 모드다(`_AFTER_SUBRISK_NOT_DISCLOSED` 의 KR0003/KR0073 — raw 에는 표가 멀쩡히 있었다).

게이트에서 매번 fitz 로 486개 PDF 를 여는 건 ~45초라 비싸다 → 여기서 한 번 재고, 게이트는
읽기만 한다. 게이트는 사이드카를 **그대로 믿지 않는다**: 기록된 파일 크기를 디스크와 대조해
어긋나면 그 칸을 `UNMEASURED` 로 강등한다(사이드카가 stale 이면 조용히 통과하는 대신 미측정으로
드러난다).

Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_kics_source_textlayer.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from solvency.validation.kics_json_rules import KEY_CODE, KEY_QUARTER  # noqa: E402

OUT = ROOT / "data" / "_derived" / "kics_source_textlayer.json"

# 판독 하한(문자/페이지). 실측 분포(2026-08-21, 143개 raw): 스캔본 13건이 4.6~73.4,
# 텍스트본은 179~2,700 대에 몰려 있고 **73과 103 사이가 비어 있다**. 100 은 그 빈 구간에 둔 값이다.
# 100~400 은 '경계'로 따로 세어 아무것도 안 보이게 만들지 않는다(부분 스캔·표 이미지 혼재).
UNREADABLE_FLOOR = 100.0
BORDERLINE_FLOOR = 400.0


def classify(chars_per_page: float | None) -> str:
    if chars_per_page is None:
        return "UNMEASURED"
    if chars_per_page < UNREADABLE_FLOOR:
        return "UNREADABLE"
    if chars_per_page < BORDERLINE_FLOOR:
        return "BORDERLINE"
    return "READABLE"


def _fyq(q: str) -> str:
    return f"FY{q[:4]}_Q{q[5]}"


def main() -> int:
    import fitz  # imported here so the gate never needs it

    records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    cells = sorted({(r.get(KEY_CODE), r.get(KEY_QUARTER)) for r in records
                    if r.get(KEY_CODE) and r.get(KEY_QUARTER)})
    out: dict[str, dict] = {}
    t0 = time.time()
    counts = {"READABLE": 0, "BORDERLINE": 0, "UNREADABLE": 0, "NO_RAW": 0, "ERROR": 0}
    for code, q in cells:
        d = ROOT / "data" / "disclosure" / _fyq(q) / "raw"
        cands = sorted(d.glob(f"*{code}*.pdf")) if d.exists() else []
        key = f"{code}|{q}"
        if not cands:
            out[key] = {"raw": None, "status": "NO_RAW"}
            counts["NO_RAW"] += 1
            continue
        p = cands[0]
        try:
            doc = fitz.open(p)
            pages = doc.page_count
            chars = sum(len(pg.get_text()) for pg in doc)
            doc.close()
        except Exception as exc:  # noqa: BLE001
            out[key] = {"raw": p.name, "bytes": p.stat().st_size,
                        "status": "ERROR", "error": f"{type(exc).__name__}: {exc}"[:200]}
            counts["ERROR"] += 1
            continue
        cpp = (chars / pages) if pages else 0.0
        st = classify(cpp)
        out[key] = {"raw": p.name, "bytes": p.stat().st_size, "pages": pages,
                    "chars": chars, "chars_per_page": round(cpp, 1), "status": st}
        counts[st] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "_doc": ("K-ICS 정기경영공시 raw PDF 텍스트레이어 밀도. 게이트(validate_kics_disclosure)가 "
                 "'적용후 세부 결측(후=전)' 을 '원천 판독가능' 과 '판독불가(스캔본)' 로 가르는 데 쓴다. "
                 "docling MD 가 아니라 raw PDF 에서 잰다 — MD 유실을 '원천 부재' 로 오독한 전례가 이 "
                 "사이드카의 존재 이유다. 게이트는 bytes 를 디스크와 대조해 stale 이면 UNMEASURED 로 강등한다."),
        "_builder": "scripts/build_kics_source_textlayer.py",
        "generated_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "unreadable_floor_chars_per_page": UNREADABLE_FLOOR,
        "borderline_floor_chars_per_page": BORDERLINE_FLOOR,
        "cells": out,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{OUT}: {len(out)} cells in {time.time()-t0:.1f}s  {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
