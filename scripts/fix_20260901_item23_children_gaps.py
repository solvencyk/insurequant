# -*- coding: utf-8 -*-
"""item23(기타 요구자본) 자식 칸 2건 수정 — 원문 확증 건만.

배경: 2026-09-01 라운드에서 `OTHER_CAPITAL_CHILDREN_SUM` 게이트가 흥국생명 2023.4Q 1건만
잡길래 전수로 다시 쟀다(item23 vs item24+25+26, 전·후 양컬럼). 불일치 29건 중 28건은
±1 반올림이었고, **게이트가 아예 못 보는 사각이 따로 있었다** — 자식 칸이 `None` 이거나
행 자체가 없으면 합계 룰이 SKIP 된다(이 저장소의 'SKIP-on-missing = 검증무력화' 사각).
SKIP 되는 버킷 347건 중 결측이 실제 gap 을 만드는 것이 33건이다.

33건 중 32건은 [적용후] 자식 3개가 통째로 비는 기존 축(`적용후 세부결측`)이라 여기서
다루지 않는다. 아래 2건만 **원문에 값이 인쇄돼 있는데 마스터가 틀린** 추출갭이다.

1) 메리츠화재해상보험(KR0001) 2026.1Q — item25 **행 자체가 없다**(셀 null 이 아니다)
   data/disclosure/FY2026_Q1/parsed/KR0001_메리츠화재해상보험.md L362-365:
       | Ⅲ. 기타 요구자본(1+2+3)                          |  57 |  50 |  46 |
       | 1. 업권별 ... 종속회사의 요구자본 환산치           |   0 |   0 |   0 |
       | 2. 비례성원칙을 적용한 종속회사의 요구 자본 대응치  |  57 |  50 |  46 |
       | 3. 업권별 ... 관계회사의 요구자본 환산치           |   0 |   0 |   0 |
   라벨에 "요구 자본" 처럼 공백이 끼어 매칭이 빗나간 것으로 보인다(2026.2Q 는 정상 추출됨).
   이 회사는 item25 가 13분기 내내 있고 2026.1Q 한 분기만 없다 = SANDWICHED 추출갭.
   값_적용후: 이 필링에는 적용후 세부표가 없고(단일 표 L336 `[경과조치 적용 전 ...]`),
   형제 item23/24/26 의 값_적용후 가 이미 전값과 같게 채워져 있다(57/0/0). 기타요구자본은
   경과조치 대상이 아니라 후=전이 정의다. 빠진 형제에 **같은 처리**를 적용한다.

2) 흥국생명보험(KR0071) 2023.1Q — item24 가 부모값 복사(대시 오독)
   data/disclosure/FY2023_Q1/parsed/KR0071_흥국생명보험_amended.md L135-138:
       | Ⅲ . 기타 요구자본 (1+2+3)        | 8,534 | - | - |
       | 1. ... 종속회사의 요구자본 환산치 |   -   | - | - |
       | 2. 비례성원칙 ...                |   -   | - | - |
       | 3. ... 관계회사의 요구자본 환산치 | 8,534 | - | - |
   → item24 = 0 (현재 8534). 같은 회사 2023.3Q·2023.4Q 에서 이미 두 번 고친 것과 같은
     지문이다(`fix_20260821_kr0071_item24_fabricated_dash.py`, 그리고 2026-09-01 kics 라운드).
     **인접 분기 스윕이 두 번 다 이 분기를 놓쳤다.**

실행:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260901_item23_children_gaps.py [--apply]
"""
from __future__ import annotations
import json, sys, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
MASTER = ROOT / "kics_disclosure.json"


def census(rows):
    combos = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])) for r in rows}
    filled = sum(1 for r in rows for f in ("값", "값_적용후") if r.get(f) is not None)
    return len(rows), len(combos), filled


def find(rows, code, q, item):
    return [r for r in rows
            if r["원보험사코드"] == code and r["공시분기"] == q and str(r["항목번호"]) == str(item)]


def main() -> int:
    apply = "--apply" in sys.argv
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    b_rows, b_combos, b_filled = census(rows)
    print(f"before: rows={b_rows} combos={b_combos} filled_cells={b_filled}")

    # --- 1) 메리츠 2026.1Q item25 행 삽입 (템플릿 = 같은 회사 2026.2Q item25 행) --------
    if find(rows, "KR0001", "2026.1Q", 25):
        print("  ABORT: KR0001 2026.1Q item25 행이 이미 있다 — 누가 먼저 고쳤다")
        return 2
    tmpl = find(rows, "KR0001", "2026.2Q", 25)
    if len(tmpl) != 1:
        print(f"  ABORT: 템플릿(KR0001 2026.2Q item25) 행이 {len(tmpl)}개")
        return 2
    anchor = find(rows, "KR0001", "2026.1Q", 24)
    if len(anchor) != 1:
        print(f"  ABORT: 삽입 기준(KR0001 2026.1Q item24) 행이 {len(anchor)}개")
        return 2
    new = dict(tmpl[0])
    new["공시분기"] = "2026.1Q"
    new["값"] = 57.0
    new["값_적용후"] = 57.0
    print(f"  INSERT KR0001 2026.1Q item25 = 57.0 / 적용후 57.0   [{new['항목명']}]")

    # --- 2) 흥국생명 2023.1Q item24 = 0 --------------------------------------------
    tgt = find(rows, "KR0071", "2023.1Q", 24)
    if len(tgt) != 1:
        print(f"  ABORT: KR0071 2023.1Q item24 행이 {len(tgt)}개")
        return 2
    cur = tgt[0].get("값")
    if cur is None or abs(float(str(cur).replace(",", "")) - 8534.0) > 0.01:
        print(f"  ABORT: KR0071 2023.1Q item24 현재값={cur!r} 기대=8534 — 전제가 틀렸다")
        return 2
    print(f"  EDIT   KR0071 2023.1Q item24.값: {cur} -> 0.0   [{tgt[0]['항목명']}]")

    if not apply:
        print("\n(dry-run) 반영하려면 --apply")
        return 0

    rows.insert(rows.index(anchor[0]) + 1, new)
    tgt[0]["값"] = 0.0

    a_rows, a_combos, a_filled = census(rows)
    print(f"after : rows={a_rows} combos={a_combos} filled_cells={a_filled}")
    if (a_rows, a_combos, a_filled) != (b_rows + 1, b_combos + 1, b_filled + 2):
        print(f"  ABORT: census 변화가 예상(+1행 +1콤보 +2셀)과 다르다 — 저장하지 않는다")
        return 2

    # 항등식 재검산
    for code, q in (("KR0001", "2026.1Q"), ("KR0071", "2023.1Q")):
        for fld, lab in (("값", "전"), ("값_적용후", "후")):
            p = find(rows, code, q, 23)
            if not p or p[0].get(fld) is None:
                continue
            pv = float(p[0][fld])
            ch = [find(rows, code, q, i) for i in (24, 25, 26)]
            vals = [float(c[0][fld]) for c in ch if c and c[0].get(fld) is not None]
            if len(vals) != 3:
                print(f"  검산 {code} {q}[{lab}]: 자식 {len(vals)}/3 — 여전히 SKIP 상태")
                continue
            ok = "OK" if abs(sum(vals) - pv) <= 0.01 else "*** 안 닫힘 ***"
            print(f"  검산 {code} {q}[{lab}]: item23={pv:,.0f} vs 자식합={sum(vals):,.0f}  {ok}")

    bak = MASTER.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_item23children")
    shutil.copy2(MASTER, bak)
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 완료. 백업: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
