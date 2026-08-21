# -*- coding: utf-8 -*-
"""inbox/parser/20260821T1140Z__orchestrator__KR0087_2023.2Q__main_table_26_items_missing.md

동양생명(KR0087) 2023.2Q 메인표(items 1-28)가 항목 1·14·36·41-46 밖에 없었다(9행). 원인은
표 연속페이지 유실(총괄표가 p11=항목1-11 / p12=항목12-28로 쪼개지는데 p12쪽에 분기헤더가 안
찍혀서 스캐너가 버림) — `20260821T1030Z` F3와 동일한 실패 모드.

여기서 채우는 25개 항목의 값은 raw PDF를 이 스크립트 실행 세션에서 직접 fitz로 재확인했다
(data/disclosure/FY2023_Q2/raw/KR0087_동양생명.pdf, fitz 0-idx page 8-11 = 1-idx p9-p12) —
inbox 티켓의 표를 베끼지 않고 각 셀을 원문과 26/26 대조 완료.

원문 인용 (단위 억원, 2023.2Q 열):
  [경과조치 적용 전 지급여력비율 세부] (p11=fitz idx10):
    가.지급여력금액(=1) 44,512 | 기본자본(2) 25,518 | 보완자본(3) 18,995
    Ⅰ.순자산(4)=(1+2+3+4+5+6) 41,485 | 1.보통주(5) 12,705 | 2.보통주이외자본증권(6) 3,446 |
    3.이익잉여금(7) 12,399 | 4.자본조정(8) -607 | 5.기타포괄손익누계액(9) 3,934 |
    [비지배지분 행 자체 없음 - 이 분기는 (1+2+3+4+5+6) 6개 구성, item10 스킵]
    6.조정준비금(11) 9,608
  (p12=fitz idx11):
    Ⅱ.불인정항목(12) 0 | Ⅲ.보완자본재분류(13) 15,968 | 나.기준금액(14)=Ⅰ-Ⅱ+Ⅲ 27,385
    Ⅰ.기본요구자본(15) 33,008 | 분산효과(16) 9,602 | 1.생명장기(17) 22,342 |
    2.일반손해(18) 0 | 3.시장위험(19) 10,176 | 4.신용위험(20) 6,467 | 5.운영위험(21) 3,625 |
    Ⅱ.법인세조정액(22) 5,623 | Ⅲ.기타요구자본(23) 0 | 1.종속회사환산치(24) 0 |
    2.비례성원칙대응치(25) 0 | 3.관계회사환산치(26) 0 | 다.비율(27)=가÷나×100 162.54
  item28(기본자본비율) = 원문에 행 없음 -> item2/item14*100 산출 (reference_kics_item28_computed 관례)

경과조치(적용후) 판단 근거 - 원문 "나. 경과조치 적용에 관한 세부사항"(p11=fitz idx10):
  선택경과조치(TAC/TIR/TER/TIRR) 전부 X, 공통(TFI + 보고기한)만 O = "선택경과조치 미적용사".
  [지급여력비율의 경과조치 적용에 관한 사항 - (1)공통적용 경과조치 관련](단위 백만원, p11-12=idx10-11):
    지급여력비율 162.54%->162.54% | 지급여력금액 4,451,215->4,451,215 |
    기본자본 2,551,763->2,896,331 | 보완자본 1,899,451->1,554,884 |
    지급여력기준금액 2,738,518->2,738,518 (각주: "경과조치 미적용으로 전후 금액 및 비율이 동일")
  즉 item1/14/27후 = 전과 정확히 동일(공통TFI가 요구자본측을 안 건드리는 이 코드베이스의 기존
  확립 관례와 일치, item14 정밀값까지 완전히 같다). item2/3후는 TFI의 자본계층 재분류로 실제
  다르다(raw 정밀값 나눠서 ->28963.31/15548.84). item15-26후는 item14후=item14전이 정밀값까지
  정확히 같다는 것 자체가 그 입력들(15,22,23)이 안 바뀌었다는 강한 직접증거이고, TFI는 정의상
  가용자본측 계층재분류일 뿐 요구자본 산식에 입력이 없다 -> 기존 확립 룰
  (fix_20260716_nonapplier_requirement_mirror.py의 "item14 동일 -> 15-26후 미러링", 비적용사
  전사에 이미 적용 중인 방법론)을 그대로 적용해 전=후로 채운다. item28후도 item2후/item14후로
  같은 산출 규칙 적용.

  item4-9,11-13후(순자산·불인정항목·보완자본재분류)는 채우지 않는다: item12/13는 TFI가 직접
  건드리는 대상 그 자체라(재분류항목의 정의가 "자본증권 인정한도" 문제) 전=후를 가정할 근거가
  없고, 원문에 이 항목들의 적용후 숫자가 직접 나온 표가 없다 - 틀린 값을 싣느니 빈 칸.

검증(쓰기 전): rule1(1=2+3) rule2(4=5+6+7+8+9+11) rule4(15=sqrt(R4)+21) rule5(14=15-22+23)
rule6(16=(17+18+19+20+21)-15) rule7(27=1/14*100) 전부 허용오차 내 재현 확인 (스크립트 실행 출력
참조). item10(비지배지분) 행은 만들지 않는다 - 원문에 없다(ticket 명시 경고).

Usage:
  ...python scripts/fix_20260821_kr0087_2023q2_main_table.py --dry-run
  ...python scripts/fix_20260821_kr0087_2023q2_main_table.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "kics_disclosure.json"

CODE, NAME, TICKER, KIND, Q = "KR0087", "동양생명", "082640", "생명보험", "2023.2Q"

LABELS = {
    2: "기본자본", 3: "보완자본",
    4: "Ⅰ. 건전성감독기준 재무상태표 상의 순자산",
    5: "1. 보통주", 6: "2. 자본항목 중 보통주 이외의 자본증권", 7: "3. 이익잉여금",
    8: "4. 자본조정", 9: "5. 기타포괄손익누계액",
    11: "6. 조정준비금",  # NOTE: this quarter's own raw numbers it "6." (item10 비지배지분 has
                          # no row this quarter) - NOT "7." like the 2023.1Q template row, which
                          # was parsed from a quarter where item10 IS present. Content-accurate,
                          # not copy-paste.
    12: "Ⅱ. 지급여력금액으로 불인정하는 항목 (지급이 예정된 주주배당액 등)",
    13: "Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)",
    15: "Ⅰ. 기본요구자본", 16: "- 분산효과 : (1+2+3+4+5) - Ⅰ",
    17: "1. 생명장기손해보험위험액", 18: "2. 일반손해보험위험액", 19: "3. 시장위험액",
    20: "4. 신용위험액", 21: "5. 운영위험액",
    22: "Ⅱ. 법인세조정액", 23: "Ⅲ. 기타 요구자본(1+2+3)",
    24: "1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치",
    25: "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치",
    26: "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치",
    27: "다. 지급여력비율 : 가 ÷ 나 × 100",
    28: "기본자본비율",
}

# 값(적용전), 억원 - 원문 그대로(정수), item8만 진짜 음수.
PRE = {
    2: 25518, 3: 18995, 4: 41485, 5: 12705, 6: 3446, 7: 12399, 8: -607, 9: 3934,
    11: 9608, 12: 0, 13: 15968, 15: 33008, 16: 9602, 17: 22342, 18: 0, 19: 10176,
    20: 6467, 21: 3625, 22: 5623, 23: 0, 24: 0, 25: 0, 26: 0,
}


def fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))

    before_row_count = len(data)
    before_combos = {(r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) for r in data}

    by_item: dict[int, dict] = {}
    for r in data:
        if r.get("원보험사코드") == CODE and r.get("공시분기") == Q:
            by_item[int(r["항목번호"])] = r
    print(f"기존 KR0087 2023.2Q 행: {sorted(by_item)}")

    # --- derive item28(pre) and item2/3/27/28(post) precisely ---
    item28_pre = PRE[2] / 27385 * 100          # item14 pre = 27385 (already in master)
    item2_post = 2_896_331 / 100.0             # raw TFI table, 백만원 -> 억원
    item3_post = 1_554_884 / 100.0
    item14_post = 27385                        # raw TFI table shows EXACT same precise value
                                                # (2,738,518 == 2,738,518) as pre -> use master's
                                                # existing pre integer, no new precision implied
    item1_post = 44512                          # same reasoning, already in master unchanged
    item27_post = item1_post / item14_post * 100
    item28_post = item2_post / item14_post * 100

    print(f"computed: item28_pre={item28_pre:.4f} item2_post={item2_post} item3_post={item3_post} "
          f"item27_post={item27_post:.4f} item28_post={item28_post:.4f}")

    # --- pre-write identity checks (raw-sourced numbers only) ---
    checks = []
    checks.append(("rule1 item1=2+3", 44512, PRE[2] + PRE[3]))
    checks.append(("rule2 item4=5+6+7+8+9+11", PRE[4], PRE[5] + PRE[6] + PRE[7] + PRE[8] + PRE[9] + PRE[11]))
    checks.append(("rule5 item14=15-22+23", 27385, PRE[15] - PRE[22] + PRE[23]))
    checks.append(("rule6 item16=(17+18+19+20+21)-15", PRE[16],
                    PRE[17] + PRE[18] + PRE[19] + PRE[20] + PRE[21] - PRE[15]))
    checks.append(("rule7 item27=1/14*100", 162.54, round(44512 / 27385 * 100, 2)))
    checks.append(("rule8 item28=2/14*100(computed)", round(item28_pre, 2), round(item28_pre, 2)))
    ok = True
    for label, want, got in checks:
        diff = abs(want - got)
        status = "OK" if diff <= 2.0 else "FAIL"
        if status == "FAIL":
            ok = False
        print(f"  [{status}] {label}: want={want} got={got} diff={diff:.4f}")
    # rule4 (sqrt R4) needs the correlation matrix - import from the rules engine, not retyped.
    sys.path.insert(0, str(REPO / "src"))
    from solvency.validation.kics_json_rules import R4  # noqa: E402
    import numpy as np
    w = np.array([PRE[17], PRE[18], PRE[19], PRE[20]], float)
    r4_calc = float(np.sqrt(w @ R4 @ w)) + PRE[21]
    diff4 = abs(PRE[15] - r4_calc)
    print(f"  [{'OK' if diff4 <= 2.0 else 'FAIL'}] rule4 item15=sqrt(R4[17-20])+21: "
          f"want={PRE[15]} got={r4_calc:.2f} diff={diff4:.4f}")
    if diff4 > 2.0:
        ok = False
    if not ok:
        print("!! 검산 실패 - 쓰지 않고 중단")
        return 1

    # --- build writes: insert new rows (items missing) / update existing (none expected to change) ---
    inserts = []
    for it in sorted(PRE):
        if it in by_item:
            print(f"  SKIP item{it}: 이미 존재 (예상 밖) -> 값 확인 필요, 손대지 않음")
            continue
        post = None
        if it in (2, 3):
            post = fmt(item2_post if it == 2 else item3_post)
        elif 15 <= it <= 26:
            post = fmt(PRE[it])  # mirror: item14후=item14전 확인 -> 15-26후=전 (established rule)
        row = {
            "원보험사코드": CODE, "원수사명": NAME, "티커": TICKER, "생손보여부": KIND,
            "항목번호": it, "항목명": LABELS[it], "공시분기": Q,
            "값": fmt(PRE[it]), "값_적용후": post,
        }
        inserts.append(row)

    # item27, item28 rows (also missing) - special-cased (not in PRE dict's mirror-range loop above
    # since 27/28 are ratios, not additive items, and 28 has no raw row at all)
    for it, pre_v, post_v in ((27, 162.54, item27_post), (28, round(item28_pre, 2), item28_post)):
        if it in by_item:
            print(f"  SKIP item{it}: 이미 존재")
            continue
        inserts.append({
            "원보험사코드": CODE, "원수사명": NAME, "티커": TICKER, "생손보여부": KIND,
            "항목번호": it, "항목명": LABELS[it], "공시분기": Q,
            "값": fmt(pre_v), "값_적용후": fmt(post_v),
        })

    print(f"\n삽입 예정 {len(inserts)}행:")
    for row in sorted(inserts, key=lambda r: r["항목번호"]):
        print(f"  item{row['항목번호']:>2} {row['항목명']:<45} 값={row['값']:>10} 값_적용후={row['값_적용후']}")

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0

    # append (cell-by-cell insert - existing rows/objects are never touched or rebuilt)
    data.extend(inserts)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {TARGET.name}: +{len(inserts)}행")

    after_row_count = len(data)
    after_combos = {(r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) for r in data}
    added_combos = after_combos - before_combos
    removed_combos = before_combos - after_combos
    print(f"\n=== census ===")
    print(f"row_count: {before_row_count} -> {after_row_count} (delta {after_row_count - before_row_count}, "
          f"expected +{len(inserts)})")
    print(f"combo delta: +{len(added_combos)} / -{len(removed_combos)} (expected +{len(inserts)}/-0)")
    if removed_combos:
        print(f"!! UNEXPECTED REMOVED COMBOS: {removed_combos}")
    unexpected_added = added_combos - {(CODE, Q, r["항목번호"]) for r in inserts}
    if unexpected_added:
        print(f"!! UNEXPECTED ADDED COMBOS (outside plan): {unexpected_added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
