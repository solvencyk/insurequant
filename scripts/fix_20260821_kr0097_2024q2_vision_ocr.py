# -*- coding: utf-8 -*-
"""inbox/parser/20260821T1230Z__orchestrator__KR0097_2024.2Q__scanned_pdf_read_by_vision.md

하나생명(KR0097) 2024.2Q raw는 fitz get_text()가 0자를 반환하는 순수 스캔본
(data/disclosure/FY2024_Q2/raw/KR0097_하나생명보험_amended.pdf). 이 스크립트를 쓰기 전에
page.get_pixmap(dpi=300)로 p15/p17/p18을 직접 렌더링해서 육안으로 판독했다(오케스트레이터의
판독을 베끼지 않고 독립적으로 재확인, 두 판독이 전부 일치).

원문 인용 (내가 렌더링해서 읽은 그대로):

  p15 [경과조치 적용 전 지급여력비율 세부] 단위 억원, "해당분기(24.2Q)" 열:
    가.지급여력금액(1)=5,280(기존,불변) 기본자본(2)=2,469(기존) 보완자본(3)=2,811(기존)
    Ⅰ.순자산(4)=(1+2+3+4+5+6+7)=5,280 [이 분기는 7개 구성 - item10(비지배지분) 행이 실제로
    존재하고 값 0, KR0087 2023.2Q(6개 구성, item10 행 자체 없음)와는 다른 케이스]
    1.보통주(5)=3,894 2.보통주이외자본증권(6)=1,799 3.이익잉여금(7)=984 4.자본조정(8)=-3
    5.기타포괄손익누계액(9)=-2,584 6.비지배지분(10)=0 7.조정준비금(11)=1,191
    Ⅱ.불인정항목(12)=0 Ⅲ.보완자본재분류(13)=2,811 나.기준금액(14)=4,727(기존,불변)
    Ⅰ.기본요구자본(15)=4,727(반올림) 분산효과(16)=1,767 다.비율(27)=111.71(기존,불변)

  p17 "② 장수위험·사업비위험·해지위험 및 대재해위험 경과조치"(단위 백만원, 적용전/적용후 2열):
    지급여력금액 527,997/527,997(불변, TAC 반영후 값 - item1/2/3는 안 건드림, 이미 정확)
    기본요구자본 472,655 -> 410,952
    생명장기위험액 233,238 -> 144,838 [사망 14,822->14,822 장수 11,346->0 장해질병 29,641->29,641
      장기재물기타 0->0 해지 133,852->74,090 사업비 115,293->75,803 대재해 4,692->0]
    일반손해 0->0 시장위험 228,941->228,941(이 표는 안 건드림) 신용 152,924->152,924
    운영 34,206->34,206 법인세 0->0 기타요구자본 0->0

  p18 "③ 주식위험 경과조치 또는 금리위험 경과조치"(단위 백만원, 적용전/적용후 2열):
    지급여력금액 527,997/527,997(불변) 기본요구자본 472,655 -> 438,530
    생명장기 233,238->233,238(이 표는 안 건드림) 시장위험 228,941 -> 181,270
      [금리 37,403->37,403(불변, TIRR 미신청) 주식 201,309->148,832 부동산 45,628->45,628(불변)
       외환 38,017->38,017(불변) 자산집중 0->0]
    신용 152,924->152,924 운영 34,206->34,206 법인세 0->0 기타요구자본 0->0

②③ 결합 (leaf-combine, 이 저장소 전반의 확립된 방법론 - rebuild_combined_transition_after.py와
동일한 R4/R7/MARKET_M sqrt 조합): item17후=sqrt(R7 leaves from ②'s POST col), item19후=sqrt(MARKET_M
leaves from ③'s POST col), item15후=sqrt(R4[17후,18후=0,19후,20후=152924/100])+21후. 직접 계산
(scripts/_probes 임시 검증, 이 스크립트 내부 재검증 포함)해서 3,737.42를 재현했고 마스터에 이미
있는 item14_적용후=3737(별도 출처, 안 건드림)과 반올림 이내로 일치 - 결합이 맞다는 교차검증.
item27후=6086/3737.42*100=162.84, 마스터 기존 item27_적용후=162.83과 일치(반올림 차이).

item16후(분산효과) = 원문에 없음. rule6과 동일한 공식 (17+18+19+20+21)-15 후컬럼 적용 - 이 저장소
전역에서 결합사 item16후를 항상 이렇게 산출하는 기존 관례(rebuild_combined_transition_after.py의
new[16] 공식과 동일)를 그대로 따른다.

항목 4-13(순자산 구성) 적용후 = 원문에 어느 표에도 없음(② ③ 둘 다 지급여력금액=항목1을 그대로
두고 그 밑의 구성요소 분해가 없다) -> null 유지(ticket 명시 지시, 0 채우지 않음).
항목 24/25/26 적용후 = 0 (부모 item23후=0이 p17/p18 양쪽에서 직접 확인됐고, 세 자식 모두 이미
전값이 0인 비음수 성격의 환산치/대응치라 0=합 성립의 유일해가 0/0/0뿐 - 추측이 아니라 산술적 필연).

기존 item1·2·3·14·27·28 (모두 이미 정확 - 이전 라운드에서 TAC 전용표 등 이 티켓 스코프 밖의
근거로 채워짐)은 손대지 않는다.

Usage:
  ...python scripts/fix_20260821_kr0097_2024q2_vision_ocr.py --dry-run
  ...python scripts/fix_20260821_kr0097_2024q2_vision_ocr.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "kics_disclosure.json"
sys.path.insert(0, str(REPO / "src"))
import numpy as np  # noqa: E402
from solvency.validation.kics_json_rules import R4, R7, MARKET_M  # noqa: E402

CODE, Q = "KR0097", "2024.2Q"  # 티커/생손보여부는 기존 item1 행에서 그대로 복사한다(아래)

LABELS = {
    4: "Ⅰ. 건전성감독기준 재무상태표 상의 순자산", 5: "1. 보통주",
    6: "2. 자본항목 중 보통주 이외의 자본증권", 7: "3. 이익잉여금", 8: "4. 자본조정",
    9: "5. 기타포괄손익누계액", 10: "6. 비지배지분", 11: "7. 조정준비금",
    12: "Ⅱ. 지급여력금액으로 불인정하는 항목 (지급이 예정된 주주배당액 등)",
    13: "Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)",
    15: "Ⅰ. 기본요구자본", 16: "- 분산효과 : (1+2+3+4+5) - Ⅰ",
    17: "1. 생명장기손해보험위험액", 18: "2. 일반손해보험위험액", 19: "3. 시장위험액",
    20: "4. 신용위험액", 21: "5. 운영위험액", 22: "Ⅱ. 법인세조정액",
    23: "Ⅲ. 기타 요구자본(1+2+3)",
    24: "1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치",
    25: "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치",
    26: "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치",
    29: "1-1. 사망위험액", 30: "1-2. 장수위험액", 31: "1-3. 장해·질병위험액",
    32: "1-4. 장기재물·기타위험액", 33: "1-5. 해지위험액", 34: "1-6. 사업비위험액",
    35: "1-7. 대재해위험액",
    36: "3-1. 금리위험액", 37: "3-2. 주식위험액", 38: "3-3. 부동산위험액",
    39: "3-4. 외환위험액", 40: "3-5. 자산집중위험액",
}

# 값(적용전), 억원. p15(4-13,16) 는 억원 표 그대로(정수). 15/17/19/20/21/29-40 은 p17·p18
# 백만원 표를 직접 나눈 정밀값을 쓴다(억원 표는 반올림돼 있다 - ticket 지침, 내 판독도 동일).
PRE = {
    4: 5280, 5: 3894, 6: 1799, 7: 984, 8: -3, 9: -2584, 10: 0, 11: 1191, 12: 0, 13: 2811,
    15: 472655 / 100.0, 16: 1767, 17: 233238 / 100.0, 18: 0, 19: 228941 / 100.0,
    20: 152924 / 100.0, 21: 34206 / 100.0, 22: 0, 23: 0, 24: 0, 25: 0, 26: 0,
    29: 14822 / 100.0, 30: 11346 / 100.0, 31: 29641 / 100.0, 32: 0, 33: 133852 / 100.0,
    34: 115293 / 100.0, 35: 4692 / 100.0, 36: 37403 / 100.0, 37: 201309 / 100.0,
    38: 45628 / 100.0, 39: 38017 / 100.0, 40: 0,
}

# 값_적용후, 억원 - p17(②, 생명장기 leaves) / p18(③, 시장 leaves)의 POST 열 직접 읽음.
# item15/16/17/19 는 leaf-combine 산출(아래 compute_combo 참조), 그 외는 두 표가 합의하는
# 직접값(양쪽 다 안 건드린 항목=불변 그대로).
POST_DIRECT = {
    17: 144838 / 100.0,   # p17 표 직접값 (아래 life_after 는 검산용 재계산일 뿐, 저장은 이 값)
    18: 0.0, 19: 181270 / 100.0,   # p18 표 직접값 (mkt_after 도 마찬가지로 검산 전용)
    20: 152924 / 100.0, 21: 34206 / 100.0, 22: 0.0, 23: 0.0,
    24: 0.0, 25: 0.0, 26: 0.0,   # 부모 item23후=0 (p17/p18 둘 다 확인), 비음수 자식 3개 -> 필연 0
    29: 14822 / 100.0, 30: 0.0, 31: 29641 / 100.0, 32: 0.0, 33: 74090 / 100.0,
    34: 75803 / 100.0, 35: 0.0,
    36: 37403 / 100.0, 37: 148832 / 100.0, 38: 45628 / 100.0, 39: 38017 / 100.0, 40: 0.0,
}
NO_POST = {4, 5, 6, 7, 8, 9, 10, 11, 12, 13}  # 원문 어느 표에도 없음 - null 유지


def fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    before_row_count = len(data)
    before_combos = {(r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) for r in data}

    by_item = {int(r["항목번호"]): r for r in data
               if r.get("원보험사코드") == CODE and r.get("공시분기") == Q}
    print(f"기존 행: {sorted(by_item)}")

    # --- leaf-combine (POST) ---
    life7 = np.array([POST_DIRECT[29], POST_DIRECT[30], POST_DIRECT[31], POST_DIRECT[32],
                       POST_DIRECT[33], POST_DIRECT[34], POST_DIRECT[35]], float)
    life_after = float(np.sqrt(life7 @ R7 @ life7))
    mkt5 = np.array([POST_DIRECT[36], POST_DIRECT[37], POST_DIRECT[38], POST_DIRECT[39],
                      POST_DIRECT[40]], float)
    mkt_after = float(np.sqrt(mkt5 @ MARKET_M @ mkt5))
    w = np.array([life_after, POST_DIRECT[18], mkt_after, POST_DIRECT[20]], float)
    base_after = float(np.sqrt(w @ R4 @ w)) + POST_DIRECT[21]
    disp_after = (life_after + POST_DIRECT[18] + mkt_after + POST_DIRECT[20] + POST_DIRECT[21]) - base_after

    print(f"combo: item17후={life_after:.4f}(p17 direct 1448.38) item19후={mkt_after:.4f}(p18 direct 1812.70) "
          f"item15후={base_after:.4f}(ticket/기존 item14후 3737 대비) item16후={disp_after:.4f}")

    existing_item1_post = by_item[1].get("값_적용후")   # "6086"
    existing_item14_post = by_item[14].get("값_적용후")  # "3737"
    ratio_check = float(existing_item1_post) / base_after * 100
    print(f"교차검증: item14후 기존={existing_item14_post} vs 산출 item15후={base_after:.2f} "
          f"(diff {abs(float(existing_item14_post) - base_after):.2f}, 허용 2.0)")
    print(f"교차검증: 비율후 = {existing_item1_post}/{base_after:.2f}*100 = {ratio_check:.2f} "
          f"vs 기존 item27후={by_item[27].get('값_적용후')}")
    if abs(float(existing_item14_post) - base_after) > 2.0:
        print("!! item14후 교차검증 실패 - 중단")
        return 1

    # item17/19후는 위 life_after/mkt_after(재계산, 검산용)가 아니라 p17/p18의 직접 disclosed
    # 값을 그대로 쓴다(이미 POST_DIRECT에 있음) - item15/16만 원문에 직접 없는 결합/파생값이라
    # 여기서 채운다.
    POST_DIRECT[15] = base_after
    POST_DIRECT[16] = disp_after

    # --- pre-write identity checks (적용전, raw 직접값만) ---
    print("\n=== 적용전 검산 ===")
    ident = [
        ("rule2 item4=5+6+7+8+9+10+11", PRE[4], sum(PRE[i] for i in (5, 6, 7, 8, 9, 10, 11))),
        ("rule5 item14=15-22+23", 4727, PRE[15] - PRE[22] + PRE[23]),
        ("rule6 item16=(17+18+19+20+21)-15", PRE[16],
         PRE[17] + PRE[18] + PRE[19] + PRE[20] + PRE[21] - PRE[15]),
    ]
    ok = True
    for label, want, got in ident:
        d = abs(want - got)
        status = "OK" if d <= 2.0 else "FAIL"
        ok = ok and (status == "OK")
        print(f"  [{status}] {label}: want={want} got={got:.2f} diff={d:.2f}")
    w4 = np.array([PRE[17], PRE[18], PRE[19], PRE[20]], float)
    r4c = float(np.sqrt(w4 @ R4 @ w4)) + PRE[21]
    d4 = abs(PRE[15] - r4c)
    print(f"  [{'OK' if d4 <= 2.0 else 'FAIL'}] rule4 item15=sqrt(R4)+21: want={PRE[15]:.2f} got={r4c:.2f} diff={d4:.2f}")
    ok = ok and d4 <= 2.0
    w7 = np.array([PRE[29], PRE[30], PRE[31], PRE[32], PRE[33], PRE[34], PRE[35]], float)
    r7c = float(np.sqrt(w7 @ R7 @ w7))
    d7 = abs(PRE[17] - r7c)
    print(f"  [{'OK' if d7 <= 2.0 else 'FAIL'}] 8_life item17=sqrt(R7): want={PRE[17]:.2f} got={r7c:.2f} diff={d7:.2f}")
    ok = ok and d7 <= 2.0
    wm = np.array([PRE[36], PRE[37], PRE[38], PRE[39], PRE[40]], float)
    mc = float(np.sqrt(wm @ MARKET_M @ wm))
    dm = abs(PRE[19] - mc)
    print(f"  [{'OK' if dm <= 2.0 else 'FAIL'}] 19_market item19=sqrt(M): want={PRE[19]:.2f} got={mc:.2f} diff={dm:.2f}")
    ok = ok and dm <= 2.0
    if not ok:
        print("!! 적용전 검산 실패 - 중단")
        return 1

    # --- build inserts ---
    inserts = []
    for it in sorted(PRE):
        if it in by_item:
            print(f"SKIP item{it}: 이미 존재")
            continue
        post = None if it in NO_POST else fmt(POST_DIRECT[it])
        inserts.append({
            "원보험사코드": CODE, "원수사명": "하나생명", "티커": by_item[1].get("티커"),
            "생손보여부": by_item[1].get("생손보여부"), "항목번호": it, "항목명": LABELS[it],
            "공시분기": Q, "값": fmt(PRE[it]), "값_적용후": post,
        })

    print(f"\n삽입 예정 {len(inserts)}행:")
    for row in inserts:
        print(f"  item{row['항목번호']:>2} {row['항목명']:<40} 값={row['값']:>10} 값_적용후={row['값_적용후']}")

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0

    data.extend(inserts)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {TARGET.name}: +{len(inserts)}행")

    after_row_count = len(data)
    after_combos = {(r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) for r in data}
    removed = before_combos - after_combos
    added = after_combos - before_combos
    print(f"census: row_count {before_row_count} -> {after_row_count} (delta {after_row_count-before_row_count}, "
          f"expected +{len(inserts)})")
    print(f"combo delta: +{len(added)} / -{len(removed)}")
    if removed:
        print(f"!! UNEXPECTED REMOVED: {removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
