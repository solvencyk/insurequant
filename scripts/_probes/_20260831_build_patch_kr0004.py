# -*- coding: utf-8 -*-
"""Build data/_derived/_patch_2026q2_KR0004.json for MG/예별손해보험 2026.2Q load-gap
resolution. All values fitz-confirmed against data/disclosure/FY2026_Q2/pdf/
KR0004_MG_예별손해보험.pdf pages 17-19, 23-24, 29, 34-36 (docling MD dropped this
entire span for the 생명장기 29-34 table page 23-24 tail / TFI table page 17-19 /
market sub-table pages 34-36 -- keyword-window truncation, same failure class as
inbox 20260831T0700Z but this company's gap wasn't in that ticket's 5-company list).

Labels byte-copied from this company's own live master rows (2026.1Q, or 2025.4Q
for items 41-46 which don't exist in odd-quarter 2026.1Q) -- never hand-typed, per
the U+318D-vs-U+00B7 lookalike trap.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
MASTER = ROOT / "kics_disclosure.json"

data = json.loads(MASTER.read_text(encoding="utf-8"))


def label(code: str, item: int, quarter: str = "2026.1Q") -> str:
    row = next(r for r in data
               if r.get("원보험사코드") == code and r.get("공시분기") == quarter
               and r.get("항목번호") == item)
    return row["항목명"]


def fmt(x) -> str:
    """Match master's string convention: 2dp, trim trailing zeros/point, int if whole."""
    r = round(float(x), 2)
    if r == int(r):
        return str(int(r))
    s = f"{r:.2f}".rstrip("0").rstrip(".")
    return s


def fmt8(x) -> str:
    """item27/28 precision convention: round(x, 8), python str() repr (matches live
    master's '-13.12973428' style exactly -- verified against KR0004 2026.1Q/2025.4Q
    item28 cells, which are round(item2/item14*100, 8))."""
    return str(round(float(x), 8))


PAGE = "data/disclosure/FY2026_Q2/pdf/KR0004_MG_예별손해보험.pdf"

cells = []

# ---------------------------------------------------------------------------
# item10 -- 6.비지배지분. Row entirely absent from the printed
# "[경과조치 적용 전 지급여력비율 세부]" table this quarter (PDF p17, fitz-confirmed):
# only 6 sub-rows print (보통주/자본증권/이익잉여금/자본조정/기타포괄손익누계액/조정준비금,
# numbered 1-6), jumping straight from "5." to "6.조정준비금" -- no "6.비지배지분" line at
# all, for ANY of the 3 comparison columns (26.2Q/26.1Q/25.4Q), even though 26.1Q/25.4Q
# are independently KNOWN =0 from the live master. This is a genuine template omission
# this quarter (row not printed), not a per-quarter value change -- item10 has been 0 in
# every quarter this pipeline has ever loaded for KR0004. TFI table (p18) confirms
# 지급여력금액/기본자본/보완자본 전=후 identically -> no transition effect on 가용자본 side
# (공통 TFI=X, 선택 TAC=X per p16 적용여부 table) -> 값_적용후=값=0.
# Cross-check: item4 = Σ(items5-11) = 300+0-6031-4+34+0(item10)+2685 = -3016 vs disclosed
# item4=-3017 (diff -1) -- explained by the SAME table's own B/S 자기자본 총계 arithmetic
# showing an identical +-1 residual (300+0+0-6031-4+34=-5701 vs disclosed 자본총계=-5702,
# 4-1 table PDF p12) -- i.e. a structural 억원-integer rounding artifact of this company's
# disclosure, not evidence of a nonzero item10.
cells.append({
    "항목번호": 10,
    "항목명": label("KR0004", 10),
    "값": 0,
    "값_적용후": 0,
    "근거": (
        f"{PAGE} p17(fitz-confirmed), '[경과조치 적용 전 지급여력비율 세부]' 표: 26.2Q/26.1Q/"
        "25.4Q 3개 컬럼 전부에서 '6.비지배지분' 행이 아예 인쇄되지 않음(5.기타포괄손익누계액 "
        "다음이 곧바로 '6.조정준비금'). 26.1Q/25.4Q는 라이브 마스터에 이미 item10=0으로 적재돼 "
        "있어(원래 있던 값이 이번 분기 서식 압축으로 행 자체가 빠짐), 이 회사는 전 분기 "
        "비지배지분=0 이력. TFI표(p18)가 지급여력금액/기본자본/보완자본 전부 전=후 동일하게 "
        "인쇄(공통TFI=X, 선택TAC=X, p16 적용여부표) -> 가용자본측 전 항목 무변, 값_적용후=값. "
        "item4=SUM(5-11) 대조: 300+0-6031-4+34+0+2685=-3016 vs 공시 item4=-3017 (diff -1) -- "
        "동일 회사 4-1 B/S표(p12)의 자기자본 총계 자체도 300+0+0-6031-4+34=-5701 vs 공시 "
        "-5702 로 같은 +-1 잔차 구조를 보여, 억원 정수 반올림 누적오차이지 비지배지분 실값 "
        "아님을 확인."
    ),
})

# ---------------------------------------------------------------------------
# item28 -- 기본자본비율. Never printed in source (established convention: derived
# item2/item14*100). Uses headline rounded item2/item14 (matches this company's own
# 2026.1Q/2025.4Q precedent exactly: round(-1092/8317*100,8)=-13.12973428 byte-matches
# live; round(-715/8656*100,8)=-8.26016636 byte-matches live 2025.4Q).
item2_pre, item14_pre = -3018, 8613
item2_post, item14_post = -3018, 7219  # TFI/TAC=X -> item2 unaffected by transition
cells.append({
    "항목번호": 28,
    "항목명": label("KR0004", 28),
    "값": fmt8(item2_pre / item14_pre * 100),
    "값_적용후": fmt8(item2_post / item14_post * 100),
    "근거": (
        "MD 미추출 항목(이 저장소 확립 관행: item28=item2/item14x100 직접산출). "
        f"item2(기본자본,헤드라인,적용전)={item2_pre}, item14(적용전)={item14_pre} "
        f"-> round(({item2_pre}/{item14_pre})*100,8)={fmt8(item2_pre/item14_pre*100)}. "
        f"item2_적용후: TFI=X, TAC=X(p16 적용여부표, p18 TFI표 기본자본 전=후 -301,770=-301,770 "
        f"백만원 동일 확인)이라 값_적용후=값={item2_post}, item14_적용후={item14_post}(라이브 "
        f"기존값) -> round(({item2_post}/{item14_post})*100,8)={fmt8(item2_post/item14_post*100)}. "
        "정밀도(8자리 round)는 이 회사 2026.1Q(item28='-13.12973428')와 2025.4Q('-8.26016636'/"
        "'-9.70939707') 기존 셀과 동일 공식 재현으로 검증(byte-exact)."
    ),
})

# ---------------------------------------------------------------------------
# items 29-35 -- 생명·장기손해보험위험액 현황(대재해위험 이외 + 대재해위험 별도표),
# PDF p23-24 (fitz-confirmed; docling MD only shows a 1-row tail fragment "사업비위험
# - 94,991 94,991" belonging to the PRIOR-quarter comparison block, at md L322 --
# the entire 당기(26.2Q) block + table headers were dropped). Column order in raw =
# [1.생명보험(항상 '-', 이 회사는 생명보험 無)/2.장기손해보험/3.총계] -- 2==3 always
# since 생명보험=0. 직전반기(25.4Q) 비교 블록 값 전부가 라이브 마스터의 기존 2025.4Q
# item29-35 값과 소수점까지 정확히 일치(사망26,237->262.37 / 장수0->0 / 장해질병640,618
# ->6406.18 / 장기재물기타12,406->124.06 / 해지179,759->1797.59 / 사업비94,991->949.91 /
# 대재해(별도표)4,541->45.41) -- 표/컬럼 식별 100% 교차검증됨.
#
# 적용후(TIR, 선택적용 O -- p16 적용여부표): PDF p19 "장수위험ㆍ사업비위험ㆍ해지위험 및
# 대재해위험 경과조치" 표(단위 백만원,%)가 [적용전/적용후] 두 컬럼을 직접 인쇄. 사망/장수/
# 장해질병/장기재물기타는 TIR 미적용축이라 전=후. 해지=157,961/0(완전 미인식), 사업비=
# 164,142/70,274(부분인식, 이전 분기들의 '전부 0' 패턴과 다름 -- 분기별 phase-in 비율 상승,
# 패턴 추정 아니라 원문 재확인으로 얻음), 대재해=3,544/0.
#
# 게이트 8_life(item17=sqrt(S'R7S), S=29-35, PRE only) 재검산: expected=7311.03 vs 공시
# item17=7311, diff=-0.03(rel -0.0004%) -- kics_json_rules.py의 실제 R7 행렬로 재계산,
# tolerance(1%) 내 정확 일치. 표/부호/단위 정합성 최종 확인.
sub29_35 = [
    (29, 24681, 24681, "사망위험", False),
    (30, 0, 0, "장수위험", False),
    (31, 588113, 588113, "장해ㆍ질병위험", False),
    (32, 15016, 15016, "장기재물ㆍ기타위험", False),
    (33, 157961, 0, "해지위험", False),
    (34, 164142, 70274, "사업비위험", False),
    (35, 3544, 0, "대재해위험", True),
]
for item, v_pre_mn, v_post_mn, kr_name, is_correction in sub29_35:
    if item == 35:
        source_note = (
            f"{PAGE} p24(fitz-confirmed, docling MD 미포함), "
            "'[생명ㆍ장기손해보험위험액 - 대재해위험]' 표(단위 백만원) 'Ⅲ.총계' 행 "
            f"당기(26.2Q) 대재해위험액={v_pre_mn:,}백만원 -> /100 = {fmt(v_pre_mn/100.0)}억원."
        )
    else:
        source_note = (
            f"{PAGE} p23(fitz-confirmed, docling MD 미포함), "
            "'[생명ㆍ장기손해보험위험액 - 대재해위험 이외]' 표(단위 백만원) "
            f"'Ⅲ.총계' 컬럼 당기(26.2Q) {kr_name}={v_pre_mn:,}백만원 -> /100 = "
            f"{fmt(v_pre_mn/100.0)}억원 (Ⅰ.생명보험=항상 '-'=이 회사 생명보험 無, "
            "Ⅱ.장기손해보험==Ⅲ.총계). 직전반기(25.4Q) 비교블록 값이 라이브 마스터 기존 "
            "2025.4Q 동일항목과 소수점까지 정확 일치(표/컬럼 식별 교차검증됨)."
        )
    fix_prefix = (
        "FIX(오적재 정정 -- 라이브 값 2897833은 6-3.일반손해보험위험액의 [대재해위험]표(p29) "
        "'Ⅳ.대재해위험액' 행의 익스포져 컬럼값이 잘못 들어간 것이다. 항목17(생명장기)의 "
        "대재해위험 하위항목이 아니라 항목18(일반손해)의 전혀 다른 표+다른 컬럼이었다. "
        if is_correction else
        "GAP-FILL(29-34 ZERO match -- fill_subitems_to_disclosure.py 가 docling MD 유실로 "
        "이 회사를 통째로 못 찾음). "
    )
    post_note = (
        f" 값_적용후: p19 '장수위험ㆍ사업비위험ㆍ해지위험 및 대재해위험 경과조치' 표"
        f"(TIR, 선택적용 O) [적용전/적용후] 두 컬럼 중 {kr_name} 행 후={v_post_mn:,}백만원 "
        f"-> /100 = {fmt(v_post_mn/100.0)}억원."
    )
    cells.append({
        "항목번호": item,
        "항목명": label("KR0004", item),
        "값": fmt(v_pre_mn / 100.0),
        "값_적용후": fmt(v_post_mn / 100.0),
        "근거": fix_prefix + source_note + post_note,
    })

# ---------------------------------------------------------------------------
# items 36-40 -- 시장위험 하위. Sourced from THREE independent locations that all
# agree: (a) 6-4-1)(2) 금리위험액현황 p34 'Ⅳ.금리위험액' row; (b) 6-4-1)(3)
# 주식위험액현황 p36 'Ⅲ.합계주)' row + narrative "2026년 6월 주식위험액은 1,765억원"
# (rounds); (c) 부동산 p37 narrative "2026년 6월 부동산위험액은 0억원" (current-period
# block is the all-dash one, comparison block=6,645/1,661 matches live 2025.4Q
# item38=16.61 exactly); (d) 외환 p38 narrative "2026년 6월 외환위험액 279억원" +
# table '계' row=27,883백만원; (e) 자산집중 p38 "*해당사항 없음"=0.
# 값_적용후: p19 "주식위험 경과조치 또는 금리위험 경과조치" 표(TER+TIRR, 선택적용 O 둘다)
# [적용전/적용후] 컬럼: 금리110,218/34,650, 주식176,466/123,489, 부동산0/0, 외환27,883/
# 27,883(FX 무영향), 자산집중0/0.
# 게이트 19_market(item19=sqrt(V'MARKET_M V), PRE) 재검산: expected=2299.28 vs 공시
# item19=2299, diff=-0.28(rel -0.012%) -- kics_json_rules.py의 실제 MARKET_M 행렬로
# 재계산, tolerance(1%) 내 정확 일치.
sub36_40 = [
    (36, 110218, 34650, "금리위험", "p34", ""),
    (37, 176466, 123489, "주식위험", "p36", " (narrative: '2026년 6월 주식위험액은 1,765억원'과 반올림 일치)"),
    (38, 0, 0, "부동산위험", "p37",
     " (narrative: '2026년 6월 부동산위험액은 0억원으로 산출'; 표의 두 블록 중 첫(전부 '-')이 "
     "당기, 둘째(6,645/1,661)가 직전반기 비교=라이브 기존 2025.4Q item38=16.61과 정확 일치로 "
     "블록순서 확인)"),
    (39, 27883, 27883, "외환위험", "p38", " (narrative: '2026년 6월 외환위험액 279억원으로 산출'와 반올림 일치, 표 '계' 행)"),
    (40, 0, 0, "자산집중위험", "p38", " (narrative: '(6)자산집중위험액 현황 *해당사항 없음' = 0, 명시적 공시)"),
]
for item, v_pre_mn, v_post_mn, kr_name, srcpage, extra in sub36_40:
    cells.append({
        "항목번호": item,
        "항목명": label("KR0004", item),
        "값": fmt(v_pre_mn / 100.0),
        "값_적용후": fmt(v_post_mn / 100.0),
        "근거": (
            "GAP-FILL(36-40 전부 결측 -- 6-4.시장위험 관리 절이 docling MD keyword-window에서 "
            "통째로 드롭됨: MD가 '6-3.일반손해보험위험 관리'에서 곧바로 '(4)부동산위험액현황'으로 "
            "점프, (1)개념/(2)금리위험액현황/(3)주식위험액현황 헤더 전부 미포함 -- inbox "
            "20260831T0700Z '5사 재발' 티켓과 동일 실패양식의 6번째 사례). "
            f"{PAGE} {srcpage}(fitz-confirmed) 당기(26.2Q) {kr_name}액={v_pre_mn:,}백만원 -> "
            f"/100 = {fmt(v_pre_mn/100.0)}억원{extra}. 값_적용후: p19 '주식위험 경과조치 또는 "
            "금리위험 경과조치' 표(TER+TIRR, 선택적용 둘다 O, p16 적용여부표) [적용전/적용후] "
            f"컬럼 {kr_name} 후={v_post_mn:,}백만원 -> /100 = {fmt(v_post_mn/100.0)}억원."
        ),
    })

# ---------------------------------------------------------------------------
# items 41-46 -- 금리위험 순자산가치 시나리오(충격전/평균회귀/금리상승/금리하락/금리평탄/
# 금리경사). p34 금리위험액현황 표 'Ⅲ.순자산가치' 행. 값_적용후 없음(established
# convention -- 이 항목은 이 회사 전 분기 이력에서 값_적용후 필드 자체가 존재한 적이 없음,
# 2025.4Q 6개 항목 전부 값_적용후=None 확인).
# 게이트 36_irr(item36=irr_derive_expected({36,41-46})) 재검산: expected=1102.1782 vs
# item36(위에서 채운 값)=1102.18, diff=0.0018 -- kics_json_rules.py 실제 함수로 재계산,
# 사실상 완전 일치. 짝수분기(2Q)인데 item36 present + 41-46 결측이면 36_irr이 RED로
# 뜨는 구조(코드 확인) -- 36-40과 함께 41-46도 반드시 같이 채워야 새 RED 안 생김.
sub41_46 = [
    (41, -5595, "충격전"),
    (42, -5833, "평균회귀"),
    (43, 76826, "금리상승"),
    (44, -106211, "금리하락"),
    (45, -50002, "금리평탄"),
    (46, 37824, "금리경사"),
]
for item, v_mn, kr_name in sub41_46:
    cells.append({
        "항목번호": item,
        "항목명": label("KR0004", item, quarter="2025.4Q"),
        "값": fmt(v_mn / 100.0),
        "근거": (
            "GAP-FILL(41-46 전부 결측 -- 36-40과 동일 원인, 6-4.시장위험 관리 절 docling MD "
            f"드롭). {PAGE} p34(fitz-confirmed) '6-4-1)(2)금리위험액현황' 표(단위 백만원) 당기"
            f"(26.2Q) 'Ⅲ.순자산가치' {kr_name} 컬럼={v_mn:,}백만원 -> /100 = {fmt(v_mn/100.0)}억원. "
            "값_적용후 없음: 이 항목은 시나리오 순자산가치 원값이라 TIRR 전환감쇄가 결과(item36)에만 "
            "적용되고 41-46 자체엔 적용후 컬럼이 없음 -- 이 회사 2025.4Q 6개 항목 전부 "
            "값_적용후=None 확립 관행과 동일. 36_irr 게이트가 item36 present+짝수분기인데 "
            "41-46 결측이면 RED로 판정하는 구조(kics_json_rules.py L659부근)라 36-40 작업과 "
            "묶어서 반드시 같이 채움 -- 안 그러면 새 RED 유발."
        ),
    })

# ---------------------------------------------------------------------------
# items 47/49/50/51/53/54 -- TFI 공통적용경과조치 표(p18). item48은 별도 FIX(아래).
# 라벨은 항상 이 회사 2026.1Q 기존 행에서 그대로 복사.
tfi_cells = [
    (47, 49, 49, "보완자본 한도 적용 전"),
    (49, 0, 0, "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분"),
    (50, -301770, -301770, "기본자본"),
    (51, 49, 49, "보완자본"),
]
for item, v_pre_mn, v_post_mn, kr_name in tfi_cells:
    extra = ""
    if item == 51:
        v52 = round((-301770 + 49) / 100.0, 2)
        extra = (
            f" 축E 검산(item50+item51==item52): {v52} vs 라이브 기존 item52=-3017.21 -- diff 0"
            "으로 정확 일치(전ㆍ후 공통, 이 표 자체가 전=후 동일 인쇄)."
        )
    elif item == 47:
        extra = (
            " UNCAPPED 판정(축B): item47=0.49 ~= item3(헤드라인 보완자본,적용전)=0(반올림) -- "
            "한도(item48=4306.72)가 훨씬 커서 미구속, item3==item47 재현식 성립."
        )
    cells.append({
        "항목번호": item,
        "항목명": label("KR0004", item),
        "값": fmt(v_pre_mn / 100.0),
        "값_적용후": fmt(v_post_mn / 100.0),
        "근거": (
            "GAP-FILL(47-54 전부 결측 -- TFI 표는 자동추출기가 다루지 않는 항목, KR1000/KR0005/"
            f"KR0075 등과 동일 계열 백필 필요). {PAGE} p18(fitz-confirmed, docling MD 미포함), "
            "'[지급여력비율의 경과조치 적용에 관한 사항] (1) 공통적용 경과조치 관련' 표"
            f"(단위 백만원,%) '{kr_name}' 행 [적용전/적용후]={v_pre_mn:,}/{v_post_mn:,}백만원 -> "
            f"/100 = {fmt(v_pre_mn/100.0)}/{fmt(v_post_mn/100.0)}억원.{extra}"
        ),
    })

# item48 -- FIX(오적재 정정). 라이브 값 0은 명백히 오적재(보완자본 한도 4306.72억이어야
# 할 자리에 0). 독립검산 item48==item14_적용전x50%로 확정.
item48_pre_mn, item48_post_mn = 430672, 430672
i48_expected_check = 8613 * 0.5
i48_val = fmt(item48_pre_mn / 100.0)
diff48 = round(item48_pre_mn / 100.0 - i48_expected_check, 2)
cells.append({
    "항목번호": 48,
    "항목명": label("KR0004", 48),
    "값": i48_val,
    "값_적용후": fmt(item48_post_mn / 100.0),
    "근거": (
        "FIX(오적재 정정 -- 라이브 값 0은 오적재/미충전. 정답은 TFI표 자체에서 직접 확인됨). "
        f"{PAGE} p18(fitz-confirmed) 같은 표 '보완자본 한도' 행 [적용전/적용후]="
        f"{item48_pre_mn:,}/{item48_post_mn:,}백만원 -> /100 = {i48_val}/"
        f"{fmt(item48_post_mn/100.0)}억원(전=후 동일 인쇄). 독립검산(요청된 필수 검증): "
        f"item48 == item14(적용전)x50% = 8613x0.5={i48_expected_check} vs 원문값 {i48_val} -- "
        f"diff {diff48} (반올림 범위, KR0008 diff 0.20ㆍKR0005 diff 0.03과 동일 규모) -- 정답 "
        "확정. inbox 20260831T0705Z item48 라벨오염(보완자본 한도 자리에 item3 보완자본값이 "
        "복사되는 9사 패턴)과는 다른 결함으로 보임: KR0004의 오염값은 0이라 item3(=0)과 우연히 "
        "같아 동일 패턴인지 다른 원인(단순 미충전)인지 원문만으로는 구분 불가하나, 결과적으로 "
        "정답은 동일하게 이 독립검산식으로 확정됨."
    ),
})

# item53/54 -- (기발행 신종자본증권)/(기발행 후순위채무). 원문 전용컬럼(적용전)만 인쇄,
# 적용후는 공백 -- KR0005/KR0032 선례와 동일 패턴(추측/보간 금지).
cells.append({
    "항목번호": 53,
    "항목명": label("KR0004", 53),
    "값": 0,
    "근거": (
        f"GAP-FILL(TFI 표 미백필분). {PAGE} p18(fitz-confirmed) 같은 표 '(기발행 신종자본증권)' "
        "행: 적용전 컬럼에만 '0'이 인쇄되고 적용후 컬럼은 공백(그 다음 줄 "
        "'(기발행 후순위채무)' 행으로 곧바로 이어짐, 지급여력기준금액 행처럼 두 값이 나란히 "
        "인쇄되는 표준 행과 다름). 값_적용후는 원문 자체가 공백이라 채우지 않음(KR0005/KR0032 "
        "선례와 동일 패턴, 추측ㆍ보간 금지)."
    ),
})
cells.append({
    "항목번호": 54,
    "항목명": label("KR0004", 54),
    "값": 0,
    "근거": (
        f"GAP-FILL(TFI 표 미백필분). {PAGE} p18(fitz-confirmed) 같은 표 '(기발행 후순위채무)' "
        "행: 적용전 컬럼에만 '0'이 인쇄되고 적용후 컬럼은 공백. 값_적용후는 원문 자체가 공백이라 "
        "채우지 않음(KR0005/KR0032 선례와 동일 패턴, 추측ㆍ보간 금지)."
    ),
})

# ---------------------------------------------------------------------------
# item17/19 적용후 -- 부모 항목의 값_적용후만 결측(값 자체는 이미 정확히 적재됨).
# 자식(29-35, 36-40)의 값_적용후를 채우면서 게이트의 부모-자식 적용후 완전성census
# (_parent_present_child_incomplete 계열)가 함께 열리므로, KR1000 선례와 동일하게
# 부모 축도 같이 닫는다. "값":null 로 명시 -- 값은 이미 정확하니 건드리지 않는다는 뜻
# (KR1000 patch item52와 같은 관행).
i17_post_mn = 634160
i19_post_mn = 134643
cells.append({
    "항목번호": 17,
    "항목명": label("KR0004", 17),
    "값": None,
    "값_적용후": fmt(i17_post_mn / 100.0),
    "근거": (
        "GAP-FILL(적용후만 결측 -- 값=7311은 이미 정확, 안 건드림). 29-35의 값_적용후를 채우면서 "
        "게이트의 17->29-35 적용후 완전성census가 함께 열려 부분충전 RED를 새로 만들기 때문에 "
        "KR1000 선례와 동일하게 부모 축도 같이 채움(항목이 서로 census로 얽혀 있음). "
        f"{PAGE} p19 '장수위험ㆍ사업비위험ㆍ해지위험 및 대재해위험 경과조치' 표(TIR) "
        f"'생명ㆍ장기손해보험위험액' 행 적용후={i17_post_mn:,}백만원 -> /100 = "
        f"{fmt(i17_post_mn/100.0)}억원. 게이트 8_life는 PRE(29-35, item17 모두 bucket.get "
        "기본값=적용전)만 검사하므로 이 적용후 fill은 8_life 판정에는 영향 없음(코드 확인, "
        "kics_json_rules.py L818부근)."
    ),
})
cells.append({
    "항목번호": 19,
    "항목명": label("KR0004", 19),
    "값": None,
    "값_적용후": fmt(i19_post_mn / 100.0),
    "근거": (
        "GAP-FILL(적용후만 결측 -- 값=2299는 이미 정확, 안 건드림). 36-40의 값_적용후를 채우면서 "
        "게이트의 19->36-40 적용후 완전성census가 함께 열리므로 부모 축도 같이 채움(17/19 동일 "
        "이유). "
        f"{PAGE} p19 '주식위험 경과조치 또는 금리위험 경과조치' 표(TER+TIRR) '시장위험액' 행 "
        f"적용후={i19_post_mn:,}백만원 -> /100 = {fmt(i19_post_mn/100.0)}억원. 게이트 19_market은 "
        "PRE(36-40, item19 모두 bucket.get 기본값=적용전)만 검사하므로 이 적용후 fill은 "
        "19_market 판정에는 영향 없음(코드 확인, kics_json_rules.py L568부근)."
    ),
})

# ---------------------------------------------------------------------------
# item2 적용후 -- discovered via scratch-gate diff (not in original named-gap
# list): rule "8_post" (item28_후=item2_후/item14_후x100) stays SKIP even after
# item28_후 is filled, because its same_basis guard requires item2 and item14 to
# BOTH have post values or BOTH not -- item14_후 was already present pre-patch
# but item2_후 was not, so the mismatch forces SKIP forever regardless of item28.
# item2_후 is fully evidenced (TFI=X/TAC=X, TFI table 기본자본 전=후 identical,
# same reasoning as item10/item28 above) so this is a zero-risk, code-verified
# fill, not speculative scope creep -- confirmed against the gate itself.
cells.append({
    "항목번호": 2,
    "항목명": label("KR0004", 2),
    "값": None,
    "값_적용후": fmt(item2_post / 1.0),
    "근거": (
        "GAP-FILL(적용후만 결측 -- 값=-3018은 이미 정확, 안 건드림). 스크래치 게이트 diff에서 "
        "발견: rule 8_post(item28_후=item2_후/item14_후x100)의 same_basis 가드가 item2/item14 "
        "둘 다 post 존재 또는 둘 다 부재를 요구하는데, item14_후는 이미 있고 item2_후만 없어서 "
        "item28_후를 채워도 8_post가 계속 SKIP으로 남는 것을 확인(kics_json_rules.py L780부근). "
        "TFI=X, TAC=X(p16 적용여부표, TFI표 기본자본 전=후 -301,770=-301,770 백만원 동일, item10/"
        "item28 근거와 동일 논리)이라 값_적용후=값=-3018 로 채움 -- 추측이 아니라 게이트 자체로 "
        "확인된 필요 fill."
    ),
})

patch = {
    "company_code": "KR0004",
    "quarter": "2026.2Q",
    "cells": cells,
    "notes": (
        "MG/예별손해보험 2026.2Q 적재 갭(48항목 중 29만 적재) 해소. 원인 3갈래: "
        "(1) items 29-34 '[생명ㆍ장기손해보험위험액 현황]' 표(p23-24)와 36-40 '6-4.시장위험 "
        "관리' 절(p34-38)이 docling keyword-window에서 통째로 드롭됨(6-4절 드롭은 inbox "
        "20260831T0700Z '5사' 패턴의 6번째 사례) -- fitz 직접추출로 복구, 41-46(금리IRR "
        "시나리오)도 36_irr 게이트가 item36 present+41-46 결측이면 RED를 내는 구조라 함께 "
        "복구(요청범위 밖이었으나 새 RED 방지를 위해 필수). (2) items 47/49/50/51/53/54(TFI "
        "표, p18)는 자동추출기가 아예 다루지 않는 항목이라 원래부터 백필 대상. (3) item35"
        "(대재해위험)와 item48(보완자본 한도)은 '결측'이 아니라 오적재였다 -- item35는 "
        "일반손해보험(item18) 대재해위험표의 익스포져 컬럼(2,897,833)이 잘못 들어간 것(정답은 "
        "생명장기 대재해위험표 Ⅲ.총계=35.44), item48은 0으로 미충전(정답 4306.72, 독립검산 "
        "item14_적용전x50%=4306.5와 diff 0.22로 확정). item10(비지배지분)은 이번 분기 표에서 "
        "행 자체가 안 인쇄됐지만(생성 이력ㆍTFI표 교차확인으로 0 확정) 값=0 채움. item28(기본자본"
        "비율)은 이 저장소 확립 관행대로 item2/item14x100 8자리 반올림 직접산출. item17/19의 "
        "값_적용후만 부수로 채움(자식 29-35/36-40 적용후 census 완결에 필요, 값 자체는 안 건드림). "
        "item53/54의 값_적용후는 원문 자체가 공백(KR0005/KR0032 선례와 동일)이라 결측 유지. "
        "게이트 재검산 3종 전부 tolerance 내 정확 일치: 8_life(item17=sqrt(S'R7S)) diff -0.03 "
        "(rel -0.0004%), 19_market(item19=sqrt(V'MARKET_M V)) diff -0.28(rel -0.012%), "
        "36_irr(item36=irr_derive_expected) diff 0.0018(사실상 0) -- 전부 kics_json_rules.py "
        "실제 함수로 재계산(행렬 재타이핑 아님)."
    ),
    "unfixable": [],
}

out_path = ROOT / "data" / "_derived" / "_patch_2026q2_KR0004.json"
if out_path.exists():
    raise SystemExit(f"ABORT: {out_path} already exists -- would overwrite, merge instead")
out_path.write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out_path} ({len(cells)} cells)")
for c in cells:
    print(f"  item{c['항목번호']:>2} {c['항목명']!r} 값={c.get('값')!r} 값_적용후={c.get('값_적용후')!r}")
