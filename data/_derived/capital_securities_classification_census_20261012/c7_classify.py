"""c7_classify.py (parser-kics, ticket 20261012T1230Z) -- READ ONLY on every repo file; writes only next to this script.

Final step of the 신종자본증권 / 후순위채 classification census.  Inputs (all produced by c1..c5 or read-only repo files):
  census_inventory.json        (c1)  133 securities of the bond files + registry / ledger fields
  census_reconcile.csv         (c2)  K-ICS items 6 / 53 / 54 vs the inventory, every quarter
  census_issue_quarter_test.csv(c5)  issuer-treatment test of every post-2022 hybrid (item 47 / X jump in the issue quarter)
  c6_evidence.py                     evidence table (regulation text, DART filing lines, press)
Decision rules (every decision names its evidence ids):
  hybrid issued before 2023-01-01            -> legacy_tfi  ([별표22] Ⅵ.1.가.(1) 공통적용 경과조치: 종전 RBC 기본자본분, 2032-12-31 까지 총요구자본 15% 한도)
  hybrid issued 2023-01-01 or later          -> the issuer's own filing decides: a step-up (금리상향) fails the 기본자본요건 (R1) -> tier2 (보완자본 자본증권 Ⅲ.2.다.(2));
                                               no step-up wording -> tier1 only with rating / press / K-ICS-table support, else unknown
  subordinated bond issued before 2023       -> tier2_legacy (경과조치 (2): 종전 보완자본 인정분은 한도 무관 보완자본)
  subordinated bond issued 2023 or later     -> tier2 (보완자본 자본증권, 보완자본 한도 내)
Grades:  a = 원문 확정 (issuer filing / rating-agency report / regulation text states it)   b = 시계열 추정 (issuer's K-ICS tables)   c = 불명 / conflicting
a_basis tells what the grade-a rests on (issuer_filing / K-ICS_table / press_of_rating_report / regulation).  The registry (capital_tier_registry.json) is NEVER modified.
Outputs: census_securities.csv/json, census_evidence.csv, census_mismatch.csv/txt, census_summary.txt.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/c7_classify.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
from c6_evidence import EV, EVIDENCE  # noqa: E402

inv_doc = json.loads((HERE / "census_inventory.json").read_text(encoding="utf-8"))
inv = inv_doc["rows"]
reg = json.loads((REPO / "data/bonds/capital_tier_registry.json").read_text(encoding="utf-8"))
h1 = json.loads((REPO / "data/bonds/capital_securities_fy2026h1.json").read_text(encoding="utf-8"))
kd = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
iqt = {(r["code"], r["issue_date"]): r for r in csv.DictReader(open(HERE / "census_issue_quarter_test.csv", encoding="utf-8-sig"))}
NAMES = {c["code"]: c["company"] for c in h1["companies"]}

QUARTERS = [f"{y}.{n}Q" for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]


def item_series(code, item):
    out = {}
    for r in kd:
        if r["원보험사코드"] == code and r["항목번호"] == item:
            try:
                out[r["공시분기"]] = float(str(r.get("값")).replace(",", ""))
            except (TypeError, ValueError):
                pass
    return out


def compress(series):
    """'23.1Q-23.3Q=2850; 23.4Q-25.3Q=2837.3; ...' (consecutive equal values)"""
    parts, cur = [], None
    for q in QUARTERS:
        v = series.get(q)
        if v is None:
            continue
        if cur and abs(cur[2] - v) < 0.5:
            cur[1] = q
        else:
            if cur:
                parts.append(cur)
            cur = [q, q, v]
    if cur:
        parts.append(cur)
    return "; ".join(f"{a[2:]}{'' if a == b else '-' + b[2:]}={v:g}" for a, b, v in parts)


# ---------------------------------------------------------------------------------------------------------------- hybrids issued before 2023
LEG_NOTES = {  # company-level reading of the issuer's own TFI-table row item 53 against the bond list (series auto-printed in the evidence column)
    "KR0001": "발행사 TFI 표 항목 53 이 목록 합계(제1회 1,050 상환 전 2,850)와 일치",
    "KR0002": "항목 53 = 제13·14회 2,350 과 일치(2023.1Q~2Q 의 추가 1,885억 = 2023.3Q 에 상환된 이력 신종)",
    "KR0003": "항목 53 = 제3·4회 460 과 일치",
    "KR0005": "항목 53 = 2,120 = 5건 합계(920+200+300+600+100)와 일치",
    "KR0071": "항목 53 = 496.5 = 제2·3회 500 과 일치",
    "KR0073": "항목 53 = 11,088.99 = 4,700 + 6,448.5(USD 500M 장부 환산) 와 일치",
    "KR0076": "항목 53 = 2,465.98 = 신종 제1회 948.8 + 2022 발행 전환우선주 1,517.18(자본금 380 + 자본잉여금 1,137.18) 과 일치",
    "KR0082": "항목 53 = 697 -> 398.39(2023.2Q~2025.1Q) -> 0(2025.2Q 상환) - 제2회 400억의 상환까지 일치",
    "KR0083": "항목 53 = 400(2023.2Q~) 일치(2023.1Q 는 40 으로 적재 - 소스 MD 표기 '4,000' 이라 단위 확인 필요)",
    "KR0087": "항목 53 = 3,445.67(USD 3억 환산, 2023.1Q~2025.2Q) -> 0(2025.3Q 상환)",
    "KR0094": "항목 53 이 목록 합계 3,000 과 일치, 2025.3Q 이후 0(2025-08 상환)",
    "KR0099": "항목 53 = 498 ≈ 500(2023.2Q 만 인쇄 '-')",
    "KR0104": "항목 53 = 2,500 = 제4회 2,500 과 일치(14/14분기)",
    "KR1000": "항목 53 = 5,586(2023.1Q~2024.3Q: 제3·4회 3,300 + 이력 신종 2,286) -> 3,291.75~3,291.97(2024.4Q~) = 제3·4회 3,300",
}
LEG_STEP = {  # whether the issuer's own wording shows the step-up that the K-ICS commentary (R2) names as the reason legacy hybrids are 보완자본-type
    "KR0001": ("unknown", ["F-KR0001"]), "KR0068": ("yes", ["F-KR0068-2019"]), "KR0071": ("yes", ["F-KR0071"]), "KR0073": ("yes", ["F-KR0073"]),
    "KR0082": ("yes", ["F-KR0082"]), "KR0087": ("yes", ["F-KR0087"]), "KR0094": ("yes", ["F-KR0094"]), "KR0099": ("yes", ["F-KR0099"]),
    "KR0104": ("yes", ["F-KR0104"]), "KR1000": ("yes", ["F-KR1000"]), "KR0083": ("yes(indirect)", ["F-KR0083"]),
}

# ---------------------------------------------------------------------------------------------------------------- hybrids issued 2023 or later
POST = {
    ("KR0005", "2025-03-21", 2000.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR0005", "R1"],
        basis="사업보고서: 발행 10년째 가산금리 +1.00%p(재산정) = 스텝업 -> 기본자본요건 불충족(R1) -> 보완자본형. 발행사 K-ICS 표 항목 47 이 발행분기에 +1,998(액면 2,000)",
        treat="consistent"),
    ("KR0011", "2025-09-01", 7470.0): dict(type="tier1", grade="a", a_basis="press_of_rating_report", step_up="no", ev=["W3", "W4", "W1", "F-KR0011", "R1"],
        basis="한신평·한기평 AA(안정적) '기본자본 신종자본증권(비조건부)' 평가 보도(스텝업 조항 삭제, 발행기관의 이자지급 전적 재량); 사업보고서 발행금리 3.80% 단일, 조정 문구 없음; 2025.3Q 항목 47 +1,267(8,670 중 한도 10% 9,783 이내라 재분류 없어야 함)",
        treat="consistent(tier1: item 47 jump << face)"),
    ("KR0011", "2025-09-25", 1200.0): dict(type="tier1", grade="b", b_strength="strong", a_basis="", step_up="no(no wording)", ev=["F-KR0011", "C9", "W2", "R1"],
        basis="제1회와 같은 조건(3.80% 단일, 조기상환 = 5년 후 금감원 승인, 기타 조건 없음); 별도 신평 보고서는 못 찾음. 발행사 표에서는 제1회와 같은 분기(2025.3Q)의 한 블록 8,650 - c9 사건연구: 블록을 보완자본형으로 보면 'other' 변화 -7,302(불가능), 기본자본형이면 +1,348(발행 전 변화 최대 1,963 안) -> 제1회와 함께 기본자본형으로 읽힘(제2회만 따로 판독은 불가)",
        treat="consistent(tier1: c9 event study 2025.3Q)"),
    ("KR0011", "2026-02-11", 4420.0): dict(type="tier2", grade="b", b_strength="moderate", a_basis="", step_up="no(no wording)", ev=["F-KR0011", "C9", "W5"],
        basis="발행사 K-ICS 표(c9): 2026.1Q 블록(4,413)을 보완자본형으로 보면 'other' 변화 +421, 기본자본형(요구자본 10% 한도 초과분만 재분류)이면 +1,638 - 발행 전 분기 변화의 중앙 660·최대 1,963 이라 기본자본형도 이 분기 하나로는 배제 못 함. 2026.1Q~2026.2Q 누적 점수는 보완자본형 배정이 328, 2026 두 블록을 기본자본형으로 두면 4,404. 보도(IB토마토 2026-06-01, 2차 자료)도 2026-02 사모 4,420억을 '보완자본 인정'으로 분류했다고 같은 결론. 반기보고서에는 스텝업 문구도 분류 문구도 없어 원문으로는 확정 못 함(보도만으로는 ⓐ 불가)",
        treat="consistent(c9: tier2 best; item 47 +4,536 ~ face)",
        note="발행조건상 스텝업이 없는데도 보완자본이라면 '스텝업 없음 = 기본자본' 추정이 DB손보 사모분에는 안 맞는다 - 사모 조건 원문(증권신고서 대체 공시) 필요. 등재부는 5건 모두 tier1(소진율 151.6%); 2026 세 건이 tier2 면 기본자본형 신규 약 8,632 / 한도 11,510 = 약 75%"),
    ("KR0011", "2026-06-09", 4100.0): dict(type="tier2", grade="b", b_strength="moderate", a_basis="", step_up="no(no wording)", ev=["F-KR0011", "C9", "W6", "W5"],
        basis="발행사 K-ICS 표(c9): 2026.2Q 블록(4,389 = 4,100 + 300)을 기본자본형으로 보면 'other' 변화 +2,552(발행 전 최대 1,963 초과), 보완자본형이면 -308 -> 보완자본형 선택; 이 블록만 기본자본형으로 바꾸면 누적 점수가 328 -> 3,188. X=13-49 는 후순위를 포함하지 않아 같은 분기 4,990억 후순위 상환의 영향이 없음(항목 47 은 영향을 받아 이 판정에는 쓰지 않음). 상충: 발행 전 보도(데일리안 2026-05/06)는 '기본자본으로 인정되는 구조'라고 설명 - 보도는 발행 의도, 표는 보고 결과",
        treat="consistent(c9: tier2 for the 2026.2Q block)", note="4,100 과 300 은 같은 분기라 표에서 분리 불가(블록 판정)"),
    ("KR0011", "2026-06-29", 300.0): dict(type="tier2", grade="b", b_strength="weak", a_basis="", step_up="no(no wording)", ev=["F-KR0011", "C9"],
        basis="제4회와 발행조건이 같고(금리 5.30%, 후후순위, 5년 후 조기상환요건) 발행사 표에서는 같은 2026.2Q 블록(4,389) - 300억은 표 잡음(분기 변화 중앙 660)보다 작아 단독 판독은 불가, 블록 판정을 따름",
        treat="block of 2026.2Q (c9)"),
    ("KR0032", "2024-12-27", 4500.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR0032", "R1"],
        basis="사업보고서 '발행금리(금리상향조정조건)': 10년째 +1.00%p step-up -> 보완자본형; 발행사 표 항목 47 +4,330(액면 4,500)", treat="consistent"),
    ("KR0050", "2024-05-14", 1000.0): dict(type="tier2", grade="b", b_strength="strong", a_basis="", step_up="no wording (note has none)", ev=["F-KR0050", "C9", "W8", "R1"],
        basis="주석에 스텝업·이자율 조정 문구가 없어 조건만으로는 확정 불가; 발행사 K-ICS 표(c9): 보완자본형으로 보면 X 에서 신종을 뺀 'other' 가 9분기 내내 -1~52 로 발행 전 밴드 15~39 와 같고 발행 분기 변화 -26(발행 전 변화 최대 16), 기본자본형(한도 초과분만 재분류)이면 발행 분기 변화 +241 이고 누적 점수 2,943 -> 발행액 전액이 보완자본에 가산된 것으로 읽힘(항목 47 도 발행분기 +973 이후 액면 1,000 에 머묾); 발행 전 보도(W8)는 '기본자본으로 바로 적용'이라는 일반론",
        treat="consistent(c9: tier2, other inside the pre-issue band for 9 quarters)", note="보도(일반론)와 발행사 표가 반대 - 사모 계약서/증권신고서 없이는 ⓐ 불가"),
    ("KR0068", "2024-07-17", 5000.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR0068", "R1"],
        basis="사업보고서: 스텝업(Step-up) 조항 - 10년째 가산금리 +1.00%p -> 보완자본형. 발행사 표 항목 47 이 2024.3Q +7,912(2019 신종 5,000 상환과 같은 분기)", treat="consistent"),
    ("KR0068", "2024-09-24", 6000.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR0068", "R1"],
        basis="사업보고서: 스텝업 조항(+1.00%p). 2024.3Q 항목 47 +7,912", treat="consistent"),
    ("KR0068", "2025-03-26", 6000.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR0068", "R1"],
        basis="사업보고서: 스텝업 조항(+1.00%p). 2025.1Q 항목 47 +5,087(액면 6,000)", treat="consistent"),
    ("KR0068", "2025-06-24", 13819.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR0068", "R1"],
        basis="사업보고서: 외화 신종 스텝업 조항(+1.00%p, 美 국채 기준). 2025.2Q 항목 47 +17,876", treat="consistent"),
    ("KR0072", "2023-05-19", 2160.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR0072", "R1"],
        basis="반기·사업보고서: 'Step-Up 포함여부' 10년 경과 후 +1.00%p -> 보완자본형. (같은 분기에 옛 제1회가 상환돼 항목 47 단독 판독은 불가; 항목 6 = 47 이 13분기 내내 일치)", treat="unclear (구 신종 상환과 같은 분기)"),
    ("KR0072", "2024-12-26", 250.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR0072", "R1"],
        basis="사업보고서: Step-Up 조항(+1.00%p) -> 보완자본형. 소액이라 표 판독 불가(항목 47 잡음 -943)", treat="unclear (소액)"),
    ("KR0073", "2023-05-12", 5000.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR0073", "R1"],
        basis="사업보고서: Step-up 조항(10년 경과 후 1% 가산) -> 보완자본형. 발행사 표 항목 47 이 2023.2Q 에 +4,985 로 액면과 정확히 일치", treat="consistent"),
    ("KR0073", "2024-11-12", 6000.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR0073", "R1"],
        basis="사업보고서 L46354: 'Step-up 조항에 따라 발행일로부터 10년이 경과한 이후 1회 상향 조정'(2034-11-12 Step-Up 가산금리 1%) -> 기본자본요건 불충족(R1) -> 보완자본형",
        treat="INCONSISTENT: 발행사 K-ICS 표 항목 47 은 2024.4Q 에 +202, X(13-49) +89 뿐 - 6,000억이 보완자본에 가산되지 않은 것으로 읽힘(= 발행사는 기본자본으로 처리했을 가능성). c9 사건연구: 2024-11 블록을 보완자본형으로 보면 'other' 가 8,310 -> 2,416(-5,894)로 급락, 기본자본형이면 8,310 -> 8,399(+89); 같은 문구의 2023-05 블록은 반대로 보완자본형(변화 0 vs 기본자본형 +4,985)",
        note="규정 해석(스텝업 = 보완자본; 2023-05 건은 같은 문구인데 발행 분기에 X +4,985 로 보완자본 처리됨)과 발행사 K-ICS 처리가 어긋나는 유일한 케이스. 등재부 tier1 은 발행사 처리를 따른 것. 2026-08 보도(W10)는 공통 경과조치 1조1,089억에 2023 이후 신종이 들어 있지 않다고 설명할 뿐 이 건의 분류는 다루지 않음. 발행사 처리의 근거 문서(경영공시 해설·증권신고서)가 필요"),
    ("KR0083", "2023-02-28", 600.0): dict(type="tier2", grade="a", a_basis="issuer_filing(indirect)", step_up="yes(indirect)", ev=["F-KR0083", "R1", "R2"],
        basis="주석 문구: 발행 5년 후 조기상환 + 발행일로부터 10년 경과 후 1회 이자율 조정 - 한화생명·흥국화재가 '스텝업 +1.00%p'로 풀어 쓴 문구와 같다(가산폭은 푸본 주석에 없음). 같은 문구가 2022-11-30 발행분(경과조치 신종)에도 있음. 발행 직후 분기 전기 열이 마스터에 없어 표 판독 불가",
        treat="n/a (2022.4Q 열 없음)"),
    ("KR0097", "2023-03-31", 1800.0): dict(type="tier1", grade="b", b_strength="strong", a_basis="", step_up="no wording (note has none)", ev=["F-KR0097", "C9", "W11", "R1"],
        basis="주석에 '10년 경과 후 이자율 조정' 문구가 없음(다른 발행사 주석에는 있음); 발행사 K-ICS 표 항목 47(1,252~1,884)이 14분기 내내 액면 1,799 보다 작아 전액 보완자본형일 수 없고(c9: 보완자본형 배정은 'other' 가 음수가 되는 분기가 12/13 - 점수 3,586), 한도 10%(417~755) 초과분만 재분류되는 기본자본형 모형이면 'other' 가 28~501 로 자연스러움(점수 0)",
        treat="consistent(tier1: item 47 < face)", note="명시적 '스텝업 없음' 문구나 신평 보고서는 못 찾아 ⓑ. 발행 직후 보도(W11, 출처 'IB업계')는 '콜 미행사 시 금리가 오르는 스텝업 구조'라고 한 줄 서술하나 가산폭·10년 시점 언급이 없고 발행사 주석·K-ICS 표와 어긋나 채택하지 않음 - 증권신고서/투자설명서 원문으로 확정 필요"),
    ("KR0104", "2023-01-31", 2500.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR0104", "R1"],
        basis="사업보고서 L16926: 발행금리(금리상향조정조건) 10년째 최초 가산금리 +1.00%(step-up) -> 보완자본형. 발행 직후 분기 전기 열이 마스터에 없어 표 판독 불가", treat="n/a (2022.4Q 열 없음)"),
    ("KR1000", "2023-03-16", 2500.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR1000", "R1"],
        basis="주석 28: 액면 5.50% '5년 시점 이자율 재산정, 10년 시점 Step up 100bps' -> 보완자본형. 발행 직후 분기 전기 열이 마스터에 없어 표 판독 불가", treat="n/a (2022.4Q 열 없음)"),
    ("KR1000", "2024-10-11", 2300.0): dict(type="tier2", grade="a", a_basis="issuer_filing", step_up="yes", ev=["F-KR1000", "R1"],
        basis="주석 28: 액면 4.27% '10년 시점 Step up 100bps' -> 보완자본형. 2019 발행 구 신종(2,286) 상환과 같은 분기라 표 판독은 혼재(항목 47 +1,709)", treat="unclear (구 신종 상환과 같은 분기)"),
}

# ---------------------------------------------------------------------------------------------------------------- subordinated: exceptions to the rule
SUB_EX = {
    ("KR0072", "2023-06-30"): dict(grade="c", ev=["F-KR0072-guar", "R4", "R3"],
        check="예외 후보: 보증부 후순위(한국산업은행 = 지배기업의 원리금 지급보증) - 후순위성 요건(R4: 지급보증 등 직·간접 지원이 이자 미지급을 보상하면 후순위성 훼손)에 걸릴 수 있어 보완자본 인정 여부 불명"),
    ("KR0049", None): dict(grade="c", ev=["R3"], check="예외 후보: 발행일·권면이 목록에 없는 외화(JPY) 그룹사 사모 후순위(AXA Life Japan) - 만기·후순위성 요건을 확인할 자료 없음"),
    ("KR0076", "2025-03-28"): dict(grade="c", ev=["R3"], check="예외 후보: 주석에 '후순위' 명시 라벨이 없는 사모사채(목록 비고) - 후순위성 확인 필요"),
    ("KR0005", "2026-03-31"): dict(grade="c", ev=["R3"], check="예외 후보: 목록에서 BS 재현으로 도출한 행(콜·금리 없음) - 증권 조건 미확인"),
}

# ---------------------------------------------------------------------------------------------------------------- extra rows (not in the bond lists)
EXTRA = [
    dict(code="KR0002", kind="non-bond (전환우선주)", tier="hybrid-like", name="전환우선주 38,000,000주 (2022-09-28, 비참가·비누적 7%, 존속기간 2032-09-27)", issue_date="2022-09-28", face_eok=1900.0,
         registry_type="tier1", census_type="tier1", grade="b", a_basis="", step_up="n/a", ev=["F-KR0002"],
         basis="발행사 K-ICS 표 항목 6 이 4,231 = 신종 2,341 + 1,890(14분기 일정), 보완자본 재분류 항목(13-49)이 신종 2,341 + 약 60 에 머물러 이 1,890 은 기본자본으로 처리됨; 조건상 존속기간 10년·보통주 전환권이라 영구성 요건 충족 여부는 별도 확인 필요",
         treat="consistent(tier1)"),
    dict(code="KR0071", kind="non-bond (전환우선주)", tier="hybrid-like", name="전환우선주 2,440,579주 (2022-12-29 제3자배정, 비누적·비참가 7.1%)", issue_date="2022-12-29", face_eok=2300.0,
         registry_type="tier1", census_type="tier1", grade="b", a_basis="", step_up="n/a", ev=["F-KR0071-pref"],
         basis="발행사 K-ICS 표 항목 6 이 신종 500 + 2,296~2,300 (2023.1Q~), 경과조치 표는 신종 496.5 만 기본자본으로 옮김; 전환청구 1~10년, 미전환 시 보통주 자동 전환(상환 없음) 이라 기본자본 요건에 가까움",
         treat="consistent(tier1)"),
    dict(code="KR0008", kind="non-bond (우선주)", tier="hybrid-like", name="우선주 (자본금 16.7억 외 항목 6 = 73억 고정)", issue_date="", face_eok=73.0,
         registry_type="tier1", census_type="tier1", grade="c", a_basis="", step_up="n/a", ev=["F-KR0008-pref"],
         basis="발행사 항목 6 = 73억(14분기 고정)이나 우선주 자본금은 16.7억 - 나머지 구성을 공시하지 않아 증권 단위 확정 불가(결과 영향 0.5%)", treat="n/a"),
    dict(code="KR0005", kind="non-bond (우선주)", tier="hybrid-like", name="우선주 921,600주 (자본금 46억, 보통주 전환 조건부)", issue_date="", face_eok=46.0,
         registry_type="tier1", census_type="tier1", grade="b", a_basis="", step_up="n/a", ev=["F-KR0005-pref"],
         basis="사업보고서 우선주 자본금 4,608백만원 = K-ICS 항목 6 의 46억(2023.1Q~2024.4Q) 일치; 신종 재분류에 가산되지 않음", treat="consistent(tier1)"),
    dict(code="KR0083", kind="non-bond (우선주)", tier="hybrid-like", name="우선주 1,000,000주 (자본금 50억, 7%, 이사회 결의 상환)", issue_date="", face_eok=50.0,
         registry_type="tier1", census_type="tier1", grade="c", a_basis="", step_up="n/a", ev=["F-KR0083-pref"],
         basis="사업보고서 우선주 자본금 50억 = K-ICS 항목 6 +50(2024.4Q~)과 일치하나 이사회 결의 상환 조항이 있어 기본자본 요건(영구성) 충족 여부 불명", treat="n/a"),
    dict(code="KR0004", kind="non-bond (전환우선주)", tier="hybrid-like", name="전환우선주 7,273,000주 (우선주 자본금 36.4억, 10년 후 전환권)", issue_date="", face_eok=161.0,
         registry_type=None, census_type="tier1", grade="c", a_basis="", step_up="n/a", ev=["F-KR0004-pref"],
         basis="K-ICS 항목 6 = 36(2023.1Q) -> 161(2023.2Q~2025.2Q) -> 0(2025.3Q, 계약이전)인데 우선주 자본금은 36.4억 - 161억의 구성은 발행사가 공시하지 않음; 신종 아님", treat="n/a"),
    dict(code="KR0076", kind="non-bond (전환우선주)", tier="hybrid-like", name="전환우선주 7,600,000주 (2022 발행, 자본금 380억 + 자본잉여금 1,137.18억 = 1,517.18억, 보유 = 더하이스트제이십삼차㈜)", issue_date="2022", face_eok=1517.2,
         registry_type="legacy_tfi", census_type="legacy_tfi", grade="a", a_basis="issuer_filing + K-ICS table (item 53)", step_up="n/a", ev=["F-KR0076-pref", "F-KR0076", "R2"],
         basis="2022 사업연도 감사보고서 주석: '우선주 발행' 자본금 380억 + 자본잉여금 1,137.18억 = 1,517.18억(자본변동표·현금흐름표), 신종 948.8 과 합치면 2,465.98 = 발행사 K-ICS 항목 6 · 53(14분기 일정) -> 시행일 전(2022) 발행분을 발행사가 기발행 신종(경과조치 (1))으로 보고. 주식은 DGB금융지주 종속기업 SPC(더하이스트제이십삼차㈜)가 보유; 정확한 발행일·조건(배당률·전환·상환)은 이 파일에 없음",
         treat="consistent(TFI table row 53)", note="이전 판의 '증권 특정 불가'는 신종 주석만 본 탓 - 2022 감사보고서로 특정됨. SPC 보유 구조(그룹 지원 여부)는 이 자료로 판단 못 함"),
    dict(code="KR0050", kind="registry-only hybrid", tier="hybrid", name="2026.2Q 신규 신종 +999억 (채권원장 미등재)", issue_date="2026-06-30", face_eok=999.0,
         registry_type="tier2", census_type="tier2", grade="b", b_strength="strong", a_basis="", step_up="unknown", ev=["F-KR0050", "C9"],
         basis="발행사 K-ICS 표 항목 47 이 2026.2Q 에 +992 (액면 999) - 제1회(2024-05)와 같은 모양; c9 사건연구: 기본자본형이면 'other' 변화 +460, 보완자본형이면 -7(발행 전 변화 최대 16); 증권명·발행조건은 DART 목록에 아직 없음", treat="consistent(c9: tier2)"),
    dict(code="KR0068", kind="historical (redeemed)", tier="hybrid", name="2019-07-04 발행 신종 5,000억 (3.69%, 스텝업 있음)", issue_date="2019-07-04", face_eok=5000.0,
         registry_type=None, census_type="legacy_tfi", grade="a", a_basis="issuer_filing+K-ICS table", step_up="yes", ev=["F-KR0068-2019", "R2"],
         basis="2023.2Q~2024.2Q 반기·사업보고서에 있다가 2024-07 콜 가능일 이후 사라짐(상환); 항목 53 이 2023.1Q 18,668 -> 2024.2Q 4,983 -> 0 으로 줄어든 계단과 일치. 옛 목록(2025·2026)에는 없음", treat="n/a"),
    dict(code="KR0082", kind="historical (redeemed)", tier="hybrid", name="2017-11-13 발행 신종 약 300억 (DB생명)", issue_date="2017-11-13", face_eok=300.0,
         registry_type=None, census_type="legacy_tfi", grade="a", a_basis="issuer_filing+K-ICS table", step_up="unknown", ev=["F-KR0011-DBlife"],
         basis="FY2023_Q1 보고서에 2017-11-13 발행분(30,000백만원)이 제2회와 나란히 있고, 항목 53 이 2023.1Q 697 -> 2023.2Q 398.39 로 297 줄어 상환과 일치", treat="n/a"),
    dict(code="KR0011", kind="subsidiary instrument", tier="hybrid", name="(DB생명 제2회 신종 400억을 DB손보 K-ICS 항목 6·53 에 포함: 2023.1Q 697 / 2023.2Q~2025.1Q 398.39)", issue_date="2020-03-31", face_eok=400.0,
         registry_type=None, census_type="legacy_tfi", grade="b", a_basis="", step_up="yes (DB생명 제2회)", ev=["F-KR0011-DBlife", "F-KR0082"],
         basis="DB손보 자신의 신종은 2025-09 까지 없는데 DB손보 K-ICS 항목 6 · 53 이 DB생명(KR0082)의 같은 값을 쥐고 있음 - 발행사 표 자체의 포함 범위 문제로 보이며 마스터는 인쇄값 그대로", treat="n/a"),
    dict(code="KR0009", kind="historical (redeemed)", tier="hybrid", name="현대해상 신종 약 5,000억 (이름·발행일 미확인)", issue_date="", face_eok=5000.0,
         registry_type=None, census_type="legacy_tfi", grade="b", a_basis="", step_up="unknown", ev=[],
         basis="K-ICS 항목 53 = 5,000 / 항목 6 = 4,983 이 2023.2Q 까지 있다가 2023.3Q 에 0(상환); 2023 이전 보고서가 로컬에 없어 증권명·발행일은 못 찾음", treat="n/a"),
    dict(code="KR0002", kind="historical (redeemed)", tier="hybrid", name="한화손보 신종 약 1,885억 (이름·발행일 미확인)", issue_date="", face_eok=1885.0,
         registry_type=None, census_type="legacy_tfi", grade="b", a_basis="", step_up="unknown", ev=[],
         basis="항목 53 = 4,235(2023.1Q~2Q) -> 2,341.05(2023.3Q~): 1,885억이 2023.3Q 에 줄어 상환과 일치; 2023 이전 보고서 부재로 증권명 미확인", treat="n/a"),
    dict(code="KR1000", kind="historical (redeemed)", tier="hybrid", name="코리안리 신종 약 2,286억 (2019 발행 원화 신종으로 추정)", issue_date="2019", face_eok=2286.0,
         registry_type=None, census_type="legacy_tfi", grade="b", a_basis="", step_up="unknown", ev=[],
         basis="항목 53 = 5,586(2023.1Q~2024.3Q) -> 3,291.75(2024.4Q): 2,294억 감소 = 제6회(2024-10-11, 2,300억) 차환 시점; 공개 보도(2019 이사회 결의: 2014 USD 2억 조기상환 + 원화 약 2,300억 신규 발행)와 부합, 로컬 보고서에는 없음", treat="n/a"),
    dict(code="KR0072", kind="historical (redeemed)", tier="hybrid", name="KDB생명 구 제1회 신종 약 2,160억 (2023-05-19 제2회로 차환)", issue_date="", face_eok=2160.0,
         registry_type=None, census_type="legacy_tfi", grade="b", a_basis="", step_up="unknown", ev=["F-KR0072"],
         basis="항목 53 = 2,160(2023.1Q~2Q) -> 0(2023.3Q~); 같은 분기에 제2회 2,160 이 발행됨", treat="n/a"),
    dict(code="KR0079", kind="historical (redeemed)", tier="hybrid", name="미래에셋생명 신종 약 1,056억 (이름·발행일 미확인)", issue_date="", face_eok=1056.0,
         registry_type=None, census_type="legacy_tfi", grade="b", a_basis="", step_up="unknown", ev=[],
         basis="K-ICS 항목 6 = 1,056(2023.1Q) -> 0(2023.2Q); 2023.1Q 보고서가 로컬에 없어 증권명 미확인", treat="n/a"),
]


rows_out = []
# evidence ids of the issuer's own K-ICS series (generated further below as K-<code>) exist for every company that has item 6 or 53 values
HAS_K = {c for c in {r["code"] for r in inv} if item_series(c, 53) or item_series(c, 6)}
LEG_EXTRA_EV = {"KR0076": ["F-KR0076", "F-KR0076-pref"]}


def kev(code):
    return [f"K-{code}"] if code in HAS_K else []


for r in inv:
    code, tier, d, face = r["code"], r["tier"], r["issue_date"], r["face_eok"]
    base = {
        "code": code, "company": NAMES.get(code, r["company"]), "kind": "bond", "tier": tier, "name": r["name"], "issue_date": d or "", "call_date": r["call_date"] or "",
        "legal_maturity": r["legal_maturity"] or "", "coupon_pct": r["coupon_pct"], "face_eok": face, "outstanding_eok": r["outstanding_eok"], "as_of": r["as_of"] or "",
        "status": r["status"], "registry_type": r["registry_type"], "registry_unconfirmed": r["registry_unconfirmed"],
        "ledger_tier1_eok": r["ledger_tier1_eok"], "ledger_tier2_eok": r["ledger_tier2_eok"],
    }
    if tier == "hybrid":
        if (d or "9999") < "2023-01-01":
            step, evs = LEG_STEP.get(code, ("unknown", []))
            red = (r["outstanding_eok"] == 0)
            base.update(census_type="legacy_tfi", grade="a", a_basis="issuer_filing + K-ICS table (item 53)", step_up=step,
                        basis=f"발행일 {d} < 2023-01-01(시행일 전 발행) -> 공통적용 경과조치 (1) 대상. {LEG_NOTES.get(code, '')}"
                              + (" [상환 완료/미잔존]" if red else ""),
                        ev=";".join(["R2"] + evs + LEG_EXTRA_EV.get(code, []) + kev(code)), issuer_treatment="consistent(TFI table row 53)", note="")
        else:
            dec = POST.get((code, d, face))
            if dec is None:
                raise SystemExit(f"no decision for post-2022 hybrid {(code, d, face)}")
            base.update(census_type=dec["type"], grade=dec["grade"], b_strength=dec.get("b_strength", ""), a_basis=dec.get("a_basis", ""), step_up=dec["step_up"], basis=dec["basis"],
                        ev=";".join(dec["ev"] + kev(code)), issuer_treatment=dec.get("treat", ""), note=dec.get("note", ""))
    else:  # subordinated
        ex = SUB_EX.get((code, d or None))
        legacy = bool(d) and d < "2023-01-01"
        t = "tier2_legacy(TFI (2))" if legacy else "tier2"
        flags = []
        if r["outstanding_eok"] == 0:
            flags.append("상환 완료/미잔존")
        if r["call_date"] and r["outstanding_eok"] and r["call_date"] < "2026-06-30":
            flags.append("콜 도래 후 잔존(보완자본 잔존만기 체감 대상)")
        if any(k in r["name"] for k in ("외화", "JPY", "USD", "해외")):
            flags.append("외화")
        if ex:
            base.update(census_type="unknown", grade=ex["grade"], a_basis="", step_up="n/a", basis=ex["check"], ev=";".join(ex["ev"]), issuer_treatment="", note=" / ".join(flags))
        else:
            chk = "예외 없음(법적 후순위·무보증·만기 10년·5년 콜)" if not flags else "예외 없음(" + ", ".join(flags) + ")"
            if legacy:
                base_basis = (f"발행일 {d} < 2023-01-01: 종전 규정 보완자본 후순위채 -> 공통적용 경과조치 (2)로 보완자본 한도와 무관하게 인정(R2). {chk}")
            else:
                base_basis = f"시행일 후 발행 후순위(법적 후순위, 5년 콜): 보완자본요건 충족(R3), 보완자본 한도(총요구자본 50%) 내에서 인정. {chk}"
            base.update(census_type=t, grade="a", a_basis="regulation", step_up="n/a", basis=base_basis, ev="R2;R3" if legacy else "R3", issuer_treatment="", note=" / ".join(flags))
    rows_out.append(base)

for e in EXTRA:
    rows_out.append({
        "code": e["code"], "company": NAMES.get(e["code"], e["code"]), "kind": e["kind"], "tier": e["tier"], "name": e["name"], "issue_date": e["issue_date"], "call_date": "",
        "legal_maturity": "", "coupon_pct": None, "face_eok": e["face_eok"], "outstanding_eok": None, "as_of": "", "status": "추가 발견(채권 목록 밖)",
        "registry_type": e["registry_type"], "registry_unconfirmed": None, "ledger_tier1_eok": None, "ledger_tier2_eok": None,
        "census_type": e["census_type"], "grade": e["grade"], "b_strength": e.get("b_strength", ""), "a_basis": e["a_basis"], "step_up": e["step_up"], "basis": e["basis"],
        "ev": ";".join(e["ev"] + kev(e["code"])), "issuer_treatment": e.get("treat", ""), "note": "",
    })

# ---------------------------------------------------------------------------------------------------------------- registry comparison
def norm_reg(x):
    return {"legacy_tfi": "legacy_tfi", "tier1": "tier1", "tier2": "tier2", None: None}.get(x, x)


for r in rows_out:
    ct, rt = r["census_type"], norm_reg(r["registry_type"])
    r["tier_family"] = "tier2" if str(ct).startswith("tier2") else ct
    if r["tier"] == "subordinated":
        r["mismatch"] = ""  # the registry does not hold subordinated bonds
        r["mismatch_note"] = "등재부 대상 아님(후순위)"
        continue
    if rt is None:
        r["mismatch"] = "registry-absent"
        r["mismatch_note"] = "등재부에 없음(상환·이력 증권 또는 채권 목록 밖 항목)"
    elif ct == rt:
        r["mismatch"] = "same"
        r["mismatch_note"] = ""
    elif ct == "unknown":
        r["mismatch"] = "census-unknown"
        r["mismatch_note"] = f"등재부 {rt}{'(미확정)' if r['registry_unconfirmed'] else ''} 인데 census 는 확정 못함"
    else:
        r["mismatch"] = "DIFFERENT"
        r["mismatch_note"] = f"등재부 {rt}{'(미확정, 보수적 상한)' if r['registry_unconfirmed'] else ''} vs census {ct}"

# ---------------------------------------------------------------------------------------------------------------- write outputs
cols = ["code", "company", "kind", "tier", "name", "issue_date", "call_date", "legal_maturity", "coupon_pct", "face_eok", "outstanding_eok", "as_of", "status",
        "registry_type", "registry_unconfirmed", "census_type", "grade", "b_strength", "a_basis", "step_up", "issuer_treatment", "mismatch", "mismatch_note", "basis", "ev", "note",
        "ledger_tier1_eok", "ledger_tier2_eok"]
rows_out.sort(key=lambda x: (x["code"], 0 if x["tier"] != "subordinated" else 1, x["issue_date"] or "9999", x["name"]))
with open(HERE / "census_securities.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows_out)
(HERE / "census_securities.json").write_text(json.dumps(rows_out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

# evidence table: static evidence + generated K-ICS series evidence
ev_rows = [dict(id=e["id"], kind=e["kind"], strength=e["strength"], date=e["date"], source=e["src"], statement=e["statement"]) for e in EVIDENCE]
for code in sorted({r["code"] for r in rows_out if r["tier"] != "subordinated"}):
    s53, s6, s47 = item_series(code, 53), item_series(code, 6), item_series(code, 47)
    if not (s53 or s6):
        continue
    ev_rows.append(dict(id=f"K-{code}", kind="KICS", strength="inference", date="2023.1Q-2026.2Q",
                        source="kics_disclosure.json (issuer 경영공시 4-2 지급여력비율 표; census_reconcile.csv / census_issue_quarter_test.csv)",
                        statement=f"{NAMES.get(code, code)} 항목 6={compress(s6) or '-'} | 항목 53(기발행 신종)={compress(s53) or '-'} | 항목 47(보완자본 한도 적용 전)={compress(s47) or '-'} (억원, 연속 동일값 압축)"))
with open(HERE / "census_evidence.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "kind", "strength", "date", "source", "statement"])
    w.writeheader()
    w.writerows(ev_rows)

# mismatch list
mm = [r for r in rows_out if r["mismatch"] in ("DIFFERENT", "census-unknown")]
with open(HERE / "census_mismatch.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["code", "company", "issue_date", "face_eok", "name", "registry_type", "registry_unconfirmed", "census_type", "grade", "mismatch", "mismatch_note",
                                       "issuer_treatment", "basis", "ev", "ledger_tier1_eok", "ledger_tier2_eok"], extrasaction="ignore")
    w.writeheader()
    w.writerows(mm)

# ---------------------------------------------------------------------------------------------------------------- summary
H = [r for r in rows_out if r["tier"] == "hybrid" and r["kind"] == "bond"]
S = [r for r in rows_out if r["tier"] == "subordinated"]
X = [r for r in rows_out if r["kind"] != "bond"]


def fmtf(x):
    return "-" if x is None else f"{x:g}"


def cnt(rs, key="grade"):
    c = Counter(r[key] for r in rs)
    return f"ⓐ {c.get('a', 0)} / ⓑ {c.get('b', 0)} / ⓒ {c.get('c', 0)}"


lines = []
lines.append("신종자본증권·후순위채 분류 전수조사 (parser-kics, 티켓 20261012T1230Z, 2026-10-12)")
lines.append("")
lines.append(f"전수 건수: 채권 목록 {len(H) + len(S)}건 = 신종 {len(H)} + 후순위 {len(S)}  (27개사; 47사 중 20사는 채권 없음)  + 목록 밖 추가 발견 {len(X)}건")
lines.append(f"확정도: 신종 채권 {cnt(H)} | 후순위 {cnt(S)} | 추가 발견 {cnt(X)} | 합계 {cnt(rows_out)}")
a_h = Counter(r["a_basis"] for r in H if r["grade"] == "a")
lines.append("신종 ⓐ 의 근거 종류: " + ", ".join(f"{k or '-'} {v}" for k, v in a_h.most_common()))
b_h = Counter(r.get("b_strength") or "-" for r in H if r["grade"] == "b")
lines.append("신종 ⓑ 의 강도(c9 정량 검정 기준): " + ", ".join(f"{k} {v}" for k, v in b_h.most_common()) + "  (strong = 반대 가설이 불가능/발행 전 밴드 밖, moderate = 한 분기 변화만으로는 못 가르나 누적·보도가 같은 쪽, weak = 같은 블록의 소액)")
lines.append(f"후순위 ⓐ 는 전부 규정 적용(근거: 법적 후순위 + 보완자본요건 R3 / 경과조치 (2) R2). 예외 후보(ⓒ) {sum(1 for r in S if r['grade'] == 'c')}건: " +
             "; ".join(f"{r['company']} {r['issue_date'] or '(발행일 없음)'}" for r in S if r["grade"] == "c"))
ty = Counter(r["census_type"] for r in H)
lines.append("신종 분류 분포: " + ", ".join(f"{k} {v}" for k, v in sorted(ty.items())))
post = [r for r in H if (r["issue_date"] or "9999") >= "2023-01-01"]
lines.append(f"  - 시행일(2023-01-01) 후 발행 신종 {len(post)}건: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(r['census_type'] for r in post).items())) + f" | 확정도 {cnt(post)}")
dif = [r for r in rows_out if r["mismatch"] == "DIFFERENT"]
unk = [r for r in rows_out if r["mismatch"] == "census-unknown"]
lines.append(f"등재부(capital_tier_registry.json) 대비: 같음 {sum(1 for r in rows_out if r['mismatch'] == 'same')}건 · 다름 {len(dif)}건 · census 가 확정 못 함 {len(unk)}건 · 등재부 없음 {sum(1 for r in rows_out if r['mismatch'] == 'registry-absent')}건")
lines.append("")
lines.append("[불일치 목록: 등재부를 고치지 않고 보고]")
for r in dif + unk:
    lines.append(f"  - {r['company']} {r['issue_date'] or ''} {fmtf(r['face_eok'])}억 {r['name'][:30]}: {r['mismatch_note']} (확정도 {r['grade']}; 발행사 처리 {r['issuer_treatment'][:60]})")
inc = [r for r in rows_out if str(r["issuer_treatment"]).startswith("INCONSISTENT")]
lines.append("")
lines.append("[발행조건(규정 해석)과 발행사 K-ICS 표 처리가 어긋나는 증권]")
for r in inc:
    lines.append(f"  - {r['company']} {r['issue_date']} {fmtf(r['face_eok'])}억: {r['issuer_treatment']}")
lines.append("")
# ledger comparison
tier2_h = [r for r in H if r["census_type"] == "tier2"]
led_t1 = sum((r["ledger_tier1_eok"] or 0) for r in tier2_h)
lines.append(f"참고: 옛 화면 채권원장(kics_capital_securities.json)은 census 가 보완자본형(tier2)으로 본 신종 {len(tier2_h)}건 중 {sum(1 for r in tier2_h if (r['ledger_tier1_eok'] or 0) > 0)}건에 기본자본 인정액 합계 {led_t1:,.0f}억을 잡고 있었다(소진율 도넛 분자 과대).")
lines.append("")
lines.append("[범위와 한계]")
lines.append("  - 전수의 기준 = 채권 목록(2025-12-31 사업보고서 + 2026-06-30 반기보고서 + 2026.1Q 증권별 표 + 옛 화면 원장)과 K-ICS 항목 6·53 (census_reconcile.txt). 상환 완료된 과거 후순위채는 넣지 않았다.")
lines.append("  - 후순위 쪽 점검: 항목 54(기발행 후순위채무)는 경과조치 (2) 적용 여부에 따라 회사마다 뜻이 달라 목록과 일대일로 안 맞는다(census_reconcile_sub.txt). 다만 2025.4Q 이후 항목 54 가 목록 액면 합계를 넘는 회사는 악사(발행일 없는 JPY 후순위 약 340억 - 목록에 있음)·DB생명(+136)·흥국생명(2025.4Q +157)뿐이라 목록 밖 현존 후순위의 증거는 없다.")
lines.append("  - 근거 등급: ⓐ = 발행사 공시(사업보고서·주석·발행사 K-ICS 표 항목 53)·규정 원문·신평사 보고서(보도로 전달된 1건 포함)가 분류 또는 스텝업을 직접 말함 / ⓑ = 발행사 K-ICS 표의 시계열 검정(c9; 항목 13-49, 14, 53, 6)이 한쪽을 가리킴 / ⓒ = 불명·상충. 보도만으로는 ⓐ 를 주지 않았다.")
lines.append("  - 공개 자료는 WebSearch/WebFetch 로 본 언론·신평 요약만 썼다(go.kr·law.go.kr·KIPRIS 미사용). 증권신고서·사모 계약서 원문은 열지 못했다 - ⓑ 증권의 ⓐ 승급에는 그 원문이 필요하다.")
lines.append("")
lines.append("[재현 순서] (저장소 루트에서, python = C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe)")
lines.append("  c1_inventory.py -> c2_reconcile.py -> c2b_sub_reconcile.py -> c3_dart_sections.py -> c3b_extract_terms.py -> c4_evidence_from_dart.py -> c5_issue_quarter_test.py -> c7_classify.py -> c9_x_band_test.py -> c8_registry_crosstab.py -> c10_selfcheck.py(내부 일관성 14항 PASS)")
lines.append("  (c6_evidence.py = 근거 표 데이터, c7 이 import / dart_text.py = DART XML 텍스트 변환 도우미. 모든 스크립트는 저장소 파일을 읽기만 하고 이 폴더에만 쓴다.)")
lines.append("")
lines.append("[회사별 한 줄]")
by = defaultdict(list)
for r in rows_out:
    by[r["code"]].append(r)
for code in sorted(NAMES):
    rs = by.get(code, [])
    if not rs:
        lines.append(f"  {code} {NAMES[code]}: 신종·후순위 없음(채권 목록 기준)")
        continue
    hb = [r for r in rs if r["tier"] == "hybrid" and r["kind"] == "bond"]
    sb = [r for r in rs if r["tier"] == "subordinated"]
    xb = [r for r in rs if r["kind"] != "bond"]
    parts = []
    if hb:
        c = Counter(r["census_type"] for r in hb)
        gr = Counter(r["grade"] for r in hb)
        parts.append("신종 " + "·".join(f"{k} {v}" for k, v in sorted(c.items())) + f" [{cnt(hb)}]")
    if sb:
        parts.append(f"후순위 {len(sb)}건 보완자본 [{cnt(sb)}]")
    if xb:
        parts.append("추가 " + "·".join(f"{r['kind'].split(' ')[0]}:{r['census_type']}({r['grade']})" for r in xb))
    flag = ""
    if any(r["mismatch"] in ("DIFFERENT", "census-unknown") for r in rs):
        flag = "  <== 등재부와 다른/미확정 있음"
    lines.append(f"  {code} {NAMES[code]}: " + " | ".join(parts) + flag)
(HERE / "census_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
