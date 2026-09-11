# -*- coding: utf-8 -*-
"""티켓 `inbox/parser/20260831T0705Z__orchestrator__MULTI_2026.2Q__item48_label_confusion.md`
REOPEN (orchestrator, 2026-09-11) — 2026.2Q item48(보완자본 한도, 적용전) 이 item3(보완자본)
값으로 오염된 잔여 4셀 정정.

## 근거 (셀 단위)
값_적용후 는 이미 정답(각 사 TFI 표 자체가 pre==post 로 인쇄 — regulatory 한도는 경과조치
적용전 SCR 기준 고정값이라 표의 두 컬럼이 같은 숫자를 찍는다)이고, 값(적용전)만 item3 로
오염돼 있다 — orchestrator 재확인 답변에 이미 넷 다 명시됨. 이번 세션에서 **두 개의 독립
추출 경로**로 재확인했다(둘 다 raw PDF 직접 판독, MD 경유 아님):

  1. `scripts/fix_20260821_tier2_limit_lines.py::extract_tier2()` (fitz 텍스트 스트림,
     라벨 EXACT-match) 를 각 사 2026.2Q raw PDF 에 직접 호출 -> found[48] 이 넷 다
     (pre_raw, post_raw) 를 **같은 숫자**로 반환(그 자체가 원문의 pre==post 정합성 증거).
  2. `md_inbox/FY2026_Q2/<KR>_*.md` 의 "(1) 공통적용 경과조치" 표 grep(`보완자본` 라인) —
     동일 숫자 확인.

  KR0003 raw 1,055,550백만 (md L372) / extract_tier2 (1055550.0,1055550.0) -> 10555.50억
  KR0011 raw 5,754,942백만 (md L376) / extract_tier2 (5754942.0,5754942.0) -> 57549.42억
  KR0029 raw   138,983백만 (md L525) / extract_tier2  (138983.0, 138983.0) -> 1389.83억
  KR0094 raw (MD 에 표 없음, docling 누락) / extract_tier2 (2688072.0,2688072.0) -> 26880.72억
    (KR0094 은 md_inbox 에 "(1)공통적용경과조치" 표 자체가 없다 -- KR0094 md 파일 grep 결과
    47/48/49 라벨 라인 0건, 이번 세션에서도 fitz 직접호출로만 확인. TODO_parser_kics.md 2026-09-01
    항목(현재는 docs/todo_archive_parser_kics.md 로 이동)이 같은 값을 이미 26880.72 로 남겨 둠.)

item14(적용전)x50% 검산: 21111x0.5=10555.50 / 115099x0.5=57549.50(diff 0.08, TIER2_LIMIT_RATIO
공식오차 이내) / 2780x0.5=1390.00(diff 0.17, item14 정수반올림 오차) / 53761x0.5=26880.50
(diff 0.22, 동일) -- 전부 회사 자체 반올림오차(<1) 이내, item3 값과는 수천~수만억 단위로
다르다(예: KR0003 item3=28741 vs 정답 10555.50, diff 18185.5) -- "오염" 판정의 근거.

KR0083 2026.2Q(item48=item3=7713)는 item14x50%=7713 과 이미 일치하는 정당한 우연 일치라
이 패치의 대상이 아니다(원 티켓 명시) -- 이 스크립트는 KR0083 을 건드리지 않는다.

## 오염 주입점 조사 (요청 (b))
git blame 으로 4셀 전부 커밋 8f5e3b8("data(2026.2Q): 정기경영공시 39사 전원 적재", 2026-09-01
04:56, 단일 커밋)에서 도입된 것을 확인했다. 그러나 **현재 저장소의 두 정본 추출기 중 어느 쪽도
이 버그를 재현하지 않는다** -- 위 (1)의 `extract_tier2()` 도, `fill_tfi_table_to_disclosure.py`
의 MD-테이블 추출도, 지금 다시 돌리면 정답을 낸다(이 스크립트 docstring 상단 근거 참조). 즉 이
값을 쓴 정확한 스크립트는 그 커밋의 세션 내부에서 한 번 쓰이고 이후 코드가 고쳐졌거나(버그가
이미 수정된 흔적 -- 회귀는 아님) 세션 로그에만 존재하던 수기 patch 였을 가능성이 높다 -- 8f5e3b8
은 그 세션의 여러 스크립트 실행을 한 커밋으로 묶은 것이라 blame 이상으로는 특정이 불가능했다.
대신 **현재 활성 경로의 재발 방지**로 대응한다: `fill_tfi_table_to_disclosure.py` 의 item48
자체검산이 `item14_pre_f is not None` 조건에서만 발동해(그 외엔 무검증 통과) fail-open 이던
gap 을 이 티켓과 같은 세션에서 fail-closed 로 고쳤다(별도 diff, 이 스크립트가 아니라
`fill_tfi_table_to_disclosure.py` 자체를 수정) -- item14 가 아직 안 실려 있으면 item48 신규
행은 더 이상 무검증으로 써지지 않고 selfcheck_blocked 로 남는다.

## 실행
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260911_item48_item3_contamination.py [--apply]
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
Q = "2026.2Q"

# code -> (contaminated 값 that must currently be present, corrected 값)
FIXES: dict[str, tuple[str, str]] = {
    "KR0003": ("28741", "10555.5"),
    "KR0011": ("124792", "57549.42"),
    "KR0029": ("754", "1389.83"),
    "KR0094": ("59367", "26880.72"),
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

    targets = []
    for r in rows:
        if r.get("원보험사코드") in FIXES and r.get("공시분기") == Q and int(r.get("항목번호", -1)) == 48:
            targets.append(r)

    if len(targets) != len(FIXES):
        print(f"ABORT: item48/{Q} 행을 {len(targets)}개 찾음(기대 {len(FIXES)}) -- 코드 목록 재확인 필요")
        return 2

    changes = []
    for r in targets:
        code = r["원보험사코드"]
        expected_old, new_val = FIXES[code]
        cur = r.get("값")
        if str(cur) != expected_old:
            print(f"ABORT {code}: 기존값 {cur!r} 이 예상한 오염값 {expected_old!r} 과 다르다 "
                  f"-- 다른 세션이 이미 건드렸을 수 있다, 손대지 않는다")
            return 2
        changes.append((r, cur, new_val))

    print(f"\n{len(changes)}칸 정정 예정:")
    for r, old, new in changes:
        print(f"  {r['원보험사코드']} {Q} item48: 값 {old!r} -> {new!r}  (값_적용후={r.get('값_적용후')!r}, 무변경)")

    if not apply:
        print("\n(dry-run) 반영하려면 --apply")
        return 0

    bak = MASTER.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_item48item3fix")
    shutil.copy2(MASTER, bak)

    for r, old, new in changes:
        r["값"] = new

    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    a = census(rows)
    print(f"\nafter : rows={a[0]} combos={a[1]} filled={a[2]}  (행수 불변 기대: {a[0] == b[0]}, "
          f"콤보 불변 기대: {a[1] == b[1]})")
    print(f"저장 완료. 백업: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
