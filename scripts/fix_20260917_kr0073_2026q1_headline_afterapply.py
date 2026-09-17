# -*- coding: utf-8 -*-
"""KR0073(교보생명보험) 2026.1Q — item1/14/27 값_적용후(경과조치 후) 정정.

## 배경
FSS 보도자료(`R26090720.pdf`, '26.6월말 기준 보험회사 지급여력비율 현황, 2026.9.17
조간)와 `kics_disclosure.json`을 항목27(지급여력비율) 기준 38개사(국내 공시대상만,
외국 재보험지점 14개사·예별손보 제외) × 2개분기(26.1Q/26.2Q) × 전/후 152칸 대조 중
발견. 나머지는 억원 단위 반올림 오차(<0.3%p, item1/item14 재계산 특유의 설계상
오차)였지만 KR0073 2026.1Q 경과조치 후만 2.83%p 어긋남(진짜 오류).

## 원인
`data/disclosure/FY2026_Q1/parsed/KR0073_교보생명보험.md` (원본 26.1Q 공시) 당시
[지급여력비율 총괄] 표 "해당분기(26.1Q)" 경과조치 후: 지급여력비율 214.23 /
지급여력금액(A) 149,556 / 지급여력기준금액(B) 69,811 (억원)이 그대로 마스터에 적재됨.

이후 `data/disclosure/FY2026_Q2/parsed/KR0073_교보생명보험.md`(26.2Q 공시)의 같은
표 "직전분기(26.1Q)" 컬럼이 이를 정정: 경과조치 후 지급여력비율 211.39 /
지급여력금액(A) 149,557 / 지급여력기준금액(B) 70,749. 경과조치 전(값) 컬럼은
이 정정을 이미 반영(160.41 등)했는데 경과조치 후(값_적용후) 컬럼만 정정 전 옛
값에 남아있었다 — `reference_transition_after_capture` 메모에 있는 "적용후 컬럼
파싱 불안정(flip-flop)" 사각의 구체 사례.

## 교차검증 (2개 독립 소스 일치)
  FSS 보도자료 붙임1: 교보생명 경과조치 후 '26.3월말 211.4 (반올림)
  KR0073 26.2Q 공시 [지급여력비율 총괄] 직전분기(26.1Q) 경과조치 후: 211.39
  항등식: item1_적용후(149557) / item14_적용후(70749) x 100 = 211.39 (재계산 일치)

## 부수효과 — R5_기준금액(item14=item15-item22+item23) 적용후 항등식이 깨진다
item14_적용후만 정정치로 바뀌고 그 하위 세부항목(item15/22/23_적용후)은 26.1Q
원본 공시의 미정정 값 그대로다 — 26.2Q 공시가 총괄표 비교컬럼만 정정하고 세부
항목의 정정된 비교치는 공시하지 않기 때문(당분기 전용 ①②③ 유형별 표만 있음).
파생값으로 세부항목을 갈아끼우지 않는다(발행사 표 불일치는 있는 그대로 둔다) —
대신 이 잔차(938.25)를 `scripts/validate_kics_disclosure.py` 의
`AFTER_IDENT_ISSUER_INCONSISTENT` 등재부에 박제해 매 실행 재검산하도록 했다
(owner 2026-09-17 승인). `validate_data_contract.py` 도 같은 함수를 공유해 동일하게
반영됨.

## 실행
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260917_kr0073_2026q1_headline_afterapply.py [--apply]
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
CODE = "KR0073"
QUARTER = "2026.1Q"

# item -> (기존 값_적용후로 기대되는 값(guard), 새 값_적용후)
FIXES: dict[int, tuple[float, float]] = {
    1: (149556, 149557),
    14: (69811, 70749),
    27: (214.23, 211.39),
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

    targets = {}
    for it, (expect_old, new_val) in FIXES.items():
        cur = idx.get((CODE, QUARTER, str(it)))
        if cur is None:
            print(f"ABORT: {CODE} {QUARTER} item{it} 행이 마스터에 없다"); return 2
        old = cur.get("값_적용후")
        if old is None or abs(float(old) - expect_old) > 0.01:
            print(f"ABORT item{it}: 기존 값_적용후={old!r} 이 예상({expect_old}) 과 다르다 "
                  f"— 이미 고쳐졌거나 가정이 틀렸을 수 있다, 손대지 않는다")
            return 2
        targets[it] = cur

    new1 = FIXES[1][1]
    new14 = FIXES[14][1]
    new27 = FIXES[27][1]
    recompute = new1 / new14 * 100
    print(f"항등식 재계산: item1_적용후({new1}) / item14_적용후({new14}) x 100 "
          f"= {recompute:.4f} vs 신규 item27_적용후({new27})")
    if abs(recompute - new27) > 0.05:
        print("  ABORT: 항등식이 안 닫힌다"); return 2
    print("  OK")

    for it, cur in targets.items():
        old = cur["값_적용후"]
        new_val = FIXES[it][1]
        print(f"  UPDATE {QUARTER} item{it} 값_적용후: {old!r} -> {new_val!r}")

    if not apply:
        print("\n(dry-run) 반영하려면 --apply")
        return 0

    for it, cur in targets.items():
        cur["값_적용후"] = FIXES[it][1]

    a = census(rows)
    print(f"after : rows={a[0]} combos={a[1]} filled={a[2]}  "
          f"(행 증감 {a[0] - b[0]}, 셀 증감 {a[2] - b[2]})")
    if a[0] != b[0] or a[1] != b[1]:
        print("  ABORT: 행/콤보 수가 바뀌면 안 된다(셀 값만 수정하는 스크립트)"); return 2

    bak = MASTER.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_kr0073_2026q1headline")
    shutil.copy2(MASTER, bak)
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 완료. 백업: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
