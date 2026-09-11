# -*- coding: utf-8 -*-
"""KR0080(에이아이에이생명) item23-26(기타요구자본 세부) — 7개 분기 disclosed-zero UPSERT
+ 2024.2Q 는 원문 자체가 빈칸이라 의도적으로 미착수.

## 배경 (TODO_parser_kics.md "KR0080-2326", inbox `20260901T0420Z` 부수관찰)
KR0080 item23-26 이 8개 분기(2023.2Q·2024.2Q·2024.4Q·2025.1Q·2025.2Q·2025.3Q·2025.4Q·2026.1Q)
에서 행 자체가 결측이었다(item17 등 나머지 항목은 8분기 전부 있음 — 순수 item23-26 만 빠짐).
이 회사는 자사/렌더링 전용 PDF(`kics_source_textlayer.json` BORDERLINE 이력)라 텍스트 신뢰
불가 — 분기별 raw 를 fitz 200-400dpi 로 직접 렌더링해 육안 판독했다(스크립트 없이 render
전용, 재현 페이지는 아래 각 분기 주석과 TODO/인박스 답변에 기록).

## 결과: 8분기 중 7분기 disclosed-zero 확정, 1분기(2024.2Q)는 원문이 빈칸이라 SKIP

**적재 7개 분기 (item23=24+25+26=0, 전부 "-" 또는 "0" 으로 인쇄, 경과조치 미적용사라 전=후):**
  2025.3Q  raw p17 (`FY2025_Q3/raw/...pdf`, 33p) — [경과조치 적용전 세부], 해당분기(25.3Q)
    열 "Ⅲ.기타요구자본"+하위1/2/3 = "-"/"-"/"-" 전부 깨끗(본인 분기 원문 직접판독, 같은
    페이지가 2025.1Q/2025.2Q 의 교차확인 소스이기도 함 — 아래 참조).
  2023.2Q  raw p9 (`FY2023_Q2/raw/KR0080_...pdf`, 35p, 텍스트 있음) — "Ⅲ.기타요구자본(1+2+3)"
    행 + 하위 1/2/3 행 전부 "0"/"-" 로 직접 텍스트 추출됨(이 회사 유일하게 텍스트 레이어가
    있는 분기). 소스 각주: "당사는 경과조치를 적용하지 않아 경과조치 전후 금액 및 비율이
    동일함".
  2024.4Q  raw p54 (`FY2024_Q4/raw/...pdf`, 475p 합본 중 정기경영공시 본문 1-112p) —
    [경과조치 적용전 세부] 표, 해당분기(24.4Q)/직전분기(24.3Q)/전전분기(23.4Q) 3열 전부
    "Ⅲ.기타요구자본"+하위1/2/3 = "-"/"-"/"-" 깨끗하게 인쇄(버그 없음). 교차확인: 2025.2Q
    보고서의 "전전분기(24.4Q)" 열(p18, 아래)도 동일하게 "0" 인쇄.
  2025.1Q  raw 자기 분기서는 못 찾았으나(FY2025_Q1 은 32p 전부 이미지렌더로 4-2 절 위치
    특정 불가) 두 개의 후속 분기 보고서가 독립적으로 "0" 을 인쇄: FY2025_Q3/raw p17 "전전
    분기(25.1Q)" 열 + FY2025_Q2/raw p18 "직전분기(25.1Q)" 열, 둘 다 item23-26 = "-"/"0"
    깨끗. (당사자 분기 원문 직접판독은 아니지만 두 독립 후속판이 일치 — 신뢰 충분)
  2025.2Q  raw p18 (`FY2025_Q2/raw/...pdf`, 52p) — [경과조치 적용전 세부], 해당분기(25.2Q)
    열 "Ⅲ.기타요구자본"+1/2/3 = "0"/"0"/"0"/"0" 로 **숫자 0 이 직접 인쇄**(다른 분기들의
    "-" 표기와 달리 이 분기는 아예 0 이라는 숫자로 나옴 — 더 명확). 2026-09-11 이전 세션
    확인치와 페이지번호까지 정확히 일치, 이번 세션에서 render 로 재확인 완료.
  2025.4Q  raw p59 (`FY2025_Q4/raw/...pdf`, 493p 합본 중 정기경영공시 본문 1-115p) —
    **"Ⅲ.기타요구자본(1+2+3)" 부모행 자체는 발행사 템플릿 결함으로 "가.지급여력금액"
    값(30,382/31,331/32,358 백만원, 해당분기/직전/전전 3열 전부)이 잘못 복제 인쇄됨** —
    같은 페이지의 하위 1/2/3 행(=item24/25/26)은 3열 전부 "-" 로 깨끗이 인쇄돼 있어 부모행
    라벨이 스스로 선언한 산식 "(1+2+3)" 과 모순(0+0+0=0 ≠ 30,382). item26(관계회사분) 은
    p60 에서 재확인(3열 전부 "-"). 부모=자식합 산식으로 0 역산 — 발행사 오류를 그대로
    신는 것("가.지급여력금액" 을 item23 에 복붙)이 아니라 표 자신의 산식으로 정정한 것.
    26.1Q 보고서(FY2026_Q1 p18)의 "직전분기(25.4Q)" 열도 동일 결함(30,382) 재현 — 결함이
    이 회사 시스템에 최소 2개 보고서 버전에 걸쳐 있는 것 확인, 단발성 오탈자 아님.
  2026.1Q  raw p18-19 (`FY2026_Q1/raw/...pdf`, 36p) — [경과조치 적용전 세부], 해당분기
    (26.1Q) 열은 부모/자식 전부 "-" 로 깨끗(같은 표의 직전/전전 열(25.4Q/25.3Q)만 위 결함
    재현 — 결함이 열 위치가 아니라 특정 과거분기 캐시에 붙어있는 것으로 추정, 당기 자체는
    매번 깨끗). item26 은 p18 하단이 페이지 경계에 걸려 p18 최하단 90.5-100% 크롭으로 재확인.

**미착수 1개 분기 — 2024.2Q (SKIP, 값 넣지 않음):**
  raw p14 (`FY2024_Q2/raw/...pdf`, 58p, 텍스트 레이어 있음) [경과조치 적용전 세부] 표에서
  "Ⅲ.기타요구자본"+하위1/2 행의 **해당분기(24.2Q) 열만 완전히 빈칸**(대시도 숫자도 없음) —
  같은 행의 직전분기(24.1Q)·전전분기(23.4Q) 열은 "-" 로 정상 인쇄되고, 같은 페이지의 다른
  영(0)값 행(item2 자본증권·item4 자본조정·item6 비지배지분 등)은 해당분기 열도 전부 "-" 로
  정상 인쇄된다 — 즉 이 빈칸은 페이지 전역 렌더링 결함이 아니라 item23-26 행에만, 그것도
  "해당분기" 열에만 있는 국지적 결함이다(400/600dpi 재렌더로 재확인, 흐린 글자 아님 —
  화면상 완전 여백). 이 분기는 이후 어떤 보고서의 이력 열에도 다시 등장하지 않는다
  (분기별 이력 창이 항상 최근 2개 분기까지만 — 24.3Q/24.4Q/25.1Q 보고서 모두 24.2Q 를
  창 밖으로 밀어냄) — 즉 위 2025.4Q 처럼 "부모=자식합" 이나 "다른 보고서의 동일분기 재확인"
  으로 교차검증할 방법이 원천적으로 없다. "틀린 값을 싣느니 빈칸" 원칙에 따라 0 을 추정해
  넣지 않고 미착수로 남긴다.

## 실행
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260912_kr0080_2326_other_capital.py [--apply]
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
MASTER = ROOT / "kics_disclosure.json"
CODE = "KR0080"

LABELS = {
    23: "Ⅲ. 기타 요구자본(1+2+3)",
    24: "1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치",
    25: "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치",
    26: "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치",
}

# quarter -> {item: (값, 값_적용후)}. 전부 disclosed-zero, 경과조치 미적용사라 전=후.
# 2024.2Q 는 의도적으로 DATA 에 없음(원문 빈칸, SKIP — docstring 참조).
DATA: dict[str, dict[int, tuple[float, float | None]]] = {
    "2023.2Q": {23: (0.0, 0.0), 24: (0.0, 0.0), 25: (0.0, 0.0), 26: (0.0, 0.0)},
    "2024.4Q": {23: (0.0, 0.0), 24: (0.0, 0.0), 25: (0.0, 0.0), 26: (0.0, 0.0)},
    "2025.1Q": {23: (0.0, 0.0), 24: (0.0, 0.0), 25: (0.0, 0.0), 26: (0.0, 0.0)},
    "2025.2Q": {23: (0.0, 0.0), 24: (0.0, 0.0), 25: (0.0, 0.0), 26: (0.0, 0.0)},
    "2025.3Q": {23: (0.0, 0.0), 24: (0.0, 0.0), 25: (0.0, 0.0), 26: (0.0, 0.0)},
    "2025.4Q": {23: (0.0, 0.0), 24: (0.0, 0.0), 25: (0.0, 0.0), 26: (0.0, 0.0)},
    "2026.1Q": {23: (0.0, 0.0), 24: (0.0, 0.0), 25: (0.0, 0.0), 26: (0.0, 0.0)},
}

SKIPPED = {
    "2024.2Q": "raw p14 [경과조치 적용전 세부] 표에서 item23-26 행의 '해당분기(24.2Q)' 열만 "
               "완전 공백(대시도 숫자도 없음) — 같은 행의 직전/전전분기 열은 '-', 같은 페이지 "
               "다른 0값 행의 해당분기 열은 전부 '-' 로 정상 인쇄돼 이 행만의 국지적 결함. "
               "3분기 롤링 이력창 밖이라(24.3Q/24.4Q/25.1Q 보고서 어디에도 24.2Q 재등장 없음) "
               "교차검증 불가 — 0 추정 대신 미착수.",
}


def census(rows):
    combos = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])) for r in rows}
    filled = sum(1 for r in rows for f in ("값", "값_적용후") if r.get(f) is not None)
    return len(rows), len(combos), filled


def main() -> int:
    apply = "--apply" in sys.argv
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    b = census(rows)
    print(f"before: rows={b[0]} combos={b[1]} filled={b[2]}")
    idx = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r for r in rows}
    meta = None
    for r in rows:
        if r["원보험사코드"] == CODE:
            meta = (r["원수사명"], r.get("티커"), r["생손보여부"])
            break
    if meta is None:
        print(f"ABORT: {CODE} 행이 마스터에 전혀 없다"); return 2
    nm, tk, seg = meta

    print(f"\nSKIP (미착수): {list(SKIPPED)} — 사유는 파일 docstring 참조")

    n_ins = n_upd = 0
    for q, items in DATA.items():
        # item23 은 반드시 item24+25+26 과 일치해야 한다(부모=자식합, 표 자신의 산식).
        s = items[24][0] + items[25][0] + items[26][0]
        if abs(items[23][0] - s) > 0.01:
            print(f"  ABORT {q}: item23({items[23][0]}) != 24+25+26({s})"); return 2
        for it in sorted(items):
            cur = idx.get((CODE, q, str(it)))
            if cur is None:
                n_ins += 1
                continue
            cv = cur.get("값")
            if cv is not None and abs(float(cv) - items[it][0]) > 1.0:
                print(f"  ABORT {q} item{it}: 기존값 {cv!r} 이 판독값 {items[it][0]} 과 "
                      f"1억 넘게 다르다 — 손대지 않는다"); return 2
            if cv is not None:
                print(f"  (이미 존재, 무변경) {q} item{it}: {cv}")
                n_upd += 0  # no-op, existing correct value
    print(f"\nINSERT {n_ins}칸(신규 행)")
    if not apply:
        print("(dry-run) 반영하려면 --apply")
        return 0

    for q, items in DATA.items():
        anchor = idx.get((CODE, q, "22")) or idx.get((CODE, q, "17"))
        pos = rows.index(anchor) + 1 if anchor is not None else len(rows)
        for it in sorted(items):
            pre, post = items[it]
            cur = idx.get((CODE, q, str(it)))
            if cur is not None:
                continue  # already present and value-checked above; don't touch
            row = {"원보험사코드": CODE, "원수사명": nm, "티커": tk, "생손보여부": seg,
                   "항목번호": it, "항목명": LABELS[it], "공시분기": q,
                   "값": pre, "값_적용후": post}
            rows.insert(pos, row); pos += 1
            idx[(CODE, q, str(it))] = row

    a = census(rows)
    print(f"after : rows={a[0]} combos={a[1]} filled={a[2]}  (+{a[0] - b[0]}행 +{a[2] - b[2]}셀)")
    if a[0] - b[0] != n_ins or a[1] - b[1] != n_ins:
        print("  ABORT: 행/콤보 증가가 예상과 다르다"); return 2

    bak = MASTER.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_kr0080_2326")
    shutil.copy2(MASTER, bak)
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 완료. 백업: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
