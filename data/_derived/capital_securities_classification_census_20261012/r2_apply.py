"""r2_apply.py (parser-kics, ticket 20261012T2000Z, round 2) -- READ ONLY on every repo file; writes only next to this script, under NEW names
(the round-1 files census_securities.* / census_mismatch.csv / census_summary.txt / census_evidence.csv are not touched).

Input : census_securities.json (round 1, 149 rows), c6_evidence.py (round-1 evidence), r2_evidence.py (round-2 evidence),
        data/bonds/capital_tier_registry.json (only to re-read the registry type; NEVER written), kics_disclosure.json (item 6 / 53 at 2026.2Q, read only).
Owner decisions applied (ticket items 1-3, 2026-10-12):
  1. rows of redeemed / zero-balance / name-unknown history are marked 'excluded_owner' (not counted)
  2. preferred shares, convertible preferred shares and group-held instruments move to the 'item6_other' sheet (not counted as hybrid / subordinated)
  3. every subordinated bond is tier2 by default; the 'exception candidate' flag is removed (4 rows), counter-evidence is only recorded
  4. DB Non-life 5 hybrids = tier1, grade a (owner excerpt O1; press W12-W18)
  5. Hana Non-life 2 hybrids = tier2, grade a (owner excerpt O2); Hana Life 제1회 = tier2, grade a (owner excerpt O3 = W11), registry mismatch kept as one note
Outputs (all in this folder):
  census_securities_r2.csv/json   full 149-row table with scope + round-2 classification + round-1 values kept (r1_*)
  census_securities_final.csv     one line per in-scope hybrid bond (company, issue date, face, classification, grade, evidence one-liner)
  census_item6_other_r2.csv       the 'item 6 reconciliation only' sheet (preferred shares etc.)
  census_excluded_owner_r2.csv    the excluded rows with the reason
  census_mismatch_r2.csv          mismatch against data/bonds/capital_tier_registry.json (corrected)
  census_newly_confirmed_r2.csv   securities that moved up in round 2, with source ids / urls / search numbers
  census_evidence_r2.csv          round-1 evidence + round-2 evidence (ids)
  census_item6_check_r2.txt       K-ICS item 6 at 2026.2Q against the in-scope hybrid list (completeness check, information only)
  census_summary_r2.txt           counts, mismatches, new confirmations, limits
  r2_search_log.txt               every WebSearch call of this run
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/r2_apply.py
"""
from __future__ import annotations

import copy
import csv
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
from c6_evidence import EVIDENCE as EV1  # noqa: E402
from r2_evidence import EVIDENCE_R2, EV2, SEARCH_LOG  # noqa: E402

base = json.loads((HERE / "census_securities.json").read_text(encoding="utf-8"))
reg = json.loads((REPO / "data/bonds/capital_tier_registry.json").read_text(encoding="utf-8"))
kd = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))

# ------------------------------------------------------------------------------------------------------------------------------ scope
EXCL_HIST = "이력(상환 완료 · 증권명/발행일 미확인 포함) - 이미 상환된 건은 제외(owner 2026-10-12)"
EXCL_ZERO = "잔액 0(상환 완료) - 제외(owner 2026-10-12)"
EXCL_H1 = "2025-12-31 목록에만 있고 2026-06-30 목록에서 빠짐 = 2026 상반기 중 상환(콜 도래일이 2026 상반기) - 제외(owner 2026-10-12). 근거: "
H1_EVID = {  # company-level notes of data/bonds/capital_securities_fy2026h1.json (the H1 builder), read 2026-10-12
    "KR0009": "H1 빌더 회사 메모 '반기 중 상환 1건 제거 (H1 증거 부재 + BS 당반기말 재현 이중확인)'",
    "KR0010": "H1 빌더 회사 메모 '반기 중 상환 1건 제거 (H1 증거 부재 + BS 당반기말 재현 이중확인)'",
    "KR0079": "H1 빌더 회사 메모 '반기 중 상환 1건 제거 (H1 증거 부재 + BS 당반기말 재현 이중확인)'",
    "KR0011": "H1 빌더 회사 메모 'redeemed bond confirmed & dropped' + 보도 W6(6월 만기 4,990억 후순위 상환)·W15(콜 행사)",
    "KR0005": "H1 빌더 회사 메모는 제거 0건이나 BS 당반기말 319,060 이 제21회 200억 + 제22회 2,000억 + 신규 1,000억(할인차금 약 9억 차)으로 재현되어 제20회 450억이 BS 에 없음",
}
ITEM6_WHY = "채권이 아닌 항목(우선주 · 전환우선주 · 그룹사 포함분): 신종/후순위 건수에 안 센다. K-ICS 항목 6(보통주 이외 자본증권) 대사용 별표(owner 2026-10-12)"
SCOPE_LABEL = {"in_scope": "집계 대상", "excluded_owner": "제외(owner)", "item6_other": "항목 6 대사용 기타(우선주 등)"}


def scope_of(r):
    if r["kind"] == "historical (redeemed)":
        return "excluded_owner", EXCL_HIST
    if r["kind"] == "bond" and r["outstanding_eok"] == 0:
        return "excluded_owner", EXCL_ZERO
    if r["status"].startswith("fy2025 목록에만 있음"):
        return "excluded_owner", EXCL_H1 + H1_EVID[r["code"]]
    if r["kind"] in ("non-bond (전환우선주)", "non-bond (우선주)", "subsidiary instrument"):
        return "item6_other", ITEM6_WHY
    return "in_scope", ""


# ------------------------------------------------------------------------------------------------------------------------------ round-2 decisions
# key = (code, issue_date, face_eok) of the round-1 row.  Fields not listed stay as in round 1.
HYB = {
    ("KR0011", "2025-09-01", 7470.0): dict(
        ev_add=["O1"], a_basis="press_of_rating_report", change="",
        oneline="신평 보도(한신평·한기평 AA '기본자본 신종(비조건부)'): 스텝업 삭제·발행사 이자지급 재량; 3.80% 단일, 조정 문구 없음 [W3,W4,W1,F-KR0011]"),
    ("KR0011", "2025-09-25", 1200.0): dict(
        census_type="tier1", grade="a", a_basis="press+rating_report", step_up="no", b_strength="", ev_add=["W12", "W18", "O1"],
        change="R2: ⓑ→ⓐ(tier1 유지). 2025-09-25 보도(W12)가 공모·사모 둘 다 스텝업이 없어 기본자본 확충이라고 직접 서술, 신평 보고서(W18)가 2025년 기본자본 신종 8,670억(= 7,470 + 1,200)을 말함",
        oneline="제1회와 같은 조건(3.80% 단일, 스텝업 문구 없음); 2025-09-25 보도: 공모·사모 모두 스텝업 없어 기본자본 확충, 신평 보고서: 2025년 기본자본 신종 8,670억(=7,470+1,200) [W12,W18,F-KR0011]"),
    ("KR0011", "2026-02-11", 4420.0): dict(
        census_type="tier1", grade="a", a_basis="owner_directed(press excerpt O1)", step_up="no", b_strength="", ev_add=["O1", "W13"],
        change=("R2: tier2(ⓑ)→tier1(ⓐ, owner 지시). 1차 판정 근거는 발행사 표 검정(c9, moderate)과 W5('보완자본 인정') 였으나 owner 가 가져온 기사(O1)와 'DB 신종 5건 = 기본자본형' 결정을 따름. "
                "이 건 하나만 직접 다룬 기사는 못 찾음. 반대 방향 신호 둘: W5 는 이 건을 '보완자본 인정'이라 쓰고 W14 는 2026-06 건을 2025 이후 '두 번째' 기본자본 신종으로 센다(2월 사모분을 안 센 셈). "
                "W5 의 표현은 기본자본형 총량(제1~3회 13,090억)이 10% 한도를 넘어 초과분(등재부 evidence: 2026.1Q 약 3,196억)이 보완자본으로 재분류된 부분을 가리킬 수 있으나 이것은 추정이다"),
        oneline="owner 지시: DB 신종 5건 전부 기본자본형(O1, 원문 기사 미특정); 4.40% 단일·스텝업 문구 없음 [F-KR0011]. 건별 직접 보도 없음; W5('보완자본 인정')·W14(6월 건을 '두 번째'로 셈)·표 검정(c9)은 반대 방향 신호이나 10% 한도 초과분 재분류와 구분 불가"),
    ("KR0011", "2026-06-09", 4100.0): dict(
        census_type="tier1", grade="a", a_basis="press+prospectus(per search summary)+owner_directed", step_up="no", b_strength="", ev_add=["O1", "W14", "W15", "W16"],
        change=("R2: tier2(ⓑ)→tier1(ⓐ). 증권신고서(W16)·IB토마토 '기본자본 또 발행'(W14)·FETV(W15)가 이 건을 기본자본 신종(2호)으로 서술하고 owner 지시와 일치. "
                "발행사 표 검정(c9)은 2026.2Q 블록(4,389)을 보완자본 쪽으로 읽으나 한도 초과분 재분류와 구분되지 않아 기각하지 않고 메모로 남김"),
        oneline="증권신고서(2026-05-27)·IB토마토 '기본자본 또 발행'·FETV: 기본자본 신종 2호, 5.30% 단일 [W16,W14,W15]; owner 지시와 일치. c9 는 2026.2Q 블록(4,389)을 보완자본 쪽으로 읽으나 한도 초과 재분류와 구분 불가"),
    ("KR0011", "2026-06-29", 300.0): dict(
        census_type="tier1", grade="a", a_basis="owner_directed(press excerpt O1)+same program as 제4회", step_up="no", b_strength="", ev_add=["O1", "W17"],
        change="R2: tier2(ⓑ)→tier1(ⓐ, owner 지시). 제4회와 같은 1.5조 한도 프로그램의 사모 추가분(W17: 2026-06-16 결정, 30년, KB증권 주관). 표에서는 제4회와 한 블록이라 분리 불가",
        oneline="제4회와 같은 조건의 사모(2026-06-16 결정, 1.5조 한도 내) [W17]; owner 지시 tier1; 표는 제4회와 한 블록(분리 불가)"),
    ("KR0050", "2024-05-14", 1000.0): dict(
        census_type="tier2", grade="a", a_basis="owner excerpt O2 + K-ICS table c9 (strong)", step_up="no wording; 배당가능이익 부재로 기본자본 요건 미충족", b_strength="", ev_add=["O2"],
        change="R2: ⓑ→ⓐ. owner 발췌(O2)가 하나손보 신종 2,000억 전부 보완자본 + 이유(스텝업은 없으나 배당가능이익 부재)를 직접 서술하고, 1차의 발행사 표 검정(c9 strong)과 같은 방향. '스텝업 없음만으로 tier1 결론 금지' 원칙의 실제 사례",
        oneline="owner 발췌(O2): 신종 2,000억 전부 보완자본 - 스텝업 문구는 없으나 배당가능이익이 없어 기본자본 요건 미충족; 발행사 표(c9)도 보완자본형(strong) [O2,C9,F-KR0050]"),
    ("KR0097", "2023-03-31", 1800.0): dict(
        census_type="tier2", grade="a", a_basis="owner excerpt O3 (= W11, Asia Economy 2023-04-05)", step_up="yes (press: 콜 미행사 시 금리가 단계적으로 상승)", b_strength="", ev_add=["O3"],
        issuer_treatment="MIXED: 발행사 K-ICS 표(c9)는 부분 기본자본형 모양(항목 47 이 14분기 내내 액면 1,799 미만), DART 주석(F-KR0097)에 스텝업 문구 없음 - owner 지시로 보도의 명시적 스텝업 서술을 따름",
        change=("R2: tier1(ⓑ)→tier2(ⓐ). owner 증거 O3(= W11)의 '콜 미행사 시 금리가 단계적으로 오르는 스텝업 구조'를 따름. "
                "1차는 같은 기사를 읽고도 주석에 스텝업 문구가 없고 발행사 표가 기본자본형 모양이라 채택하지 않았음 -> 상충은 한 줄 메모로 유지, 등재부(tier1)와 새 불일치"),
        oneline="owner 발췌(O3 = 아시아경제 2023-04-05, W11): 5년 후 콜 미행사 시 금리가 단계적으로 오르는 스텝업 구조 -> 보완자본형. 상충 메모: DART 주석(F-KR0097)에 스텝업 문구 없음, 발행사 표(c9)는 부분 기본자본형 모양 - 등재부는 티켓 시점 tier1, 지금은 type=tier2 + issuer_type=tier1"),
}

# the one registry-only row (+999억 in K-ICS item 6 of 2026.2Q) becomes a real bond row: press found date / amount / terms
PROMOTE = dict(
    key=("KR0050", "2026-06-30", 999.0),
    name="하나손해보험 신종자본증권 (2026-06-29 발행, 사모, 하나금융지주 전량 인수; 회차 미확인)", issue_date="2026-06-29", call_date="2031-06-29", legal_maturity="2056-06-29",
    coupon_pct=6.2, face_eok=1000.0, outstanding_eok=1000.0, as_of="2026-06-30", status="보도 확인(DART 목록 밖 - 하나손보 2026 반기 목록 미반영)",
    census_type="tier2", grade="a", b_strength="", a_basis="owner excerpt O2 + press W19-W23 + K-ICS table c9 (strong)", step_up="no wording; 배당가능이익 부재로 기본자본 요건 미충족",
    ev_add=["O2", "W19", "W20", "W21", "W22", "W23"],
    change=("R2: 채권 목록 밖 행('2026.2Q 신규 신종 +999억')을 보도로 확인된 실제 신종으로 승격(발행일 2026-06-29, 액면 1,000억 - K-ICS 항목 6 증가 +999, 연 6.20%, 만기 2056-06-29, 5년 후 콜, 하나금융 전량 인수). ⓑ→ⓐ"),
    oneline="제1회와 같은 모양: 연 6.20%·만기 2056-06-29·5년 콜·하나금융 전량 인수 [W23,W19]; 보도·owner 발췌: 보완자본 분류 [W20,W21,O2]; c9 보완자본형(strong, 항목 47 +992)",
)

# subordinated bonds that were 'exception candidates' in round 1: owner default tier2, search found no counter-evidence
SUB_DEFAULT = {
    ("KR0049", ""): dict(ev_add=["W-none"], oneline="공개 자료 없음(검색 #27) - 반대 근거도 없음. DART 목록이 '후순위채권'(JPY, AXA Life Japan 사모)으로 적음 + owner 기본값",
                         basis="owner 기본값(후순위 = 보완자본). 검색 #27: 이 JPY 후순위에 대한 공개 보도 없음(찬반 모두) - 발행일·권면 조건은 여전히 DART 목록에 없음"),
    ("KR0072", "2023-06-30"): dict(ev_add=["W28"], oneline="산업은행 지급보증부 10년 후순위 900억; 보도는 자본성증권·전액 자본 인정으로 설명 + owner 기본값",
                                   basis="owner 기본값. 검색 #26(W28): 보증부 후순위 900억, 만기 10년·5년 콜, 보도는 자본성증권으로 분류·자본 인정이라 설명 -> 반대 근거 없음. R4(지급보증이 후순위성을 훼손하는지)는 해석 사항으로 남기고 기본값 적용"),
    ("KR0076", "2025-03-28"): dict(ev_add=["W26"], oneline="보도: 무보증 후순위채 750억, 5.5%, 만기 10년, 사모, 2025-03-28 납입 - 법적 후순위 확인 + owner 기본값",
                                   basis="owner 기본값. 검색 #25(W26): '무보증 후순위채'로 보도(DART 목록에 후순위 라벨이 없던 점 해소) -> 반대 근거 없음"),
    ("KR0005", "2026-03-31"): dict(ev_add=["W27"], oneline="보도: 무보증 후순위사채 1,000억, 만기 10년(2036-03), 5년 후 콜, 최종 5.50%, 발행 예정 2026-03-25 - 법적 후순위 확인 + owner 기본값",
                                   basis="owner 기본값. 검색 #24(W27): 무보증 후순위사채 1,000억, 10년, 5년 후 콜, 5.50% -> 반대 근거 없음. 발행일은 보도 3/25(발행 예정) 대 DART 목록 3/31(BS 재현 도출) - 타 산출과의 키를 안 바꾸려고 issue_date 는 그대로 두고 issue_date_press 에 따로 적음"),
}
ISSUE_DATE_PRESS = {("KR0005", "2026-03-31"): "2026-03-25(보도: 발행 예정일)"}

LEG_PREFIX = "2023-01-01 전 발행 -> 경과조치 (1) 기본자본(15% 한도, ~2032-12-31) [R2]; "
# DART 반기보고서(F-KR0011)의 회차로 이름을 정리: 2026 발행 3건은 목록 이름이 'KR0011 신종자본증권 (발행 ..., H1 2026 신규확인)' 이라 회차를 못 알아봄
NAME_R2 = {
    ("KR0011", "2026-02-11", 4420.0): "제3회 신종자본증권 (사모, 2026-02-11)",
    ("KR0011", "2026-06-09", 4100.0): "제4회 신종자본증권 (공모, 2026-06-09)",
    ("KR0011", "2026-06-29", 300.0): "제5회 신종자본증권 (사모, 2026-06-29)",
}

# post-2022 hybrids that round 1 left unchanged: one-liners (round-1 decision, ids in brackets)
HYB_KEEP_ONELINE = {
    ("KR0005", "2025-03-21", 2000.0): "사업보고서: 5년째 조정 후 10년째 직후 가산금리 +1.00%p(스텝업) -> 기본자본요건 불충족(R1) -> 보완자본형; 발행사 표 항목 47 발행분기 +1,998 [F-KR0005,R1,K-KR0005]",
    ("KR0032", "2024-12-27", 4500.0): "사업보고서 '금리상향조정조건': 10년째 +1.00%p step-up -> 보완자본형; 발행사 표 항목 47 +4,330(액면 4,500) [F-KR0032,R1]",
    ("KR0068", "2024-07-17", 5000.0): "사업보고서: 스텝업 조항(10년째 +1.00%p) -> 보완자본형; 발행사 표 항목 47 2024.3Q +7,912 [F-KR0068,R1]",
    ("KR0068", "2024-09-24", 6000.0): "사업보고서: 스텝업 조항(+1.00%p); 2024.3Q 항목 47 +7,912(2024-07 건과 한 블록) [F-KR0068,R1]",
    ("KR0068", "2025-03-26", 6000.0): "사업보고서: 스텝업 조항(+1.00%p); 2025.1Q 항목 47 +5,087(액면 6,000) [F-KR0068,R1]",
    ("KR0068", "2025-06-24", 13819.0): "사업보고서: 외화 신종 스텝업 조항(+1.00%p, 美 국채 기준); 2025.2Q 항목 47 +17,876 [F-KR0068,R1]",
    ("KR0072", "2023-05-19", 2160.0): "반기·사업보고서 'Step-Up 포함여부': 10년 경과 후 +1.00%p -> 보완자본형 [F-KR0072,R1]; 같은 분기 구 신종 상환으로 표 단독 판독 불가",
    ("KR0072", "2024-12-26", 250.0): "사업보고서: Step-Up 조항(+1.00%p) -> 보완자본형 [F-KR0072,R1]; 소액이라 표 판독 불가",
    ("KR0073", "2023-05-12", 5000.0): "사업보고서: Step-up 조항(10년 경과 후 +1%) -> 보완자본형; 발행사 표 항목 47 2023.2Q +4,985 = 액면 [F-KR0073,R1]",
    ("KR0073", "2024-11-12", 6000.0): "사업보고서 L46354: Step-up(2034-11-12 +1%) -> 보완자본형(R1). 단 발행사 K-ICS 표는 보완자본에 가산하지 않은 흔적(항목 47 +202, X +89) = 상충 - 등재부는 티켓 시점 tier1, 지금은 type=tier2 + issuer_type=tier1 [F-KR0073]",
    ("KR0083", "2023-02-28", 600.0): "주석: 5년 후 조기상환 + 10년 경과 후 1회 이자율 조정(한화생명·흥국화재의 스텝업 +1.00%p 문구와 같음, 가산폭 미기재) -> 보완자본형 [F-KR0083,R1]",
    ("KR0104", "2023-01-31", 2500.0): "사업보고서: 10년째 최초 가산금리 +1.00% step-up -> 보완자본형 [F-KR0104,R1]; 발행 직후 분기 전기 열이 없어 표 판독 불가",
    ("KR1000", "2023-03-16", 2500.0): "주석 28: 5년 시점 재산정, 10년 시점 Step up 100bps -> 보완자본형 [F-KR1000,R1]",
    ("KR1000", "2024-10-11", 2300.0): "주석 28: 10년 시점 Step up 100bps -> 보완자본형 [F-KR1000,R1]; 구 신종 상환과 같은 분기라 표 판독 혼재",
}
CLASS_LABEL = {"tier1": "기본자본형(tier1)", "tier2": "보완자본형(tier2)", "legacy_tfi": "경과조치 기본자본(legacy_tfi, 시행 전 발행)"}

# ------------------------------------------------------------------------------------------------------------------------------ build rows
rows = []
for b in base:
    r = copy.deepcopy(b)
    r["r1_census_type"], r["r1_grade"], r["r1_mismatch"], r["r1_kind"] = b["census_type"], b["grade"], b["mismatch"], b["kind"]
    sc, why = scope_of(b)
    r["scope"], r["scope_label"], r["exclusion_reason"] = sc, SCOPE_LABEL[sc], why
    r["r2_change"], r["r2_note"], r["issue_date_press"], r["final_oneline"] = "", "", "", ""
    r["r1_name"] = b["name"]
    key = (b["code"], b["issue_date"] or "", b["face_eok"])
    if key in NAME_R2:
        r["name"] = NAME_R2[key]
    if b["kind"] == "registry-only hybrid" and key == PROMOTE["key"]:
        for f in ("name", "issue_date", "call_date", "legal_maturity", "coupon_pct", "face_eok", "outstanding_eok", "as_of", "status", "census_type", "grade", "b_strength", "a_basis", "step_up"):
            r[f] = PROMOTE[f]
        r["kind"], r["scope"], r["scope_label"], r["exclusion_reason"] = "bond", "in_scope", SCOPE_LABEL["in_scope"], ""
        r["ev"] = ";".join([x for x in (b["ev"] or "").split(";") if x] + PROMOTE["ev_add"])
        r["basis"] = (b["basis"] or "") + " | " + PROMOTE["change"]
        r["r2_change"], r["final_oneline"] = PROMOTE["change"], PROMOTE["oneline"]
        r["note"] = (b.get("note") or "") + "(R2: 1차 'registry-only' 행을 보도 확인 신종으로 승격)"
    elif sc == "in_scope" and b["tier"] == "hybrid" and key in HYB:
        d = HYB[key]
        for f in ("census_type", "grade", "b_strength", "a_basis", "step_up", "issuer_treatment"):
            if f in d:
                r[f] = d[f]
        r["ev"] = ";".join([x for x in (b["ev"] or "").split(";") if x] + [e for e in d["ev_add"] if e not in (b["ev"] or "").split(";")])
        if d["change"]:
            r["basis"] = (b["basis"] or "") + " | " + d["change"]
            r["r2_change"] = d["change"]
        r["final_oneline"] = d["oneline"]
    elif sc == "in_scope" and b["tier"] == "hybrid":
        if b["census_type"] == "legacy_tfi":
            note = b["basis"].split("대상. ", 1)[-1] if "대상. " in b["basis"] else ""
            ids = [x for x in b["ev"].split(";") if x and x != "R2"]
            r["final_oneline"] = LEG_PREFIX + note.replace(" [상환 완료/미잔존]", "") + f" [{','.join(ids)}]"
        else:
            r["final_oneline"] = HYB_KEEP_ONELINE[key]
    elif sc == "in_scope" and b["tier"] == "subordinated":
        skey = (b["code"], b["issue_date"] or "")
        if skey in SUB_DEFAULT:
            d = SUB_DEFAULT[skey]
            r["census_type"], r["grade"], r["a_basis"], r["step_up"] = "tier2", "a", "owner_default_rule(후순위=보완자본) - 반대 근거 없음", "n/a"
            r["basis"] = d["basis"]
            old_ev = [x for x in (b["ev"] or "").split(";") if x]
            r["ev"] = ";".join(old_ev + [e for e in d["ev_add"] if e != "W-none" and e not in old_ev])
            r["r2_change"] = "R2: ⓒ(예외 후보)→ⓐ(owner 기본값 tier2). 예외 후보 표시 제거. " + d["basis"]
            r["issue_date_press"] = ISSUE_DATE_PRESS.get(skey, "")
            r["final_oneline"] = d["oneline"]
        r["tier_family"] = "tier2"
    r["tier_family"] = "tier2" if str(r["census_type"]).startswith("tier2") else r["census_type"]
    rows.append(r)

# registry comparison (in-scope hybrids only).
# NOTE the registry moved while this round was running: publishing commit ef62969 (ticket 20261012T2030Z, owner-confirmed classification, 2026-10-12 19:46)
# rewrote it.  r["registry_type"] (round 1 snapshot) is the registry AT TICKET TIME -> 'mismatch' = the list the ticket asked for;
# registry_type_now / registry_issuer_type_now / vs_registry_now re-read the registry file as it is when this script runs.
def reg_lookup_now(code, d):
    for s in reg["companies"].get(code, {}).get("securities", []):
        sd = s.get("issue_date")
        if not sd:
            continue
        if sd == d:
            return s
        if re.fullmatch(r"\d{4}\.\dQ", sd) and d[:4] == sd[:4] and (int(d[5:7]) - 1) // 3 + 1 == int(sd[5]):
            return s
        if "~" in sd and sd.split("~")[0] <= d <= sd.split("~")[1]:
            return s
        if sd.endswith(" 외") and sd[:-2].strip() == d:
            return s
    return None


for r in rows:
    r["registry_type_now"], r["registry_issuer_type_now"], r["vs_registry_now"] = "", "", ""
    if r["scope"] == "in_scope" and r["tier"] == "hybrid":
        s = reg_lookup_now(r["code"], r["issue_date"])
        r["registry_type_now"] = s["type"] if s else ""
        r["registry_issuer_type_now"] = (s.get("issuer_type") or "") if s else ""
        r["vs_registry_now"] = "registry-absent" if not s else ("same" if s["type"] == r["census_type"] else "DIFFERENT")
for r in rows:
    if r["scope"] != "in_scope":
        r["mismatch"], r["mismatch_note"] = "", ""
        continue
    if r["tier"] == "subordinated":
        r["mismatch"], r["mismatch_note"] = "", "등재부 대상 아님(후순위)"
        continue
    ct, rt = r["census_type"], r["registry_type"]
    if rt is None:
        r["mismatch"], r["mismatch_note"] = "registry-absent", "등재부에 없음"
    elif ct == rt:
        r["mismatch"], r["mismatch_note"] = "same", ""
    else:
        r["mismatch"] = "DIFFERENT"
        r["mismatch_note"] = f"등재부 {rt}{'(미확정, 보수적 상한)' if r['registry_unconfirmed'] else ''} vs 최종 {ct} (확정도 {r['grade']})"

# ------------------------------------------------------------------------------------------------------------------------------ output helpers
def wcsv(path, cols, data):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)


def fnum(x):
    return "-" if x is None else f"{x:g}"


def cnt(rs, key="grade"):
    c = Counter(r[key] for r in rs)
    return f"ⓐ {c.get('a', 0)} / ⓑ {c.get('b', 0)} / ⓒ {c.get('c', 0)}"


rows.sort(key=lambda x: (x["code"], 0 if x["tier"] != "subordinated" else 1, x["issue_date"] or "9999", x["name"]))
INS = [r for r in rows if r["scope"] == "in_scope"]
HYBS = [r for r in INS if r["tier"] == "hybrid"]
SUBS = [r for r in INS if r["tier"] == "subordinated"]
EXC = [r for r in rows if r["scope"] == "excluded_owner"]
OTH = [r for r in rows if r["scope"] == "item6_other"]
assert len(INS) + len(EXC) + len(OTH) == len(rows) == 149

cols_full = ["code", "company", "scope", "scope_label", "exclusion_reason", "kind", "r1_kind", "tier", "name", "r1_name", "issue_date", "issue_date_press", "call_date", "legal_maturity", "coupon_pct", "face_eok", "outstanding_eok", "as_of", "status",
             "registry_type", "registry_unconfirmed", "census_type", "tier_family", "grade", "b_strength", "a_basis", "step_up", "issuer_treatment", "mismatch", "mismatch_note",
             "registry_type_now", "registry_issuer_type_now", "vs_registry_now",
             "r1_census_type", "r1_grade", "r1_mismatch", "r2_change", "basis", "ev", "note", "final_oneline", "registry_entry", "registry_evidence", "ledger_tier1_eok", "ledger_tier2_eok"]
wcsv(HERE / "census_securities_r2.csv", cols_full, rows)
(HERE / "census_securities_r2.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

# final: one line per in-scope hybrid bond
final_rows = []
for r in sorted(HYBS, key=lambda x: (x["code"], x["issue_date"])):
    final_rows.append(dict(code=r["code"], company=r["company"], name=r["name"], issue_date=r["issue_date"], face_eok=r["face_eok"], outstanding_eok=r["outstanding_eok"],
                           type=r["census_type"], classification=CLASS_LABEL[r["census_type"]], grade=r["grade"], a_basis=r["a_basis"], registry_type=r["registry_type"] or "",
                           vs_registry=r["mismatch"], registry_type_now=r["registry_type_now"], registry_issuer_type_now=r["registry_issuer_type_now"], vs_registry_now=r["vs_registry_now"],
                           evidence=r["final_oneline"]))
wcsv(HERE / "census_securities_final.csv", ["code", "company", "name", "issue_date", "face_eok", "outstanding_eok", "type", "classification", "grade", "a_basis",
                                            "registry_type", "vs_registry", "registry_type_now", "registry_issuer_type_now", "vs_registry_now", "evidence"], final_rows)

# item 6 sheet
cols6 = ["code", "company", "kind", "name", "issue_date", "face_eok", "registry_type", "registry_entry", "r1_census_type", "r1_grade", "step_up", "basis", "ev", "exclusion_reason"]
wcsv(HERE / "census_item6_other_r2.csv", cols6, OTH)
# excluded
cols_x = ["code", "company", "kind", "tier", "name", "issue_date", "call_date", "face_eok", "outstanding_eok", "status", "exclusion_reason", "r1_census_type", "r1_grade", "basis"]
wcsv(HERE / "census_excluded_owner_r2.csv", cols_x, EXC)
# mismatch (corrected)
MM = [r for r in INS if r["mismatch"] == "DIFFERENT"]
cols_m = ["code", "company", "issue_date", "face_eok", "name", "registry_type", "registry_unconfirmed", "census_type", "grade", "r1_census_type", "r1_grade", "r1_mismatch", "mismatch_note",
          "registry_type_now", "registry_issuer_type_now", "vs_registry_now", "issuer_treatment", "final_oneline", "ev"]
wcsv(HERE / "census_mismatch_r2.csv", cols_m, MM)

# newly confirmed
NEWSRC = {  # key -> (source ids, search numbers)
    ("KR0011", "2025-09-25", 1200.0): (["W12", "W18"], "#28, #29"),
    ("KR0011", "2026-02-11", 4420.0): (["O1", "W13"], "#31 (terms only), owner decision"),
    ("KR0011", "2026-06-09", 4100.0): (["W14", "W15", "W16", "O1"], "#6, #20"),
    ("KR0011", "2026-06-29", 300.0): (["W17", "O1"], "#30 (decision only), owner decision"),
    ("KR0050", "2024-05-14", 1000.0): (["O2"], "#2, #9, #11-#16 (exact sentence not found; owner excerpt)"),
    ("KR0050", "2026-06-29", 1000.0): (["W19", "W20", "W21", "W22", "W23", "O2"], "#11, #13, #14, #15, #21"),
    ("KR0097", "2023-03-31", 1800.0): (["O3"], "#3 (= W11 wording re-found), #22, #23"),
}
newrows = []
for r in HYBS:
    key = (r["code"], r["issue_date"], r["face_eok"])
    if key in NEWSRC:
        ids, qs = NEWSRC[key]
        newrows.append(dict(code=r["code"], company=r["company"], kind="신종", issue_date=r["issue_date"], face_eok=r["face_eok"], r1_type=r["r1_census_type"], r1_grade=r["r1_grade"],
                            r2_type=r["census_type"], r2_grade=r["grade"], a_basis=r["a_basis"], source_ids=",".join(ids),
                            sources=" | ".join(f"{i}: {EV2[i]['src']} [{EV2[i]['date']}; {EV2[i]['date_basis']}]" + (f" || original: {EV2[i]['original']}" if EV2[i].get("original") else "") for i in ids if i in EV2),
                            search_numbers=qs, evidence=r["final_oneline"], change=r["r2_change"]))
for r in SUBS:
    if r["r1_grade"] == "c":
        sid = [e for e in r["ev"].split(";") if e in EV2]
        newrows.append(dict(code=r["code"], company=r["company"], kind="후순위(예외 후보였음)", issue_date=r["issue_date"] or "(발행일 없음)", face_eok=r["face_eok"], r1_type=r["r1_census_type"], r1_grade="c",
                            r2_type=r["census_type"], r2_grade=r["grade"], a_basis=r["a_basis"], source_ids=",".join(sid) or "(공개 자료 없음)",
                            sources=" | ".join(f"{i}: {EV2[i]['src']} [{EV2[i]['date']}; {EV2[i]['date_basis']}]" for i in sid),
                            search_numbers={"KR0049": "#27", "KR0072": "#26", "KR0076": "#25", "KR0005": "#24"}[r["code"]], evidence=r["final_oneline"], change=r["r2_change"]))
wcsv(HERE / "census_newly_confirmed_r2.csv", ["code", "company", "kind", "issue_date", "face_eok", "r1_type", "r1_grade", "r2_type", "r2_grade", "a_basis", "source_ids", "sources", "search_numbers", "evidence", "change"], newrows)

# evidence table
ev_rows = [dict(id=e["id"], round=1, kind=e["kind"], strength=e["strength"], date=e["date"], date_basis="", source=e["src"], statement=e["statement"]) for e in EV1]
ev_rows += [dict(id=e["id"], round=2, kind=e["kind"], strength=e["strength"], date=e["date"], date_basis=e["date_basis"], source=e["src"], statement=e["statement"] + (" || original: " + e["original"] if e.get("original") else "")) for e in EVIDENCE_R2]
wcsv(HERE / "census_evidence_r2.csv", ["id", "round", "kind", "strength", "date", "date_basis", "source", "statement"], ev_rows)

# ------------------------------------------------------------------------------------------------------------------------------ K-ICS item 6 completeness check (information only)
def item_at(code, item, q):
    out = None
    for x in kd:
        if x["원보험사코드"] == code and x["항목번호"] == item and x["공시분기"] == q:
            try:
                out = float(str(x.get("값")).replace(",", ""))
            except (TypeError, ValueError):
                pass
    return out


chk = ["K-ICS 항목 6(2026.2Q, 억원) 대 집계 대상 신종 잔액 + 항목 6 대사용 기타 - 완결성 점검(정보용, 게이트 아님)",
       "잔차 = 항목 6 - 신종 잔액 합 - 기타 액면 합; 신종은 액면(장부와 수억 차이), 한도 적용 전 계상액이라 우선주·전환우선주가 같이 들어 있음",
       ""]
by = defaultdict(list)
for r in rows:
    by[r["code"]].append(r)
big = []
for code in sorted(by):
    hs = [r for r in by[code] if r["scope"] == "in_scope" and r["tier"] == "hybrid"]
    os_ = [r for r in by[code] if r["scope"] == "item6_other"]
    i6, i53 = item_at(code, 6, "2026.2Q"), item_at(code, 53, "2026.2Q")
    if not hs and not os_ and not i6:
        continue
    hsum = sum((r["outstanding_eok"] if r["outstanding_eok"] is not None else (r["face_eok"] or 0)) for r in hs)
    osum = sum((r["face_eok"] or 0) for r in os_)
    resid = None if i6 is None else i6 - hsum
    note = ""
    if resid is not None:
        resid2 = resid - osum
        tol = max(25.0, 0.03 * max(i6, hsum))
        note = "" if abs(resid) <= tol else ("  (기타 포함 시 %+.0f)" % (resid2 * 1.0) if abs(resid2) <= tol else "  <== 설명 안 되는 잔차")
        if note.strip().startswith("<=="):
            big.append((code, resid2))
    chk.append(f"{code} {by[code][0]['company']}: 항목6={fnum(i6)} 항목53={fnum(i53)} | 집계 대상 신종 {len(hs)}건 잔액합={hsum:g} | 기타 {len(os_)}건 액면합={osum:g} | 항목6-신종={fnum(resid)}{note}")
chk.append("")
chk.append("참고: KR0004(예별) 전환우선주는 2025.3Q 계약이전으로, KR0011 의 DB생명 포함분은 2025.2Q 부터 항목 6 에서 이미 0 이라 2026.2Q 대조에서 '기타'로 더하지 않는다(위 DB손보 잔차 -38 은 장부-액면 차이).")
chk.append("설명 안 되는 잔차(허용 = max(25, 3%)): " + (", ".join(f"{c}({v:+.0f})" for c, v in big) if big else "없음"))
(HERE / "census_item6_check_r2.txt").write_text("\n".join(chk) + "\n", encoding="utf-8", newline="\n")

# ------------------------------------------------------------------------------------------------------------------------------ summary
def basis_group(a):
    if a.startswith("issuer_filing + K-ICS"):
        return "발행사 공시 + 발행사 표(항목 53)"
    if a == "issuer_filing":
        return "발행사 공시(스텝업 문구)"
    if a.startswith("issuer_filing(indirect)"):
        return "발행사 공시(간접: 10년 후 이자율 조정 문구)"
    if "owner" in a:
        return "owner 지시/발췌 + 보도"
    if "rating" in a or a.startswith("press"):
        return "신평 보도"
    return a


def short(r):
    km = {"non-bond (전환우선주)": "전환우선주", "non-bond (우선주)": "우선주", "subsidiary instrument": "그룹사(DB생명) 포함분"}
    if r["scope"] == "item6_other":
        return f"{r['company']} {km[r['kind']]} {fnum(r['face_eok'])}억"
    if r["kind"] == "historical (redeemed)":
        return f"{r['company']} 신종 {fnum(r['face_eok'])}억(이력)"
    return f"{r['company']} {'신종' if r['tier'] == 'hybrid' else '후순위'} {r['issue_date']} {fnum(r['face_eok'])}억"


dif_r1 = [r for r in rows if r["r1_mismatch"] == "DIFFERENT"]
ty = Counter(r["census_type"] for r in HYBS)
ty_post = Counter(r["census_type"] for r in HYBS if (r["issue_date"] or "9999") >= "2023-01-01")
a_h = Counter(basis_group(r["a_basis"]) for r in HYBS if r["grade"] == "a")
exc_hist = [r for r in EXC if r["kind"] == "historical (redeemed)"]
exc_zero = [r for r in EXC if r["kind"] == "bond" and r["outstanding_eok"] == 0]
exc_h1 = [r for r in EXC if r["kind"] == "bond" and r["outstanding_eok"] != 0]
L = []
L.append("신종자본증권·후순위채 분류 전수조사 2차 (parser-kics, 티켓 20261012T2000Z, 2026-10-12)")
L.append("1차 산출(census_securities.* · census_mismatch.csv · census_summary.txt · census_evidence.csv)은 그대로 보존했고, 이 파일과 *_r2.* · census_securities_final.csv 가 새 버전이다.")
L.append("")
L.append("[범위 정리 - owner 지시 1~3]")
L.append(f"전체 {len(rows)}행 = 집계 대상 {len(INS)}건(신종 {len(HYBS)} + 후순위 {len(SUBS)}) + 제외(owner) {len(EXC)}건 + 항목 6 대사용 기타(우선주 등) {len(OTH)}건")
L.append(f"  - 제외(owner) {len(EXC)}건 = 이력 {len(exc_hist)}(" + " · ".join(short(r) for r in exc_hist) + f") + 잔액 0 {len(exc_zero)}(" + " · ".join(short(r) for r in exc_zero) +
         f") + 2026-06-30 목록에서 빠진 후순위 {len(exc_h1)}(" + " · ".join(short(r) for r in exc_h1) + ")")
L.append("    (잔액 0 후순위 1건 = 메리츠 2020-02-14 건: FY2025 보고서에서 이미 0, 2025-02-14 콜 상환. 목록에서 빠진 5건은 콜 도래일이 2026 상반기이고 H1 빌더 data/bonds/capital_securities_fy2026h1.json 이 현대해상 · KB손보 · 미래에셋은 "
         "'반기 중 상환 1건 제거(H1 증거 부재 + BS 당반기말 재현 이중확인)', DB손보는 '상환 확인 후 제거'(보도 W6 · W15 일치)로 기록; 흥국화재는 BS 당반기말 319,060 이 제21 · 22회 + 신규 1,000억으로 재현되어 제20회 450억이 BS 에 없다. 회사별 근거는 census_excluded_owner_r2.csv 의 exclusion_reason)")
L.append(f"  - 항목 6 대사용 기타 {len(OTH)}건 = " + " · ".join(short(r) for r in OTH))
L.append("    owner 가 적은 7건 외에 아이엠라이프 전환우선주(1,517억; 1차 ⓐ legacy_tfi)도 같은 성격이라 함께 옮겼다. 이 8건은 신종/후순위 건수에 세지 않는다(1차 등급은 열 grade 에 그대로).")
L.append("  - 후순위 전부 tier2(보완자본) 기본값. 예외 후보 4건(악사 JPY · KDB생명 보증부 · 아이엠라이프 사모 · 흥국화재 2026-03)의 예외 표시를 없앴고 공개 검색에서 반대 근거는 나오지 않았다(악사 JPY 는 공개 자료 자체가 없음).")
L.append("  - 1차의 'registry-only' 행(하나손보 2026.2Q +999억)은 보도로 실제 신종(2026-06-29 발행, 1,000억, 6.20%)임이 확인돼 신종 표의 정식 행으로 올렸다.")
L.append("")
L.append(f"[확정도 재집계: 집계 대상 {len(INS)}건 기준]")
L.append(f"  신종 {len(HYBS)}건: {cnt(HYBS)}   (1차 신종 46건: ⓐ 40 / ⓑ 6 / ⓒ 0 -> 제외 4 · 승격 1 · ⓑ 6건 전부 ⓐ)")
L.append(f"  후순위 {len(SUBS)}건: {cnt(SUBS)}   (그중 owner 기본값 적용 4건 = 1차 ⓒ 4건)")
L.append(f"  합계 {len(INS)}건: {cnt(INS)}")
L.append(f"  참고(집계 제외): 제외(owner) {len(EXC)}건 1차 등급 {cnt(EXC, 'r1_grade')} / 항목 6 대사용 기타 {len(OTH)}건 1차 등급 {cnt(OTH, 'r1_grade')}")
L.append("  신종 분류 분포: " + ", ".join(f"{k} {v}" for k, v in sorted(ty.items())))
L.append("  - 시행일(2023-01-01) 후 발행 신종: " + ", ".join(f"{k} {v}" for k, v in sorted(ty_post.items())) + f" (합 {sum(ty_post.values())}건, 전부 ⓐ)")
L.append("  신종 ⓐ 의 근거 종류: " + "; ".join(f"{k or '-'} {v}" for k, v in a_h.most_common()))
L.append("")
n_new_h = sum(1 for n in newrows if n["kind"] == "신종")
n_new_s = sum(1 for n in newrows if n["kind"] != "신종")
unclassified = [r for r in INS if r["census_type"] not in ("legacy_tfi", "tier1", "tier2", "tier2_legacy(TFI (2))") or r["grade"] != "a"]
L.append(f"[아직 미분류인 신종/후순위 채권: {len(unclassified)}건]  집계 대상 {len(INS)}건 전부 분류됨(census_type 가 legacy_tfi / tier1 / tier2 / tier2_legacy 중 하나, 확정도 ⓐ). 점검 = r2_selfcheck.py")
L.append(f"  단 ⓐ 의 질은 균일하지 않다: 발행사 공시 직접 서술 · 규정 적용 외에 ⓐ 가 보도/owner 지시에 기댄 신종 {n_new_h}건 + owner 기본값 후순위 {n_new_s}건이 있다(아래 [새로 확정된 증권]).")
L.append("")
now_diff = [r for r in HYBS if r["vs_registry_now"] == "DIFFERENT"]
now_abs = [r for r in HYBS if r["vs_registry_now"] == "registry-absent"]
issuer_diff = [r for r in HYBS if r["registry_issuer_type_now"] and r["registry_issuer_type_now"] != r["census_type"]]
L.append("[등재부(capital_tier_registry.json) 대비 불일치: 정정본 - 이 작업은 등재부를 고치지 않았다]")
L.append(f"  (가) 티켓 시점 등재부 기준(1차 census 가 읽은 등재부): 1차 {len(dif_r1)}건 -> 정정 후 {len(MM)}건")
for r in MM:
    L.append(f"    - {r['company']} {r['issue_date']} {fnum(r['face_eok'])}억: {r['mismatch_note']}")
L.append("    정정 내용: DB손보 2026 세 건은 불일치가 아니라 일치(등재부 tier1 = 최종 tier1); 하나생명 1건이 새 불일치(등재부 tier1 vs 최종 tier2); 하나손보 두 건은 등재부(tier2)와 일치 + ⓐ 로 승급.")
L.append(f"  (나) 이 작업 도중 등재부가 바뀌었다: publishing 커밋 ef62969(티켓 20261012T2030Z, owner 확정 채팅 2026-10-12)가 위 {len(MM)}건의 type 을 최종본과 같게 고치고 미확정 표시를 지웠다. "
         f"실행 시점의 HEAD 등재부와 다시 대조하면 type 불일치 {len(now_diff)}건 · 등재부에 없는 증권 {len(now_abs)}건.")
L.append(f"    남은 차이 = 등재부가 `issuer_type` 으로 병기한 {len(issuer_diff)}건(우리 type 대 발행사 K-ICS 표 처리): " +
         " · ".join(f"{r['company']} {r['issue_date']} {fnum(r['face_eok'])}억(type {r['census_type']} / issuer_type {r['registry_issuer_type_now']})" for r in issuer_diff) + " - 아래 두 한 줄 메모와 같은 내용이다.")
L.append("  하나생명 상충 메모(한 줄): 발행사 K-ICS 표는 부분 기본자본형 모양(항목 47 이 14분기 내내 액면 1,799 미만)이고 DART 주석에 스텝업 문구가 없으나, owner 지시로 보도의 명시적 스텝업 서술(아시아경제 2023-04-05 = W11)을 따랐다.")
L.append("  교보생명 2024-11-12 6,000억은 R2 증거로 바뀌는 것이 없어 1차 상충(스텝업 = 보완자본형인데 발행사 표는 기본자본형으로 처리)이 그대로다.")
L.append("")
L.append("[새로 확정된 증권] (census_newly_confirmed_r2.csv - 출처 id · URL · 날짜 · 검색 번호 포함)")
for n in newrows:
    L.append(f"  - {n['company']} {n['issue_date']} {fnum(n['face_eok'])}억 ({n['kind']}): {n['r1_type']}/ⓑ·ⓒ -> {n['r2_type']}/ⓐ  근거 {n['source_ids']}  [{n['a_basis']}]")
L.append("  - 못 오른 건: 없음(1차 ⓑ 신종 6건 전부 ⓐ). 단 DB손보 제3회(2026-02-11 4,420억)는 이 건 하나를 직접 서술한 기사를 못 찾았고 owner 지시 + 같은 프로그램 조건에 기댄 ⓐ 다. "
         "반대 방향 신호가 셋 있다: 발행사 표 검정(c9, 2026.1Q 블록 moderate) · W5(IB토마토 2026-06-01, 이 건을 '보완자본 인정'으로 분류) · W14(2026-06 건을 2025 이후 '두 번째' 기본자본 신종으로 셈). "
         "셋 다 기본자본형 총량이 10% 한도를 넘어 초과분이 보완자본으로 재분류된 효과와 구분되지 않는다(추정). DB손보 제5회(300억)도 같은 이유로 표에서 분리되지 않는다.")
L.append("")
L.append("[owner 발췌의 원문 출처]")
L.append("  - DB손보 발췌(O1): 원문 후보 = IB토마토 2026-07-09 '상환하면 자본 깎이고 안 하면 신용도 훼손...보험사 영구채 딜레마' https://www.newstomato.com/ReadNews.aspx?no=1306331 (= 1차의 W2, 같은 글 https://www.ibtomato.com/ExternalView.aspx?type=1&no=18833).")
L.append("    내용은 일치한다(K-ICS 도입 이후 스텝업 없는 신종을 발행한 보험사는 DB손보뿐 · 발행에 배당가능이익 필요 · 2026-06 두 번째 기본자본 신종이 공모희망 4.7~5.3% 최상단 5.3%로 확정). 단 검색 요약은 기사 리드와 일부 본문만 반영해 문장 그대로의 일치는 확인하지 못했다 -> 검색 #33. 앞선 9회 시도(#1, #4~#8, #17~#19)는 문장을 못 찾았다.")
L.append("    같은 내용을 말하는 다른 공개 기사: 헤럴드경제 2025-08-19(W3) · 디지털타임스 2025-09-25(W12) · IB토마토 '기본자본 또 발행'(W14) · FETV(W15) · 한국신용평가 2026-05-26 보고서(W18). 그 기사들은 '유일' 대신 '업계 최초'(2025) · '두 번째'(2026-06)로 서술한다.")
L.append("  - 하나손보 발췌(O2): 6.20% · 1,000억 · 만기 2056-06 · 하나금융 전량 인수 · 보완자본 분류는 파이낸셜투데이(W19) · 시사저널e 2026-09-15(W21) · 메트로신문 2026-09-30(W20) · 딜사이트(W22) · FETV(W23)로 확인. "
         "'스텝업은 없으나 배당가능이익이 없어 기본자본 요건 미충족'과 '신종 2,000억 전액 보완자본' 문장은 못 찾음 -> owner 제공 발췌.")
L.append("  - 하나생명 발췌(O3): 아시아경제 2023-04-05 https://core.asiae.co.kr/article/2023040506543817834 (= 1차의 W11) 와 같은 서술을 검색 #3 에서 다시 확인.")
L.append("")
L.append("[2026-06-30 이후 발행(집계 밖, 참고)]")
L.append("  - 하나생명 2026-09-15 사모 신종 1,500억(연 6%, 만기 2056-09-15, 5년 콜): 보도상 보완자본(W24·W25). K-ICS 자료 창(2026.2Q) 밖이라 표에 넣지 않음.")
L.append("  - 교보생명 2026-09 예정 신종(수요예측 2026-08-24 주문 4,460억, 목표 3,000억~최대 5,000억): 스텝업 조건이라 전액 보완자본으로 보도(W10); 최종 발행액·금리 미확인.")
L.append("")
L.append("[한계]")
L.append("  - WebSearch 는 검색 결과 목록(제목 · URL)과 요약문을 돌려주며 기사 본문을 열지 않았다. 이 폴더의 모든 기사 서술은 요약에서 옮긴 패러프레이즈이고, 일자는 date_basis 열에 확실도를 적었다. 외부에 쓰기 전에는 URL 에서 원문을 다시 읽을 것.")
L.append("  - 증권신고서 · 투자설명서 · 사모 계약서 원문은 못 열었다(go.kr 계열 금지 + WebSearch 만). W16(KIND 증권신고서 2026-05-27)과 W18(한신평 보고서)은 요약에 기댄 것이다.")
L.append("  - '기본자본 인정'은 스텝업 없음만으로 정해지지 않는다(배당가능이익 범위의 이자 지급이 함께 필요 - 하나손보가 그 사례). DB손보 tier1 은 스텝업 없음이 아니라 신평사 · 증권신고서 · 보도의 기본자본 신종 서술(제1·2·4회)과 owner 지시(제3·5회)에 기댄다.")
L.append("")
L.append("[재현 순서] (저장소 루트에서, python = C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe)")
L.append("  1차 산출(c1~c10)이 이미 있으면 -> r2_apply.py -> r2_selfcheck.py   (r2_evidence.py = 2차 근거 데이터. 저장소 파일은 읽기만 하고 이 폴더에만 쓴다.)")
L.append("")
L.append("[회사별 한 줄 - 집계 대상 기준]")
for code in sorted(by):
    rs = [r for r in by[code] if r["scope"] == "in_scope"]
    if not rs:
        continue
    hb = [r for r in rs if r["tier"] == "hybrid"]
    sb = [r for r in rs if r["tier"] == "subordinated"]
    parts = []
    if hb:
        c = Counter(r["census_type"] for r in hb)
        parts.append("신종 " + "·".join(f"{k} {v}" for k, v in sorted(c.items())) + f" [{cnt(hb)}]")
    if sb:
        parts.append(f"후순위 {len(sb)}건 보완자본 [{cnt(sb)}]")
    flag = "  <== 등재부와 다름" if any(r["mismatch"] == "DIFFERENT" for r in rs) else ""
    L.append(f"  {code} {by[code][0]['company']}: " + " | ".join(parts) + flag)
(HERE / "census_summary_r2.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")

# search log
SL = ["r2_search_log.txt - every WebSearch call of the round-2 run (ticket 20261012T2000Z, 2026-10-12). mode s = standard, x = extended.",
      "WebSearch only; no WebFetch / browser; nothing on go.kr / law.go.kr / KIPRIS was opened.  Results are model-written summaries of the hits (titles + URLs seen).",
      "Result codes: HIT = found what the query aimed at; PART = related items only; MISS = nothing usable.", ""]
for n, m, q, res in SEARCH_LOG:
    SL.append(f"#{n:02d} [{m}] {q}")
    SL.append(f"      -> {res}")
(HERE / "r2_search_log.txt").write_text("\n".join(SL) + "\n", encoding="utf-8", newline="\n")

# input fingerprints, so r2_selfcheck.py can tell whether the repo files that were read have changed since this run
import hashlib  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


(HERE / "r2_inputs.json").write_text(json.dumps({
    "note": "sha256 of the files r2_apply.py read (read only); written at the time of the run",
    "census_securities.json (round 1)": sha(HERE / "census_securities.json"),
    "kics_disclosure.json": sha(REPO / "kics_disclosure.json"),
    "data/bonds/capital_tier_registry.json": sha(REPO / "data/bonds/capital_tier_registry.json"),
    "data/bonds/capital_securities_fy2026h1.json (cited in the exclusion reason)": sha(REPO / "data/bonds/capital_securities_fy2026h1.json"),
}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

print("\n".join(L))
print()
print("wrote:", ", ".join(sorted(p.name for p in HERE.glob("*r2*") if p.is_file())), "+ census_securities_final.csv")
