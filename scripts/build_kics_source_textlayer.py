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

sys.path.insert(0, str(ROOT / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

OUT = ROOT / "data" / "_derived" / "kics_source_textlayer.json"

# 판독 하한(문자/페이지). 실측 분포(2026-08-21, 143개 raw): 스캔본 13건이 4.6~73.4,
# 텍스트본은 179~2,700 대에 몰려 있고 **73과 103 사이가 비어 있다**. 100 은 그 빈 구간에 둔 값이다.
# 100~400 은 '경계'로 따로 세어 아무것도 안 보이게 만들지 않는다(부분 스캔·표 이미지 혼재).
UNREADABLE_FLOOR = 100.0
BORDERLINE_FLOOR = 400.0

# --- 2026-09-01: 전체 평균은 '앞은 스캔·뒤는 텍스트' 문서를 영원히 READABLE 로 부른다 -------
# owner 지적으로 드러난 근본원인. 실측: FY2024_Q4 KR0071 흥국생명(538p)은 **p1-112 가 통째 스캔**
# (정기경영공시 본문)이고 p113-450 이 감사보고서·재무제표 주석이라 텍스트가 있다. 전체 평균은
# 532.8자/p → 사이드카가 READABLE 로 찍었다. 그 오판이 두 번 사람을 속였다:
#   · 2026-07-16 owner 가 'image-only PDF' 로 등재한 면제(kics_exemption_provenance entries[6])를
#   · 2026-08-21 validation 이 "538p/286,634자=533자/p 이므로 거짓" 이라며 뒤집고 '이 파일은
#     정기경영공시가 아니라 DART 사업보고서' 로까지 결론냈다. 그 반증이 틀렸다 — 근거로 든
#     'K-ICS 인접 페이지' p249·p253·p302·p304 는 전부 텍스트 구간(p113-450), 즉 감사보고서 주석이다.
# 결과적으로 처방이 downloader 재수집으로 오라우팅됐고(재수집해도 같은 스캔본이 온다) 진짜 처방인
# OCR 은 한 번도 발주되지 않았다. 그래서 이제 **페이지별 분포**와 **K-ICS 절의 위치**를 같이 잰다.

# 한 페이지가 '이미지'인지 가르는 하한(문자/페이지). 50 은 머리말·쪽번호만 남은 스캔 페이지가
# 넘지 못하는 값이다(coordinator 전수 측정 스크립트와 동일 기준).
PAGE_SCAN_FLOOR = 50
# 앞부분 연속 스캔이 이만큼이면 '본문이 이미지'로 본다. 정기경영공시 본문은 필링 맨 앞에 온다.
# 실측 17건이 이 기준에 걸리고, 그중 5건은 전체 평균이 229~693자라 종전 지표로는 안 잡혔다.
FRONT_SCAN_RUN_MIN = 10
# K-ICS 절이 텍스트로 잡히는지 보는 앵커. 하나도 없으면 그 절은 텍스트레이어에 없다.
KICS_ANCHORS = ("지급여력비율", "지급여력금액", "요구자본", "가용자본", "경과조치")


def classify(chars_per_page: float | None) -> str:
    if chars_per_page is None:
        return "UNMEASURED"
    if chars_per_page < UNREADABLE_FLOOR:
        return "UNREADABLE"
    if chars_per_page < BORDERLINE_FLOOR:
        return "BORDERLINE"
    return "READABLE"


def classify_source(page_chars: list[int], anchor_pages: list[int]) -> tuple[str, float]:
    """(페이지별 문자수, K-ICS 앵커가 잡힌 페이지들) -> (status, 판정에 쓴 밀도).

    갈래가 넷이고 **처방이 서로 다르다**:

      UNREADABLE      문서 전체가 스캔 → OCR (또는 텍스트본 재수집)
      SCANNED_SECTION 문서는 맞는데 **K-ICS 절만 이미지** → **OCR** (재수집해도 같은 파일이 온다)
      BORDERLINE      K-ICS 절 밀도가 낮음(부분 스캔·표 이미지 혼재) → 사람 확인
      READABLE        K-ICS 절이 텍스트로 잡힘 → 판정 가능

    SCANNED_SECTION 이 없던 시절에는 이 셋이 전부 READABLE 로 뭉뚱그려져 '재수집' 으로
    오라우팅됐다. 그래서 상태 이름이 처방을 담는다.
    """
    n = len(page_chars)
    if not n:
        return "UNMEASURED", 0.0
    whole = sum(page_chars) / n
    # ① 문서 전체가 스캔 — 종전과 같은 판정(연속성 유지).
    if whole < UNREADABLE_FLOOR:
        return "UNREADABLE", whole
    # ② 앞부분이 통째로 이미지. 공시 본문이 거기 있다 → 뒤쪽 감사보고서가 만든 평균을 믿지 않는다.
    front_run = 0
    for c in page_chars:
        if c < PAGE_SCAN_FLOOR:
            front_run += 1
        else:
            break
    if front_run >= FRONT_SCAN_RUN_MIN:
        return "SCANNED_SECTION", whole
    # ③ 텍스트는 있는데 K-ICS 앵커가 문서 어디에도 없다 → 그 절은 텍스트레이어에 없다.
    if not anchor_pages:
        return "SCANNED_SECTION", whole
    # ④ 앵커가 걸린 구간의 밀도로 판정하되, **전체 평균 판정보다 느슨해지지 않는다**.
    #
    # 이 지표는 '전체 평균이 과대평가하는 문서'를 잡으려고 만든 것이지 전체 평균이 이미 의심한
    # 문서를 사면하려고 만든 것이 아니다. 느슨한 쪽을 허용하면 그 순간 이 사이드카가 면제 발급기가
    # 된다 — 실측으로도 그런 칸이 나왔다: KR0080 2025.3Q 는 33p 중 23p 가 스캔인데 앵커가 잡힌
    # **단 한 페이지**가 2,176자라 구간밀도만 보면 READABLE 로 올라간다(전체평균 262.7 = BORDERLINE).
    # 한 페이지가 텍스트라는 사실은 그 절 전체가 텍스트라는 증거가 못 된다. 그래서 둘 중 **엄한 쪽**을 쓴다.
    lo, hi = min(anchor_pages), max(anchor_pages)
    window = page_chars[lo:hi + 1]
    dens = (sum(window) / len(window)) if window else whole
    sec, base = classify(dens), classify(whole)
    return (sec if _SEVERITY[sec] <= _SEVERITY[base] else base), dens


# 판정 강도 사다리. 숫자가 작을수록 '더 못 믿는다'. 위 ④ 에서 둘 중 엄한 쪽을 고르는 데 쓴다.
_SEVERITY = {"UNREADABLE": 0, "SCANNED_SECTION": 1, "BORDERLINE": 2, "READABLE": 3, "UNMEASURED": 0}


def _fyq(q: str) -> str:
    return f"FY{q[:4]}_Q{q[5]}"


def main() -> int:
    import fitz  # imported here so the gate never needs it

    records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    cells = sorted({(r.get(KEY_CODE), r.get(KEY_QUARTER)) for r in records
                    if r.get(KEY_CODE) and r.get(KEY_QUARTER)})
    out: dict[str, dict] = {}
    t0 = time.time()
    counts = {"READABLE": 0, "BORDERLINE": 0, "UNREADABLE": 0, "SCANNED_SECTION": 0,
              "UNMEASURED": 0, "NO_RAW": 0, "ERROR": 0}
    for code, q in cells:
        # raw/ 우선, 없으면 pdf/ — 2026.2Q 부터 다운로더가 pdf/ 로 떨군다(39사 중 raw 는 1개뿐).
        # raw/ 만 보던 종전 코드는 2026.2Q 39사를 통째로 NO_RAW 로 흘려 게이트가 전원을
        # UNMEASURED(판정 불가)로 찍었다. 상세: scripts/_disclosure_pdf_paths.py
        cands = disclosure_pdfs(_fyq(q), code)
        key = f"{code}|{q}"
        if not cands:
            out[key] = {"raw": None, "status": "NO_RAW"}
            counts["NO_RAW"] += 1
            continue
        p = cands[0]
        try:
            doc = fitz.open(p)
            pages = doc.page_count
            page_chars: list[int] = []
            anchor_pages: list[int] = []
            for i, pg in enumerate(doc):
                t = pg.get_text()
                page_chars.append(len(t.strip()))
                if any(a in t for a in KICS_ANCHORS):
                    anchor_pages.append(i)
            doc.close()
        except Exception as exc:  # noqa: BLE001
            out[key] = {"raw": p.name, "bytes": p.stat().st_size,
                        "status": "ERROR", "error": f"{type(exc).__name__}: {exc}"[:200]}
            counts["ERROR"] += 1
            continue
        chars = sum(page_chars)
        cpp = (chars / pages) if pages else 0.0
        st, dens = classify_source(page_chars, anchor_pages)
        front_run = 0
        for c in page_chars:
            if c < PAGE_SCAN_FLOOR:
                front_run += 1
            else:
                break
        out[key] = {
            "raw": p.name, "bytes": p.stat().st_size, "pages": pages,
            "chars": chars, "chars_per_page": round(cpp, 1), "status": st,
            # 아래 4개가 '전체 평균 하나로 판정' 을 대체하는 실측 근거다.
            "scan_pages": sum(1 for c in page_chars if c < PAGE_SCAN_FLOOR),
            "front_scan_run": front_run,
            "anchor_pages": len(anchor_pages),
            "section_chars_per_page": round(dens, 1),
        }
        counts[st] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "_doc": ("K-ICS 정기경영공시 raw PDF 텍스트레이어 밀도. 게이트(validate_kics_disclosure)가 "
                 "'적용후 세부 결측(후=전)' 을 '원천 판독가능' 과 '판독불가(스캔본)' 로 가르는 데 쓴다. "
                 "docling MD 가 아니라 raw PDF 에서 잰다 — MD 유실을 '원천 부재' 로 오독한 전례가 이 "
                 "사이드카의 존재 이유다. 게이트는 bytes 를 디스크와 대조해 stale 이면 UNMEASURED 로 강등한다. "
                 "2026-09-01: 판정을 **전체 평균 chars_per_page 에서 페이지별 분포 + K-ICS 절 밀도로** "
                 "바꿨다 — 전체 평균은 '앞은 스캔, 뒤는 감사보고서 텍스트' 문서(흥국생명 FY2024_Q4 등 5건)를 "
                 "영원히 READABLE 로 부르고 처방을 OCR 대신 재수집으로 오라우팅했다. "
                 "SCANNED_SECTION = 문서는 맞는데 해당 절이 이미지 → 처방은 OCR."),
        "_builder": "scripts/build_kics_source_textlayer.py",
        "_status_values": {
            "READABLE": "K-ICS 절이 텍스트로 잡힘 — 판정 가능",
            "BORDERLINE": "K-ICS 절 밀도가 낮음(부분 스캔·표 이미지 혼재) — 사람 확인",
            "SCANNED_SECTION": "문서는 맞는데 K-ICS 절이 이미지 — 처방은 OCR (재수집해도 같은 파일)",
            "UNREADABLE": "문서 전체가 스캔 — 처방은 OCR 또는 텍스트본 재수집",
            "NO_RAW": "그 (회사,분기)에 raw/ · pdf/ 어디에도 PDF 가 없음",
            "ERROR": "PDF 를 열지 못함",
        },
        "generated_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "unreadable_floor_chars_per_page": UNREADABLE_FLOOR,
        "borderline_floor_chars_per_page": BORDERLINE_FLOOR,
        "page_scan_floor_chars": PAGE_SCAN_FLOOR,
        "front_scan_run_min_pages": FRONT_SCAN_RUN_MIN,
        "kics_anchors": list(KICS_ANCHORS),
        "cells": out,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{OUT}: {len(out)} cells in {time.time()-t0:.1f}s  {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
