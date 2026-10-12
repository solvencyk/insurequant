"""Bundle all root master tables into one reviewable .xlsx (one sheet per master).

Output: insurequant_master_tables.xlsx (repo root).
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "insurequant_master_tables.xlsx"
FONT = "맑은 고딕"

# (json file, sheet name, description) — only real masters (diff snapshots excluded)
MASTERS = [
    ("IFRS17_BS.json", "17BS",
     "재무상태표 요약 (자산총계·부채총계·자본총계·AOCI누계액·법정준비금 3종 = 항목 1-7) long-format"),
    ("kics_disclosure.json", "K-ICS공시",
     "K-ICS 지급여력 공시 항목 (요구자본 1-35 + 시장위험 하위분해 36-46) long-format"),
    ("kics_rate_sensitivity.json", "금리민감도",
     "지급여력 금리민감도 (경과조치 적용전/후 x measure x base/±50/±100bp) — **K-ICS 쪽**. "
     "`듀레이션`·`컨벡서티`는 ±100bp 평행이동에서 유도한 유효듀레이션(년)/유효컨벡서티 "
     "(owner 2026-08-30). 양수 듀레이션 = 금리 상승 시 가치 감소. 지급여력비율 행은 두 금액의 "
     "나눗셈이라 그 미분에 듀레이션/컨벡서티라는 이름을 붙이지 않고 비워 둔다"),
    # 2026-08-30 신설. owner 상시 규칙("화면 그래프는 전부 마스터에 담는다")에 대해
    # IFRS17.html "7) 민감도(ΔCSM)" 패널만 대응 시트가 없었다. 바로 위 `금리민감도` 와
    # 이름이 비슷해 같은 것으로 오인돼 왔는데 **다른 표다** — 저쪽은 K-ICS 지급여력비율의
    # 금리 ±bp 민감도, 이쪽은 IFRS17 보험가정(사망률·장해질병·해지율·사업비) 충격의 ΔCSM.
    ("CSM_sensitivity.json", "가정민감도",
     "IFRS17 보험가정 민감도 (사망률·장해질병·해지율·사업비 충격 -> CSM변동·손익영향, 억원)"),
    ("CSM_waterfall.json", "CSM워터폴",
     "CSM 변동분석 (기초→신계약→이자부리→가정·경험조정→상각→기말)"),
    ("CSM_amortization.json", "CSM상각",
     "CSM 경과연차별 상각 스케줄"),
    ("NB_CSM_multiple.json", "신계약CSM배수",
     "신계약 CSM / 월납초회보험료 배수 (연누계)"),
    ("PL_breakdown.json", "손익분해PL",
     "손익계산서 24항목 분해 (보험·투자손익 등)"),
    ("dividend.json", "배당",
     "배당에 관한 사항 (DART alotMatter) — 항목1-7 회사단위 + 8-11 종류주(보통주/우선주)별"),
    ("kics_tier1_utilization.json", "기본자본소진율",
     "기본자본 자본증권 인정한도 소진율 — max(기발행 신종 ÷ SCR×15%, 기본자본형 신규 ÷ SCR×10%), "
     "보완자본형 신종 제외 (경영공시 기준, 2026-10-12 규정 근거 재정의) long-format. 비고열=근거·한계"),
    ("kics_tier2_utilization.json", "보완자본소진율",
     "보완자본 인정한도 소진율 — 보완자본 한도 적용 전(경과조치 적용 후) ÷ SCR×50% "
     "(경영공시 기준, 2026-10-12 규정 근거 재정의; 2026-06-20 폐기된 구산식은 참고용 별도 항목명 행) "
     "long-format. 비고열=근거·한계"),
    ("kics_capital_securities.json", "자본성증권발행현황",
     "자본성증권 한 건 단위 인정액 — 회사·구분·발행일·콜만기도래일·법정만기일·액면가·"
     "공시분기별 기본자본인정액/보완자본인정액. 종전에는 회사 단위 집계값만 있어 어느 증권이 "
     "얼마를 인정받는지 되짚을 수 없었다(owner 2026-09-01 설계). 신종은 SCR×15% 한도를 "
     "경과조치분·신규분이 공유하며 발행일 순으로 채우고 초과분은 보완자본으로 분류, "
     "후순위는 잔존만기 5년 미만부터 매년 20%p 계단식 차감. **체감 잔존만기는 법정만기일에서 "
     "센다 — 콜만기도래일이 아니다**(owner 2026-09-23): 콜은 발행사의 권리일 뿐 만기가 아니라, "
     "콜을 만기로 보면 10년만기·5년콜 구조에서 갓 발행한 채권이 바로 80%로 깎인다"),
    ("kics_forward_capital.json", "자본비율전망",
     "자본비율 5년 전망(2026~2030 연도말) — 콜옵션 도래 채무성자본 차감 + SCR 선형보간 시뮬레이션 "
     "(baseline 2026.1Q, status!=ok 회사 제외) long-format, 공시분기 칸에 전망연도. 비고열=known limitation"),
    # 2026-09-22 신설 (owner 지시). 경영공시 '금리위험액 현황' 표의 자산총계·부채총계를
    # 시나리오별로 담고 그로부터 자산·부채 듀레이션과 갭을 낸다. 분모는 이 표의 자산총계이지
    # 건전성감독기준 재무상태표의 전체 자산이 아니다 — 분자(순자산가치 변동)가 금리위험
    # 측정 대상에서만 나오므로 범위를 맞춰야 갭 = 자산D - (L/A)x부채D 가 닫힌다.
    # 순자산가치(시나리오별)는 `K-ICS공시` 시트 항목 41~46 에 이미 있어 여기 중복해 담지 않는다.
    ("kics_duration_gap.json", "금리듀레이션갭",
     "K-ICS 금리위험 듀레이션 갭 (짝수분기만 공시) — '금리위험액 현황' 표의 자산총계·부채총계 "
     "6시나리오(충격전·평균회귀·금리상승·금리하락·금리평탄·금리경사, 억원) + 파생 듀레이션. "
     "자산D=(자산_하락-자산_상승)/(2%×자산_충격전), 부채D=(부채_하락-부채_상승)/(2%×부채_충격전), "
     "갭=자산D-(부채자산비율×부채D). 부채D 는 부채로 나눠 끝내고 L/A 는 갭에서만 곱한다 "
     "(owner 2026-09-22). 부채_충격전이 0 이하인 회사는 부채D 를 비우고 갭만 채운다. "
     "양수 갭 = 금리 상승 시 순자산 감소. K-ICS 충격은 평행이동이 아니라 기간구조 충격이라 "
     "2%로 나누는 것은 근사 — 순위·상대크기는 유효하나 절대 연수는 참고치(owner 2026-09-22). "
     "비고열 = 산출 불가 사유·발행사 표 불일치"),
    # 2026-10-08 신설 (owner 가 시트를 손으로 추가하고 출처·추출방식·플래그 열을 지움).
    # 원천 마스터 JSON 은 그 열들을 그대로 갖고 있고, 시트에서만 FLATTEN 이 뺀다.
    ("data/persistency/master_persistency.json", "유지율",
     "판매채널별 유지율 (정기경영공시 7-6 표, 2Q·4Q 반기) — 회차(13·25·37·61) x 채널 대/소분류, "
     "유지율 = 유지계약액 ÷ 대상신계약액 x 100"),
    ("data/loss_ratio/master_loss_ratio.json", "손해율",
     "위험보험료 대비 예상보험금 (결산 공시, 미래 손해율 가정) — 경과차년 x 구분·상품구분·포트폴리오, "
     "손해율 = 예상보험금 ÷ 위험보험료 x 100. 공시분기 Y.4Q = Y.4Q PDF 의 <Y> 블록(다음 해 PDF 가 "
     "다르게 다시 찍으면 그 값)"),
    # 2026-10-11 신설 (owner 승인: 「발생사고요소(LIC)도 마스터 테이블 만들어야지」). IFRS17.html 섹션 3 콤보의
    # 원천인데 시트가 없어 tests/test_push_gate_wiring.py 에 MASTER_SHEET_PENDING 으로 선언돼 있던 것.
    # 잔여보장요소(LRC)와 발생사고요소(LIC)를 한 시트에 담는다 — 구분은 항목번호·섹션·레벨 열.
    ("insurance_liability_portfolio.json", "보험계약부채",
     "보험계약부채 구성 = 잔여보장요소(LRC) + 발생사고요소(LIC, 지급준비금 포함). 항목 1~8 = 경영공시 "
     "회계모형별(일반모형·변동수수료접근법·보험료배분접근법) 잔여보장요소 구성(최선추정·위험조정·보험계약마진)과 합계, "
     "9 = 무·저해지상품 해지율 예외모형 사용 여부(1=사용), 10~15 = DART 주석 기준 발생사고요소(합계·최선추정·위험조정·미분리)·"
     "잔여보장요소 합계·보험계약부채 합계, 16·17 = 비PAA 발생사고요소의 최선추정·위험조정 계산값(직접 공시값 아님). "
     "값 단위 억원(항목 9 제외, 단위 열 참조). 기준표시 열 = 값을 읽은 공시·기준, 비고 열 = 소급재작성·순액·계산값 설명. "
     "원문에 표가 없어 적재하지 않은 (회사, 분기, 항목)은 행 자체가 없다"),
    # 2026-10-12 신설 (owner 승인: 「나머지는 다 승인」, TODO.md ㉓ — 스키마 변경). IFRS17.html 손해율 패널의
    # 예실차 블록(panel_loss_ratio.json `ae`)의 원천인데 시트가 없던 것. 열은 마스터 필드 그대로이고, 출처는 쪽 번호만 싣는다.
    ("data/loss_ratio/claims_ae_ratio.json", "보험금예실차비율",
     "보험금 예실차비율 (결산 공시 손해율 표 A) — 기준연도별 예상손해율·실제손해율(%)과 예실차비율"
     "(= 예상 - 실제, %p). 공시분기 Y.4Q 결산 공시가 두 개 기준연도(Y, Y-1)를 함께 싣는다. "
     "사업구분 열은 코리안리처럼 사업별로 따로 공시한 경우만 채운다. 해당 없음(빗금)으로 공시된 칸은 비어 있고 "
     "플래그 열에 적는다. 출처쪽 = 결산 공시 PDF 의 쪽 번호"),
]

NUMERIC_COLS = {"값", "-100bp", "-50bp", "base", "+50bp", "+100bp",
                "액면가_억", "잔액_억", "기본자본인정액_억", "보완자본인정액_억",
                "기본자본한도_억", "SCR_억", "보완자본인정율",
                "상각액", "신계약CSM_연누계", "월납월초보험료_연누계", "신계약CSM배수_연누계",
                "CSM변동", "당기손익영향", "자본영향",
                "듀레이션", "컨벡서티",
                # 2026-09-22 금리듀레이션갭 시트. 자산_/부채_ 6시나리오는 억원 금액,
                # 나머지 4개는 파생 지표(년 / 배수). NUMERIC_COLS 에 없으면 coerce 가
                # 문자열로 굳혀 sync 가 값 컬럼이 아닌 키 컬럼으로 오인한다.
                "자산_충격전", "자산_평균회귀", "자산_금리상승", "자산_금리하락",
                "자산_금리평탄", "자산_금리경사",
                "부채_충격전", "부채_평균회귀", "부채_금리상승", "부채_금리하락",
                "부채_금리평탄", "부채_금리경사",
                "자산듀레이션", "부채듀레이션", "듀레이션갭", "부채자산비율",
                # 2026-10-08 유지율·손해율 시트
                "대상신계약액", "유지계약액", "유지율", "위험보험료", "예상보험금", "손해율",
                # 2026-10-12 보험금예실차비율 시트
                "예상손해율", "실제손해율", "예실차비율", "출처쪽"}
# 2026-09-01: (증권명)을 넣는다. 자본성증권발행현황 시트는 **한 회사·한 분기에 여러 행**
# (증권 한 건 = 한 행)이라 코드+분기만으로는 행을 식별할 수 없다 —
#  가 TEXT_COLS 를 그대로 행 식별키로 쓰므로 빠지면 동기화가 깨진다.
TEXT_COLS = {"원보험사코드", "원수사명", "티커", "생손보여부", "공시분기", "구분", "종류",
             "항목명", "경과조치여부", "measure구분", "경과차년", "종류주", "섹션", "레벨",
             "기준일", "순번", "위험구분", "충격수준", "비고",
             # 2026-10-08 유지율·손해율 시트의 행 식별 열
             "회차구분", "채널대분류", "채널소분류", "상품구분", "포트폴리오",
             "세그먼트", "단위",
             # 2026-10-11 보험계약부채 시트(출처 공시·기준 표시)
             "기준표시",
             # 2026-10-12 보험금예실차비율 시트(기준연도는 행 식별키라 문자열로 둔다)
             "기준연도", "사업구분", "플래그"}


def coerce(df):
    for c in df.columns:
        if c in NUMERIC_COLS:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        elif c == "항목번호":
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        else:
            df[c] = df[c].astype("string")
    return df


# ---------------------------------------------------------------------------
# Flatteners — kics_tier1_utilization.json / kics_tier2_utilization.json /
# kics_forward_capital.json are NOT already long-format (unlike the 8 masters
# above, which are flat lists-of-dicts straight off disk). Each is a per-company
# snapshot (tier1/2) or per-company x per-year-projection nest (forward). These
# reshape them into the SAME (원보험사코드,원수사명,티커,생손보여부,공시분기,항목명,값)
# shape as everything else, so xlsx/sync/coerce all stay generic.
#
# inbox/parser/20260829T0100Z (orchestrator, owner-approved schema 2026-08-29):
#   tier1/tier2: 공시분기 = snapshot quarter ("2026.1Q"), 항목명 splits the metric.
#   forward:     공시분기 = projection year ("2026".."2030") — plain 4-digit strings,
#                never mixed with "YYYY.NQ" quarter labels in the same column (checked
#                against scripts/export_public_sheets.py:41-44's non-standard-label
#                sort concern; see this ticket's report for why it doesn't apply here).
# One added column, "비고" (free-text, blank for most rows): the ticket requires the
# known extraction limitations (tier1 numerator partly BS-fallback, forward call-date
# partly estimated, low-confidence rows, deprecated tier2 proxy metric) to travel WITH
# the numbers if someone copies just the numeric rows out — a header-only note would not
# survive that. Every other column name is reused verbatim from the existing 8 sheets.
# ---------------------------------------------------------------------------

def _kics_company_lookup() -> dict:
    """원보험사코드 -> (원수사명, 티커, 생손보여부), sourced from kics_disclosure.json.

    Every insurer in the tier1/tier2/forward-capital cohorts already has K-ICS
    disclosure rows (verified 2026-08-29: all 39 tier1/tier2 codes and all 38
    forward_capital codes are a subset of kics_disclosure.json's 원보험사코드 set) —
    this reuses that already-verified truth instead of standing up a new registry.
    """
    data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    lut: dict = {}
    for r in data:
        code = r.get("원보험사코드")
        if code and code not in lut:
            lut[code] = (r.get("원수사명"), r.get("티커"), r.get("생손보여부"))
    return lut


def _company_base(code, fallback_name, lut: dict) -> dict:
    name, ticker, biztype = lut.get(code, (None, None, None))
    return {"원보험사코드": code, "원수사명": name or fallback_name,
            "티커": ticker, "생손보여부": biztype}


def _call_fallback_codes() -> set:
    """원보험사코드 set with >=1 OUTSTANDING bond whose call_source != 'disclosed'
    (call option not found in the filing -- forward_capital_simulation.py L150 derives/
    estimates effective_call_date instead, e.g. issue+5y or rating-history heuristics).
    Computed live off data/bonds/capital_securities_fy2025.json, not hardcoded — census
    verified 2026-08-29: 20 of 39 companies (see this ticket's report for the full list).
    """
    path = REPO / "data" / "bonds" / "capital_securities_fy2025.json"
    if not path.exists():
        return set()
    doc = json.loads(path.read_text(encoding="utf-8"))
    out = set()
    for c in doc.get("companies", []):
        for b in c.get("bonds", []):
            if b.get("outstanding_mn") and b.get("call_source") != "disclosed":
                out.add(c.get("code"))
    return out


# 2026-10-12 규정 근거 재정의(scripts/capital_utilization_rules.py): 소진율은 두 한도 중 먼저 차는 쪽이다
# (기발행 신종 / SCR x 15%, 기본자본형 신규 / SCR x 10%). 배포 JSON 의 tier1_hybrid_limit_eok·
# tier1_hybrid_recognized_eok 는 화면·게이트 항등식용 **결속 쪽** 값이라 행마다 15% 또는 10% 가 된다 —
# 항목명 "(SCR x 15%)" 와 어긋나므로 이 시트는 항목명은 그대로 두고 **읽는 필드만** 바꿨다:
#   "기본자본 인정한도(SCR x 15%)" <- tier1_legacy_limit_eok (늘 SCR x 15%, 값 변화 없음)
#   "신종자본증권 인정액"           <- tier1_basic_new_eok   (기본자본형 신규 = 10% 한도 대상)
# 그러면 시트만으로 소진율 = max(경과조치 인정 신종자본증권 / 인정한도(15%), 인정액 / 인정한도(엄격 10%))
# 가 재현된다. 항목명 자체를 규정 표기로 바꾸는 것은 시트 스키마 변경이라 owner 승인 사항이다.
_TIER1_ITEMS = [
    ("scr_eok", "지급여력기준금액(SCR)"),
    ("tier1_legacy_limit_eok", "기본자본 인정한도(SCR x 15%)"),
    ("tier1_hybrid_limit_strict_eok", "기본자본 인정한도(엄격, SCR x 10%)"),
    ("tier1_hybrid_issued_eok", "신종자본증권 발행잔액"),
    ("tier1_basic_new_eok", "신종자본증권 인정액"),
    ("tier1_hybrid_overflow_eok", "신종자본증권 한도초과분"),
    ("legacy_hybrid_transition_eok", "경과조치 신종자본증권(구산정)"),
    ("tier1_grandfathered_hybrid_eok", "경과조치 인정 신종자본증권"),
    ("utilization_pct", "기본자본 소진율"),
    ("utilization_pct_strict", "기본자본 소진율(엄격)"),
]
# tier1_hybrid_excess_eok dropped: null for 39/39 rows (verified 2026-08-29) — an
# always-empty column carries no information as a row.
# utilization_pct_raw dropped: byte-identical to utilization_pct for 39/39 rows
# (verified 2026-08-29) — pure duplicate.

# 2026-09-01: 분자가 DART 채권 재구성에서 **경영공시 item6**(자본항목 중 보통주 이외의
# 자본증권)으로 바뀌었다. 한도는 증권 종류별이 아니라 계정 단위라([별표22] Ⅲ.2.다.(1)①)
# 채권을 모아 만든 분자는 구조적으로 과소했다 — 실측 6개사에서 item6 > 신종잔액.
_TIER1_ISSUED_NOTE = ("분자=경영공시 '자본항목 중 보통주 이외의 자본증권'(item6). 신종자본증권만이 "
                       "아니라 기본자본요건을 충족하는 자본증권 전체이며 보통주는 제외된다")
_TIER1_NOTE_FIELDS = {"tier1_hybrid_issued_eok", "tier1_hybrid_recognized_eok", "utilization_pct"}

# 2026-08-29 코디네이터 후속 요청: 100% 초과 13행(실측: primary>100 6개사 + strict>100
# 7개사, 6개사는 두 항목 다 초과라 중복) 비고가 비어 있어 "엑셀만 받아본 사람은 파싱오류로
# 읽는다"는 지적 + 소진율/소진율(엄격) 차이가 시트만 봐서 안 읽힌다는 지적. 근거는 owner
# 승인 정의서 docs/tier1_hybrid_utilization_definition.md("왜 캡이 없나", "소진율 필드
# 의미" 절, 2026-06-14/2026-08-25 owner 결정) — 추측 아니고 그 문서를 그대로 인용.
_TIER1_BASIS_NOTE = {
    "utilization_pct": (
        "2026-10-12 규정 근거 재정의: 소진율 = max(경과조치 인정 신종자본증권 ÷ 기본자본 인정한도"
        "(SCR×15%), 신종자본증권 인정액(기본자본형 신규) ÷ 기본자본 인정한도(엄격, SCR×10%)). "
        "2022년 이전 기발행 신종만 공통적용 경과조치로 15%([별표22] Ⅵ.1.가.(1), 2032년까지), 나머지는 "
        "원칙 10%([별표22] Ⅲ.2.다.(1)②). 발행사가 경영공시에서 보완자본으로 처리한 신종"
        "([별표22] Ⅲ.2.다.(2))은 기본자본 자본증권이 아니라 분자에서 뺀다."
    ),
    "utilization_pct_strict": (
        "SCR×10% 한도 쪽 소진율 = 신종자본증권 인정액(기본자본형 신규) ÷ 기본자본 인정한도(엄격, "
        "SCR×10%). '기본자본 소진율'은 이 값과 경과조치 쪽(SCR×15%) 중 큰 값이다."
    ),
    "tier1_basic_new_eok": (
        "기본자본형 신규 자본증권(신종·우선주 등) = 신종자본증권 발행잔액(보통주 이외 자본증권) - "
        "경과조치 인정 신종자본증권 - 보완자본형 신종. 원칙 한도 SCR×10% 대상(2026-10-12 재정의)."
    ),
    "tier1_hybrid_overflow_eok": (
        "두 한도 초과분 합(경과조치분의 SCR×15% 초과 + 기본자본형 신규의 SCR×10% 초과) — "
        "보완자본으로 재분류되는 금액."
    ),
}
_TIER1_OVER100_NOTE = (
    "100%초과는 파싱오류 아님 — 실제 한도 초과 상태다. 초과분은 [별표22] Ⅲ.2.다.(1)에 "
    "따라 보완자본으로 재분류되고, 보완자본 한도까지 넘으면 1.라.(6)으로 가용자본에서 "
    "차감된다. 소진율은 100%로 자르지 않는다(owner 2026-06-14 결정 — "
    "docs/tier1_hybrid_utilization_definition.md). 화면에는 '100%+'로 표기됨."
)


def _tier1_row_note(r: dict) -> str:
    """'기본자본 소진율' 행에만 붙는 회사별 근거 — 어느 한도가 결속하는지, 형 판정이 미확정인지."""
    leg = r.get("binding_leg")
    out = []
    if leg == "legacy_15":
        out.append(f"결속 한도: 경과조치 쪽(SCR×15%) {r.get('tier1_legacy_pct')}%")
    elif leg == "basic_10":
        out.append(f"결속 한도: 원칙 한도 쪽(SCR×10%) {r.get('tier1_basic_new_pct')}%")
    if r.get("type_unconfirmed"):
        out.append("기본자본형/보완자본형 미확정 신종 포함 — 기본자본형으로 보고 계산한 상한이며, "
                   f"보완자본형으로 확인되면 {r.get('tier1_pct_if_unconfirmed_tier2')}%")
    return " / ".join(out)


def _flatten_tier1(raw: dict) -> list:
    lut = _kics_company_lookup()
    q = raw.get("quarter")
    rows = []
    for r in raw.get("results", []):
        base = _company_base(r.get("code"), r.get("company"), lut)
        issued_note = _TIER1_ISSUED_NOTE if r.get("issued_source") == "missing" else ""
        for field, label in _TIER1_ITEMS:
            row = dict(base)
            row["공시분기"] = q
            row["항목명"] = label
            v = r.get(field)
            row["값"] = v
            notes = []
            if field in _TIER1_NOTE_FIELDS and issued_note:
                notes.append(issued_note)
            basis = _TIER1_BASIS_NOTE.get(field)
            if basis:
                notes.append(basis)
                if field in ("utilization_pct", "utilization_pct_strict") and (v or 0) > 100.0:
                    notes.append(_TIER1_OVER100_NOTE)
            if field == "utilization_pct" and _tier1_row_note(r):
                notes.append(_tier1_row_note(r))
            row["비고"] = " / ".join(notes)
            rows.append(row)
    return rows


_TIER2_ITEMS = [
    ("tier2_limit_eok", "보완자본 인정한도(SCR x 50%)"),
    ("numerator_eok", "보완자본 인정한도 소진 분자"),
    ("utilization_pct", "보완자본 소진율"),
    ("tier2_eok", "보완자본 총액(경과조치 후)"),
    ("pre_limit_eok", "보완자본 한도적용전 잔액"),
    ("lapse_excess_eok", "해약환급금준비금 상당액 초과분(한도제외)"),
    ("hybrid_eok", "기발행 신종자본증권(보완자본 재분류분)"),
    ("subordinated_eok", "기발행 후순위채무"),
    ("new_subordinated_gross_eok", "신규(2023~) 후순위채 발행총액"),
    ("new_subordinated_recognized_eok", "신규(2023~) 후순위채 인정액"),
    ("tier1_overflow_into_tier2_eok", "기본자본 한도초과분의 보완자본 재분류"),
    ("grandfathered_hybrid_eok", "경과조치 인정 신종자본증권(레거시)"),
    ("grandfathered_subordinated_eok", "경과조치 인정 후순위채무(레거시)"),
    ("proxy_utilization_pct", "보완자본 소진율(구 산식, 참고용)"),
]
# 2026-08-29 census (validate_data_contract.py CHECK4 domain-identity, live): RED=0
# YELLOW=0 on tier1/tier2 today -- the "4개사 분자 불안정" issue this ticket's brief
# describes matches output/tier2_utilization/outlier_report_20261Q.json (2026-06-16,
# STALE — 5 companies over the OLD proxy_utilization_pct metric: 동양240%/하나손해235%/
# KB218%/악사197%/미래126%), already fixed by inbox/_resolved/20260620T0238Z (numerator
# switched from item3-proxy to DART bond-level issuance). Current utilization_pct has 0
# companies outside [0,100] (39/39 in range). proxy_utilization_pct is kept in the JSON
# on purpose as an audit trail of the old (broken) methodology, not a live defect — the
# note below documents that distinction so nobody downstream mistakes it for current.
_TIER2_PROXY_NOTE = ("2026-06-20 폐기된 구 산식(item3 총보완자본 raw 기준) — 한도제외 대상인 "
                      "해약환급금준비금 초과분이 섞여 부풀었던 값(예: 동양생명 240%, KB손해보험 218%). "
                      "신종/후순위 발행잔액이 아니다. 현재 헤드라인은 '보완자본 소진율' 행(2026-10-12 규정 근거 "
                      "재정의: 분자 = 보완자본 한도 적용 전, 경과조치 적용 후 기준).")
# 2026-10-12 규정 근거 재정의(scripts/capital_utilization_rules.py). '소진 분자'·'소진율' 행에 회사별로
# 어떤 인쇄 관행을 어떻게 정규화했는지(배포 JSON 의 numerator_source·rule_basis)를 실어 보낸다 —
# xlsx 만 받은 사람에게는 이 칸이 유일한 근거다. 'R2' 같은 내부 규칙 번호는 싣지 않는다.
_TIER2_UTIL_NOTE = ("분자 = 보완자본 - 해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분 - 기발행 "
                    "자본증권(공통적용 경과조치; 2022년 12월 31일까지 발행한 신종·후순위의 채권원장 잔액만 뺀다 - 발행사가 "
                    "인쇄한 기발행 금액에는 2023년 이후 발행분이 섞여 있을 수 있어 쓰지 않는다), 분모 = 총요구자본"
                    "(경과조치 적용 전) × 50% ([별표22] Ⅲ.2.마·Ⅵ.1.가.(3)·Ⅵ.1.라).")
# 2026-10-12: 이 칸은 예전 채권원장 추정(발행액 - SCR x 15%)이 갱신 없이 남아 있었다. 지금은 기본자본 소진율과 같은
# 출처(공시 보통주 이외 자본증권 + 등재부 분류)에서 나온 한도 초과 재분류액이다.
_TIER2_OVERFLOW_NOTE = ("기본자본 자본증권(기발행은 총요구자본 x 15%, 신규 기본자본형은 x 10%) 인정한도를 넘어 보완자본으로 "
                        "재분류되는 금액의 산출값(공시 보통주 이외 자본증권과 증권별 분류에서 계산, 기본자본 소진율 시트의 한도초과분과 "
                        "같은 값). 신규분 초과는 위 보완자본 소진 분자에 이미 들어 있어 따로 더하지 않고, 기발행분 초과는 경과조치에 따라 "
                        "분자에서 제외된다.")
_TIER2_OVER100_NOTE = ("100% 초과 = 보완자본 한도 초과 — 초과분은 지급여력금액에서 불인정"
                       "([별표22] Ⅲ.1.라.(6)). 화면에는 '100%+'로 표기됨.")


def _flatten_tier2(raw: dict) -> list:
    lut = _kics_company_lookup()
    q = raw.get("quarter")
    rows = []
    for r in raw.get("results", []):
        base = _company_base(r.get("code"), r.get("company"), lut)
        for field, label in _TIER2_ITEMS:
            row = dict(base)
            row["공시분기"] = q
            row["항목명"] = label
            row["값"] = r.get(field)
            note = _TIER2_PROXY_NOTE if field == "proxy_utilization_pct" else ""
            if field == "tier1_overflow_into_tier2_eok":
                note = _TIER2_OVERFLOW_NOTE
            if field in ("grandfathered_hybrid_eok", "grandfathered_subordinated_eok") and r.get(field) is not None:
                printed = r.get(field.replace("_eok", "_printed_eok"))
                note = ("보완자본 분자에서 뺀 기발행 금액 = 채권원장의 2022년 12월 31일까지 발행한 "
                        + ("신종" if "hybrid" in field else "후순위") + "자본증권 잔액"
                        + (f" (발행사가 경영공시에 인쇄한 금액 {printed:,.2f}억원은 2023년 이후 발행분이 섞여 있을 수 있어 쓰지 않음)"
                           if printed is not None else ""))
            if field == "numerator_eok" and r.get("rule"):
                note = r.get("numerator_source") or r.get("rule_basis") or ""
            if field == "utilization_pct" and r.get("rule"):
                parts = [_TIER2_UTIL_NOTE, r.get("rule_basis") or ""]
                if r.get("reason"):
                    parts.append(r["reason"])
                if (r.get("utilization_pct") or 0) > 100.0:
                    parts.append(_TIER2_OVER100_NOTE)
                note = " / ".join(p for p in parts if p)
            row["비고"] = note
            rows.append(row)
    return rows


_FORWARD_ITEMS = [
    ("ratio_pct", "지급여력비율 전망"),
    ("basic_ratio_pct", "기본자본비율 전망"),
    ("capital_eok", "가용자본 전망"),
    ("basic_capital_eok", "기본자본 전망"),
    ("scr_eok", "지급여력기준금액(SCR) 전망"),
    ("cumulative_bond_dedu_eok", "누적 채무성자본 콜상환 차감액"),
    ("cumulative_tier1_dedu_eok", "누적 기본자본 신종 콜상환 차감액"),
    ("hybrid_remaining_eok", "잔존 신종자본증권(기본자본 인정분)"),
    ("hybrid_tier1_eok", "기본자본 인정 신종자본증권(연도말)"),
    ("hybrid_tier2_overflow_eok", "기본자본 한도초과 보완자본 이관분(연도말)"),
    ("hybrid_limit_eok", "기본자본 신종 인정한도(연도별 SCR 기준)"),
]
# baseline/baseline_2025_4Q intentionally NOT emitted as rows: they duplicate items
# 1/14/27 already in the K-ICS공시 sheet at 공시분기=2026.1Q — re-flattening them here
# would (a) add no new information and (b) force mixing "2026.1Q"-style and plain-year
# "2026" labels in the same 공시분기 column for one company, which is exactly the
# non-standard-label sort risk export_public_sheets.py:41-44 documents (checked; see
# this ticket's report). scr_interp_progress dropped: pure (year-2025)/7 restatement of
# the year already carried by 공시분기. capacity_exhausted/basic_capacity_exhausted
# folded into 비고 (see below) rather than emitted as 0/1 rows.


def _flatten_forward_capital(raw: list) -> list:
    lut = _kics_company_lookup()
    call_fallback = _call_fallback_codes()
    rows = []
    for r in raw:
        if r.get("status") != "ok":
            continue
        code = r.get("insurer_code")
        base = _company_base(code, r.get("insurer_name"), lut)
        conf = r.get("confidence") or {}
        notes = []
        if r.get("bond_coverage") == "no_bonds_in_dart":
            notes.append("DART 자본성증권 발행 원자료 없음 — 콜상환 차감 없이 SCR 선형보간만 반영")
        if code in call_fallback:
            notes.append("콜옵션 미공시 채권 포함 — 콜일자를 발행일+5년/신용등급이력 등으로 추정 "
                         "(원문 미기재), 실제 콜상환 시점과 다를 수 있음")
        if conf.get("level") == "low":
            notes.append("신뢰도 낮음(발행잔액 vs BS 괴리)")
        base_note = " / ".join(notes)
        # inbox/publishing/20260921T0320Z (owner): compute_confidence()'s `reasons` list
        # is internal gate-diagnostic text (field names like subordinated_eok, gate terms
        # like "advisory, not in overall") for triage, not something a reader of this sheet
        # can interpret. Keep it, but split into its own column instead of folding it into
        # 비고 — export_public_sheets.py drops this column from the public download so only
        # the user-meaningful notes above travel with the public snapshot.
        diagnostics = "; ".join(conf.get("reasons") or [])
        for p in r.get("projections", []):
            for field, label in _FORWARD_ITEMS:
                row = dict(base)
                row["공시분기"] = str(p.get("year"))
                row["항목명"] = label
                row["값"] = p.get(field)
                note = base_note
                if field == "ratio_pct" and p.get("capacity_exhausted"):
                    note = (note + " / " if note else "") + "자본잠식(가용자본<=0) — 비율 0%로 캡 표시"
                if field == "basic_ratio_pct" and p.get("basic_capacity_exhausted"):
                    note = (note + " / " if note else "") + "기본자본 잠식(가용 기본자본<=0) — 비율 0%로 캡 표시"
                row["비고"] = note
                row["_diagnostics"] = diagnostics
                rows.append(row)
    return rows


def _flatten_capital_securities(doc):
    """이미 한 건 = 한 행이라 rows 만 꺼내면 된다(집계 해체가 필요 없다)."""
    rows = doc.get("rows", []) if isinstance(doc, dict) else (doc or [])
    out = []
    for r in rows:
        row = {k: v for k, v in r.items() if k != "flags_missing"}
        miss = r.get("flags_missing") or []
        row["비고"] = ("원천에 " + "·".join(miss) + " 플래그가 없어 신규분 10%/15% 판정과 "
                       "상환촉진 유인 콜 판정은 미확정 — 체감은 법정만기일 기준") if miss else ""
        out.append(row)
    return out


_SHEET_DROP_COLS = ("출처", "추출방식", "플래그")


def _drop_provenance(rows, extra=()):
    """유지율·손해율: owner 가 시트에서 지운 출처·추출방식·플래그 열을 뺀다(JSON 에는 남는다)."""
    drop = set(_SHEET_DROP_COLS) | set(extra)
    return [{k: v for k, v in r.items() if k not in drop} for r in rows]


def _drop_loss_ratio_cols(rows):
    """손해율: 원문 라벨 열도 뺀다(owner 2026-10-08) — 빼도 행 키 중복 0, 원문은 JSON 에 남는다."""
    return _drop_provenance(rows, extra=("원문구분", "원문포트폴리오"))


# ---------------------------------------------------------------------------
# 보험계약부채 시트 (insurance_liability_portfolio.json) — 2026-10-11.
# 마스터는 이미 long-format 이다. 여기서 붙이는 것은 세 열뿐이다: 단위(항목 9 만 0/1 플래그라
# 억원이 아니다) · 기준표시(값을 어느 공시·기준에서 읽었나) · 비고(소급재작성·순액·계산값).
# 기준표시는 insurance_liability_portfolio_provenance.json 의 `basis` 를 한글로 옮긴 것이고,
# 영문 코드(latest_filing_comparative_restatable 등)는 공개 다운로드에 그대로 나가지 않게 한다.
# 항목 블록마다 근거 목록이 다르다: 1~8 = lrc_model_cells, 9 = item9_cells(또는 lrc_model_cells),
# 10~15 = cells, 16·17 = indirect_lic_cells. 근거가 없는 셀은 추측하지 않고 비운다 — 단, 2-4/2-5 표가
# 생긴 2025.1Q 이후의 1~9 는 provenance scope("items 1-9 are the 경영공시 2-4/2-5 extract")와
# 검증 게이트(R2_CENSUS)가 정의하는 대로 그 분기 공시 자체다.
# ---------------------------------------------------------------------------
_ILP_PROVENANCE = "insurance_liability_portfolio_provenance.json"
_ILP_FIRST_OWN_FILING_QUARTER = "2025.1Q"   # 경영공시 2-4/2-5 신설 분기 (validate_insurance_liability_portfolio.py)

_ILP_LRC_BASIS_LABEL = {
    "own_filing": "해당 분기 공시",
    "latest_filing_comparative": "최신 공시 비교열",
    "latest_filing_comparative_restatable": "최신 공시 비교열(소급재작성)",
}
_ILP_LIC_BASIS_LABEL = {"liability": "부채 기준", "net": "순액 기준"}
_ILP_NOTE_RESTATED = ("최신 공시의 소급재작성 비교 잔액이다 — 당시 원 공시 잔액과 다를 수 있다 "
                      "(재작성 사유는 원문 감사보고서 강조사항)")
_ILP_NOTE_NET = ("보험계약자산을 차감한 순부채(순액)만 공시돼 있어 재무상태표 보험계약부채보다 "
                 "그 상계액만큼 작다")
_ILP_NOTE_DERIVED = ("직접 공시값이 아닌 계산값 — 측정요소별 변동표의 기말 {what} 합계에서 잔여보장요소 {what}"
                     "(항목 {lrc})를 뺀 간접 산출. 단일열로 공시된 발생사고요소(항목 13)를 허용오차 안에서 "
                     "재현하는 경우만 적재")
# 2026-10-12 스위스리아시아 2026.1Q: 원문 인쇄 합계 행이 간접 참가(Indirect-Par) 행을 뺀 값이라, 인쇄된 모든 행을 더해 적재했다
# (owner 결정, provenance `how` = derived_sum_of_rows). 기준표시는 그대로 두지 않고 계산값으로 밝힌다.
_ILP_HOW_ROW_SUM = "derived_sum_of_rows"
_ILP_LABEL_ROW_SUM = "계산값(전 행 합)"
_ILP_NOTE_ROW_SUM = ("직접 공시값이 아닌 계산값 — 원문의 인쇄 합계 행이 간접 참가(Indirect-Par) 행을 뺀 값이라, "
                     "인쇄된 생명·손해 전 행을 더해 적재했다")
_ILP_UNIT_FLAG = "여부(1=사용, 0=미사용)"


def _ilp_provenance_index() -> dict:
    """provenance 를 (회사코드, 분기) 로 색인. 파일이 없으면 조용히 빈 기준표시를 내지 않고 실패한다."""
    doc = json.loads((REPO / _ILP_PROVENANCE).read_text(encoding="utf-8"))

    def by_cell(key: str) -> dict:
        return {(x["company_code"], x["quarter"]): x for x in doc.get(key, [])}

    return {"lrc": by_cell("lrc_model_cells"), "lic": by_cell("cells"),
            "indirect": by_cell("indirect_lic_cells"), "item9": by_cell("item9_cells")}


def _ilp_lrc_label(cell: dict) -> str:
    basis = cell.get("basis")
    if basis is not None:
        return _ILP_LRC_BASIS_LABEL[basis]        # 모르는 값이면 KeyError — 조용히 비우지 않는다
    # 연말 4-6-2 표(basis 미기재): 비교열에서 읽었는지가 published_in 에 적혀 있다
    return ("최신 공시 비교열" if "comparative column" in (cell.get("published_in") or "")
            else "해당 분기 공시")


def _ilp_basis_note(item: int, key: tuple, ix: dict) -> tuple:
    """(기준표시, 비고) — 근거가 없으면 ('', '')."""
    own_filing_era = key[1] >= _ILP_FIRST_OWN_FILING_QUARTER   # '2025.1Q' 형은 문자열 비교로 충분
    if 1 <= item <= 8:
        c = ix["lrc"].get(key)
        if c is None:
            return ("해당 분기 공시", "") if own_filing_era else ("", "")
        if c.get("how") == _ILP_HOW_ROW_SUM:
            return _ILP_LABEL_ROW_SUM, _ILP_NOTE_ROW_SUM
        label = _ilp_lrc_label(c)
        return label, (_ILP_NOTE_RESTATED if c.get("basis") == "latest_filing_comparative_restatable" else "")
    if item == 9:
        c = ix["lrc"].get(key)
        if c is not None and c.get("item9") is not None:
            return _ilp_lrc_label(c), ""
        if key in ix["item9"]:
            return "공시 본문 문구(예외모형 선택)", ""
        return ("해당 분기 공시", "") if own_filing_era else ("", "")
    if 10 <= item <= 15:
        c = ix["lic"].get(key)
        if c is None:
            return "", ""
        label = _ILP_LIC_BASIS_LABEL[c["basis"]]
        notes = []
        if "original_basis" in c:                  # 소급재작성 셀: 원 공시 기준값을 따로 보관 중인 8셀
            label += "(소급재작성)"
            notes.append(_ILP_NOTE_RESTATED)
        if c["basis"] == "net":
            notes.append(_ILP_NOTE_NET)
        return label, " / ".join(notes)
    if item in (16, 17):
        c = ix["indirect"].get(key)
        if c is None:
            return "", ""
        return "계산값(간접 산출)", (_ILP_NOTE_DERIVED.format(what="최선추정", lrc="1+4") if item == 16
                      else _ILP_NOTE_DERIVED.format(what="위험조정", lrc="2+5"))
    return "", ""


def _flatten_insurance_liability_portfolio(rows: list) -> list:
    ix = _ilp_provenance_index()
    out = []
    for r in rows:
        row = dict(r)
        item = int(r["항목번호"])
        label, note = _ilp_basis_note(item, (r["원보험사코드"], r["공시분기"]), ix)
        row["단위"] = _ILP_UNIT_FLAG if item == 9 else "억원"
        row["기준표시"] = label
        row["비고"] = note
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# 보험금예실차비율 시트 (data/loss_ratio/claims_ae_ratio.json) — 2026-10-12.
# 열은 마스터 필드 그대로 + 티커(K-ICS 공시에서). 출처 {file, page} 는 쪽 번호만(출처쪽), 파일 경로는 내부 경로라 싣지 않는다.
# 추출방식·원천위치·원문·identity 는 JSON 에만 남는다(identity_break 는 162행 전부 False). 영문 플래그 코드는 한글 문구로
# 옮긴다 - 모르는 코드는 조용히 통과시키지 않고 KeyError 로 멈춘다(새 코드가 생기면 문구를 정한 뒤 늘린다).
# ---------------------------------------------------------------------------
_AE_FLAG_LABEL = {
    "year_from_caption": "기준연도는 표 제목에서 읽음",
    "year_from_context": "기준연도는 표 주변 문맥에서 읽음",
    "transposed": "원문 표가 연도를 열로 둔 형식이라 행·열을 바꿔 읽음",
    "해당없음_빗금": "해당 없음(빗금)으로 공시됨",
}


def _ae_flag_text(flags: list) -> str:
    out = []
    for f in flags or []:
        # 이미 사람이 쓴 한글 메모(예: 감사보고서 사본 대조)는 그대로, 영문 코드는 사전으로 옮긴다
        out.append(f if any("가" <= ch <= "힣" for ch in f) and f not in _AE_FLAG_LABEL else _AE_FLAG_LABEL[f])
    return " / ".join(out)


def _flatten_claims_ae_ratio(rows: list) -> list:
    lut = _kics_company_lookup()
    out = []
    for r in rows:
        base = _company_base(r["원보험사코드"], r["원수사명"], lut)
        out.append({
            "원보험사코드": base["원보험사코드"], "원수사명": r["원수사명"], "티커": base["티커"],
            "생손보여부": r["생손보여부"], "공시분기": r["공시분기"], "기준연도": str(r["기준연도"]),
            "사업구분": r.get("사업구분"),
            "예상손해율": r["예상손해율"], "실제손해율": r["실제손해율"], "예실차비율": r["예실차비율"],
            "단위": r["단위"], "출처쪽": (r.get("출처") or {}).get("page"),
            "플래그": _ae_flag_text(r.get("플래그")),
        })
    return out


FLATTEN = {
    "data/loss_ratio/claims_ae_ratio.json": _flatten_claims_ae_ratio,
    "insurance_liability_portfolio.json": _flatten_insurance_liability_portfolio,
    "data/persistency/master_persistency.json": _drop_provenance,
    "data/loss_ratio/master_loss_ratio.json": _drop_loss_ratio_cols,
    "kics_capital_securities.json": _flatten_capital_securities,
    "kics_tier1_utilization.json": _flatten_tier1,
    "kics_tier2_utilization.json": _flatten_tier2,
    "kics_forward_capital.json": _flatten_forward_capital,
}


def main():
    frames = []
    for fn, sheet, desc in MASTERS:
        data = json.loads((REPO / fn).read_text(encoding="utf-8"))
        if fn in FLATTEN:
            data = FLATTEN[fn](data)
        df = pd.DataFrame(data)
        df = coerce(df)
        frames.append((sheet, df, fn, desc))

    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        # placeholder index first (filled after we know counts)
        pd.DataFrame({"_": []}).to_excel(xw, sheet_name="요약", index=False)
        for sheet, df, _fn, _desc in frames:
            df.to_excel(xw, sheet_name=sheet, index=False)

    wb = load_workbook(OUT)

    # ---- 요약 (index) sheet ----
    idx = wb["요약"]
    idx.delete_cols(1, 4)
    idx["A1"] = "Insurequant 마스터테이블 통합"
    idx["A1"].font = Font(name=FONT, bold=True, size=14)
    headers = ["시트", "마스터 파일", "행수", "설명"]
    idx.append([])
    idx.append(headers)
    hdr_row = 3
    for sheet, df, fn, desc in frames:
        idx.append([sheet, fn, len(df), desc])
    idx.append(["합계", "", sum(len(df) for _s, df, _f, _d in frames), ""])
    # style index
    for c in range(1, 5):
        cell = idx.cell(row=hdr_row, column=c)
        cell.font = Font(name=FONT, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="305496")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    total_row = hdr_row + 1 + len(frames)
    for r in range(hdr_row + 1, total_row + 1):
        bold = (r == total_row)
        for c in range(1, 5):
            idx.cell(row=r, column=c).font = Font(name=FONT, bold=bold)
        idx.cell(row=r, column=3).alignment = Alignment(horizontal="right")
        idx.cell(row=r, column=3).number_format = "#,##0"
    idx.column_dimensions["A"].width = 16
    idx.column_dimensions["B"].width = 30
    idx.column_dimensions["C"].width = 10
    idx.column_dimensions["D"].width = 70
    idx.sheet_view.showGridLines = False

    # ---- data sheets ----
    thin = Side(style="thin", color="D9D9D9")
    for sheet, df, _fn, _desc in frames:
        ws = wb[sheet]
        ncol = ws.max_column
        nrow = ws.max_row
        # header style
        for c in range(1, ncol + 1):
            cell = ws.cell(row=1, column=c)
            cell.font = Font(name=FONT, bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="305496")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(bottom=thin)
        # body font + number format
        cols = [ws.cell(row=1, column=c).value for c in range(1, ncol + 1)]
        for c, name in enumerate(cols, start=1):
            letter = ws.cell(row=1, column=c).column_letter
            for r in range(2, nrow + 1):
                cl = ws.cell(row=r, column=c)
                cl.font = Font(name=FONT)
                if name in NUMERIC_COLS and isinstance(cl.value, (int, float)):
                    cl.number_format = "#,##0.##;(#,##0.##);-"
            # column width (approx from header + name length)
            base_w = {"원수사명": 22, "항목명": 30, "설명": 60}.get(name, 0)
            ws.column_dimensions[letter].width = base_w or max(11, min(28, len(str(name)) + 6))
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=ncol).column_letter}{nrow}"

    # order: 요약 first
    wb.move_sheet("요약", -(wb.sheetnames.index("요약")))
    wb.save(OUT)
    print(f"wrote {OUT.name}: {len(frames)} master sheets + 요약")
    for sheet, df, _fn, _desc in frames:
        print(f"  {sheet:14s} {len(df):6d} rows x {len(df.columns)} cols")


if __name__ == "__main__":
    main()
