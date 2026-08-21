"""K-ICS disclosure JSON cross-check rules (item-number keyed rows).

R4 (4x4, life-nl=0 others 0.25, item21 excluded from V):
  V = (item17, item18, item19, item20). item15 = sqrt(V' R4 V) + item21.

R7 (7x7 sub-risk matrix from K-ICS standard, items 29-35):
  item17 = sqrt(S' R7 S) when all sub-items present.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

import numpy as np

KEY_CODE = "원보험사코드"
KEY_NAME = "원수사명"
KEY_QUARTER = "공시분기"
KEY_ITEM = "항목번호"
KEY_VALUE = "값"
KEY_VALUE_POST = "값_적용후"

R4: np.ndarray = np.array(
    [
        [1.0, 0.0, 0.25, 0.25],
        [0.0, 1.0, 0.25, 0.25],
        [0.25, 0.25, 1.0, 0.25],
        [0.25, 0.25, 0.25, 1.0],
    ],
    dtype=float,
)

R7: np.ndarray = np.array(
    [
        [1.0, -0.25, 0.25, 0.0, 0.0, 0.25, 0.25],
        [-0.25, 1.0, 0.0, 0.0, 0.25, 0.25, 0.0],
        [0.25, 0.0, 1.0, 0.0, 0.0, 0.5, 0.25],
        [0.0, 0.0, 0.0, 1.0, 0.0, 0.5, 0.25],
        [0.0, 0.25, 0.0, 0.0, 1.0, 0.5, 0.25],
        [0.25, 0.25, 0.5, 0.5, 0.5, 1.0, 0.25],
        [0.25, 0.0, 0.25, 0.25, 0.25, 0.25, 1.0],
    ],
    dtype=float,
)
R7 = np.maximum(R7, R7.T)
np.fill_diagonal(R7, 1.0)

# Market sub-risk matrix M (item19 = sqrt(V'·M·V), V=[36,37,38,39,40] = 금리·주식·부동산·외환·자산집중).
# Source: kics-market-risk-decomposition.md §2 (<표19>). 대각 1.0, 외환-주식 −0.25,
# 자산집중 행/열 0(대각 제외), 그 외 비대각 0.25.
MARKET_M: np.ndarray = np.array(
    [
        [1.00, 0.25, 0.25, 0.25, 0.00],
        [0.25, 1.00, 0.25, -0.25, 0.00],
        [0.25, 0.25, 1.00, 0.25, 0.00],
        [0.25, -0.25, 0.25, 1.00, 0.00],
        [0.00, 0.00, 0.00, 0.00, 1.00],
    ],
    dtype=float,
)

STATUS_RED = "RED"
STATUS_YELLOW = "YELLOW"
STATUS_GREEN = "GREEN"
STATUS_ERROR = "ERROR"
STATUS_SKIP = "SKIP"

# Image-only PDF insurers: OCR rounding may exceed default tolerance (see KICS-IMG).
IMAGE_OCR_TOLERANCE = 10.0
IMAGE_OCR_COMPANIES = frozenset({"KR0010", "KR0079"})

# 19_market 부모-자식 완전성 면제: item19 공시인데 36-40 분해가 진짜 미공시인 (회사,분기).
# raw MD/PDF에 분해표가 실제로 없음을 교차검증한 케이스만 등록(문서화 면제). 기본 비어있음
# = "부모 공시면 분해도 있어야 한다"가 기본, 빠지면 RED(parser gap 추정).
MARKET_BREAKDOWN_EXEMPT: frozenset[tuple[str, str]] = frozenset()

# 36_irr 시나리오 완전성 면제: item36 공시인데 41-46(금리위험 순자산가치 6시나리오)이 진짜 미공시인
# (회사,분기). 41-46은 **짝수분기(2Q/4Q) 서식에만** 존재 — 홀수분기(1Q/3Q)는 시나리오표가 서식에
# 원천부재라 SKIP이 정당(RED 아님). 짝수분기인데 item36 공시·41-46 결측이면 parser gap → RED.
# raw에 짝수분기에도 시나리오표 없음을 교차검증한 케이스만 등록(문서화 면제). 기본 비어있음.
IRR_SCENARIO_EXEMPT: frozenset[tuple[str, str]] = frozenset()

# 36_irr 내부모형 면제. **2026-08-21 전건 해제 — 등재사유가 raw 대조에서 거짓으로 확인됐다.**
#
# 종전 사유: "내부모형사 — 회사가 시나리오별 금리위험액을 **직접 공시**하고 그 값을 같은 식에 넣으면
# 공시총액과 정확 일치(KR0094 2025.4Q=578,999 검증)". validation 이 2026-08-21 에 다섯 건의 raw 를
# 전부 열어(fitz 텍스트 + 240dpi 렌더링 육안) 확인한 결과 **두 전제가 모두 사실이 아니었다**:
#
#   ① 다섯 건 모두 표준서식 [② 금리위험액 현황] 표를 그대로 싣는다 — 충격 전 + 충격후 5시나리오
#      (평균회귀·금리상승·금리하락·금리평탄·금리경사) 열에 `Ⅲ. 순자산가치` 행이 완비돼 있다.
#      즉 항목 41-46 의 원천은 실재하고, 마스터에 없는 것은 **추출갭**이지 원천부재가 아니다.
#        KR0073 2025.2Q  FY2025_Q2 raw p21   (Ⅳ.금리위험액 459,988 = 마스터 item36 4,599.88)
#        KR0094 2024.2Q  FY2024_Q2 raw p22   (750,104 = 7,501.04)
#        KR0094 2024.4Q  FY2024_Q4 raw p144  (633,214 = 6,332.14)
#        KR0094 2025.2Q  FY2025_Q2 raw p28   (931,833 = 9,318.33)
#        KR0094 2025.4Q  FY2025_Q4 raw p131  (578,999 = 5,789.99)
#   ② `Ⅳ. 금리 위험액` 은 표 전체 폭을 덮는 **단일 병합셀**이다 — 시나리오별로 쪼개져 있지 않다.
#      "회사가 시나리오별 금리위험액을 직접 공시" 는 어느 페이지에서도 성립하지 않는다.
#   ③ 결정적으로 KR0094 는 스스로 **표준모형사**라고 적는다: FY2025_Q4 raw p135 "회사는
#      보험업감독업무시행세칙 [별표22] … 기준에 따라 시장위험액을 측정하고 있습니다" + 표준식
#      "금리위험액 = √max(금리상승, 금리하락)² + √max(금리평탄, 금리경사)² + 평균회귀금액".
#      '내부모형사' 라는 면제 이름 자체가 원문과 어긋난다.
#
# 해제하면 다섯 건 전부 36_irr RED("even quarter 인데 41-46 결측 = parser gap")가 된다. 그게 참이다 —
# 표는 원천에 있고 우리가 안 읽었을 뿐이다. **표준식이 공시총액을 재현하지 못하는 것은 별개의 미해결
# 질문**이고(추출 후 교보 25.2Q +5.5% · 신한 +8~34%), 그 건으로 새 면제를 만들려면 owner 승인이
# 필요하다. 검증 stage 는 반증된 면제를 지울 수 있을 뿐 새 면제를 만들지 않는다.
INTERNAL_MODEL_36IRR_EXEMPT: frozenset[tuple[str, str]] = frozenset()

# ---------------------------------------------------------------------------
# 36_irr documented exception — **통째 skip 이 아니라 '잔차 박제'다** (owner 2026-08-21 승인)
# ---------------------------------------------------------------------------
# 대상은 아래 5개 (회사,분기)뿐이다. 이 다섯은 41-46 이 원문 그대로 적재돼 있는데도 표준 도출식이
# 공시 금리위험액(item36)을 재현하지 못한다. **데이터가 아니라 재현식이 이 회사들에 안 맞는다**:
#
#   ① item36 자체는 정상값이다 — 같은 item36 을 시장위험 축에 넣으면 닫힌다.
#      실측 `item19 == sqrt(item36~40 · MARKET_M)` 잔차: 교보 25.2Q −0.0042(−0.0000%) ·
#      신한 24.2Q −0.3312 · 24.4Q −0.2521 · 25.2Q −0.3338 · 25.4Q +0.4791 (전부 |rel| ≤ 0.0022%).
#      즉 공시 금리위험액은 **다른 축에서 검산되는 값**이고, 안 맞는 것은 41-46 부속표 재현뿐이다.
#   ② 41-46 은 원문 그대로다. raw 대조(fitz, 아래 provenance 원장의 present_markers 와 동일):
#      교보 25.2Q p21 Ⅲ.순자산가치 -5,667,711/-5,414,904/-6,352,338/-5,586,899/-5,463,138/-5,742,051,
#      Ⅳ.금리위험액 459,988 → 마스터 item41~46·item36 과 백만원↔억원 환산까지 정확 일치.
#      신한 24.2Q p22(750,104) · 24.4Q p144(633,214) · 25.2Q p28(931,833) · 25.4Q p131(578,999) 동일.
#   ③ **현행 식이 옳다 — 전사로 검증했다.** owner 가 "평균회귀 충격량도 0 으로 절단해야 하지
#      않냐"고 지적해 41-46 완비 226버킷 전수 재측정(validation 2026-08-21):
#         A 현행 signed 평균회귀 : 221/226 (97.8%)
#         B 평균회귀도 0 절단     : 123/226 (54.4%)
#      판정이 갈리는 102건 중 **100건이 A만 통과**(B-only 2건은 이 면제 대상인 신한 25.2Q·25.4Q).
#      A 는 소수점까지 맞는다(메리츠 23.4Q 공시 5,060.65 vs A 5,060.66 · 삼성화재 등).
#      **평균회귀 이익을 상계하는 것이 실제 서식이다 → 식은 건드리지 않는다.**
#   ④ 교보는 하한 자체를 못 지킨다. 25.2Q 금리상승 단일 충격량 684,627 백만원(= -5,667,711 −
#      (-6,352,338))이 공시 금리위험액 459,988 보다 크다. 어떤 합성식을 써도 최악 단일 시나리오보다
#      작아질 수 없다 → 표의 순자산가치와 공시 위험액이 같은 기준이 아니다.
#   ⑤ **원인 미규명(UNEXPLAINED).** 신한 24.4Q raw p144 주2 "2024년부터 금리위험액 현황의 자산 및
#      부채는 금리위험에 직·간접적으로 노출된 자산 및 부채를 대상으로 작성" 은 작성기준 변경을
#      명시하지만 **잔차를 설명하지 못한다** — 금리에 둔감한 항목은 모든 시나리오 열에 동일하게
#      들어가 열 간 차이(=충격량)에서 상쇄된다. 게다가 그 주2 는 25.2Q(p28)·25.4Q(p131)에는
#      아예 없는데 잔차는 그대로다(+7.5% · +14.9%). "스코프 때문"이라고 단정하지 말 것.
#
# 설계 원칙 — **통째 skip 금지**(_LIFE8_ISSUER_INCONSISTENT 와 동형). 기대잔차를 값으로 박제하고
# 매 실행 마스터에서 재계산한다. item36 이나 41-46 중 한 칸이라도 바뀌어 잔차가 박제값에서
# 벗어나면 면제가 깨지고 **다시 RED** 다. blanket skip 은 이 셀을 영구 사각지대로 만든다.
#
# **적용전·적용후 두 컬럼을 각각 박제한다.** 같은 미정합이 게이트에 RED 를 두 번 만든다:
# 룰엔진 `36_irr`(적용전) + 게이트 `_transition_irr_after` 축(적용후 = TRANSITION_AFTER_IRR_MISMATCH).
# 적용전만 면제하면 적용후가 그대로 막는다 — KR0079 8_life 때 실제로 그랬다.
# (이 다섯 건은 41-46 후 == 41-46 전 미러라 두 컬럼의 잔차가 같지만, 값이 아니라 **컬럼별로**
#  재계산·대조한다 — 미러가 깨지면 그것도 검출돼야 한다.)
#
# 잔차 부호 = item36(공시) − derive(41-46). 전부 양수(공시 > 도출).
IRR_DERIVE_ISSUER_INCONSISTENT: dict[tuple[str, str], dict[str, float]] = {
    ("KR0073", "2025.2Q"): {"적용전": 241.4373504145833, "적용후": 241.4373504145833},
    ("KR0094", "2024.2Q"): {"적용전": 1287.8295634268043, "적용후": 1287.8295634268043},
    ("KR0094", "2024.4Q"): {"적용전": 1622.0506399332953, "적용후": 1622.0506399332953},
    ("KR0094", "2025.2Q"): {"적용전": 698.1839921629144, "적용후": 698.1839921629144},
    ("KR0094", "2025.4Q"): {"적용전": 863.8221082879018, "적용후": 863.8221082879018},
}
# 박제 허용오차. 마스터 셀은 소수 2자리라 재계산이 결정론적이다 — 느슨하게 잡는 순간
# '박제'가 아니라 또 하나의 blanket skip 이 된다. (룰 허용오차는 손대지 않는다: 잔차가 5~26% 다.)
IRR_PIN_TOL = 0.01

# 36_irr 도출식 입력 항목. 41=충격 전 순자산 · 42=평균회귀 · 43=금리상승 · 44=금리하락 ·
# 45=금리평탄 · 46=금리경사. 게이트의 적용후 축이 **여기서 import** 한다(재타이핑 금지).
IRR_SCENARIO_ITEMS: tuple[int, ...] = (41, 42, 43, 44, 45, 46)


def irr_derive_expected(values: Mapping[int, Optional[float]]) -> Optional[float]:
    """금리위험액 = sqrt(max(R상승,R하락)² + max(R평탄,R경사)²) + R평균회귀(signed).
    R = item41 − 시나리오 순자산가치. 입력 41-46 중 한 칸이라도 결측이면 None.

    적용전(룰엔진)·적용후(게이트) 두 축이 **이 함수 하나**를 쓴다 — 재구현하면 검증기가
    검증대상과 다른 식을 쓰게 된다."""
    if any(values.get(i) is None for i in IRR_SCENARIO_ITEMS):
        return None
    base = float(values[41])
    r_up = max(base - float(values[43]), 0.0)
    r_dn = max(base - float(values[44]), 0.0)
    r_flat = max(base - float(values[45]), 0.0)
    r_steep = max(base - float(values[46]), 0.0)
    r_mr = base - float(values[42])          # 평균회귀: signed (0 절단 금지 — 위 ③ 참조)
    return float(np.sqrt(max(r_up, r_dn) ** 2 + max(r_flat, r_steep) ** 2)) + r_mr


def irr_pin_verdict(
    code: str, quarter: str, column: str, values: Mapping[int, Optional[float]]
) -> tuple[str, Optional[float], Optional[float]]:
    """등재된 잔차 박제를 **매 실행 마스터에 대고 재검산**한다.

    반환 (verdict, pinned, actual):
      NOT_PINNED     이 (회사,분기,컬럼)은 면제 등재분이 아니다 → 평소 룰대로.
      MATCH          잔차가 박제값과 일치 → 이 셀에 한해 차단하지 않는다(SKIP).
      DRIFT          잔차가 박제값에서 이탈 → owner 판단의 전제가 바뀌었다 → RED.
      INPUT_MISSING  item36 또는 41-46 결측 → 박제 확인 불가 → **SKIP 이 아니라 RED**."""
    pins = IRR_DERIVE_ISSUER_INCONSISTENT.get((code, quarter))
    if not pins or column not in pins:
        return ("NOT_PINNED", None, None)
    pinned = pins[column]
    parent = values.get(36)
    expected = irr_derive_expected(values)
    if parent is None or expected is None:
        return ("INPUT_MISSING", pinned, None)
    actual = float(parent) - expected
    if abs(actual - pinned) > IRR_PIN_TOL:
        return ("DRIFT", pinned, actual)
    return ("MATCH", pinned, actual)


def parse_numeric(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw)
    text = str(raw).strip()
    if not text or text in {"-", "—", "N/A", "n/a"}:
        return None
    text = text.replace(",", "")
    for ch in ("\u25b3", "\u25b2", "\u25bd", "\u25bc", "\u2212"):
        text = text.replace(ch, "-")
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    try:
        return float(text)
    except ValueError:
        return None


def classify_diff(diff: float, tolerance: float = 2.0) -> str:
    ad = abs(diff)
    if ad > tolerance:
        return STATUS_RED
    if ad >= 0.5:
        return STATUS_YELLOW
    return STATUS_GREEN


@dataclass(frozen=True)
class QuarterBucket:
    code: str
    name: str
    quarter: str
    values: dict[int, float]
    values_post: dict[int, float]

    @classmethod
    def from_records(cls, rows: Iterable[Mapping[str, Any]]) -> "QuarterBucket":
        rows = list(rows)
        if not rows:
            raise ValueError("empty bucket rows")
        code = str(rows[0].get(KEY_CODE, "")).strip()
        name = str(rows[0].get(KEY_NAME, "")).strip()
        quarter = str(rows[0].get(KEY_QUARTER, "")).strip()
        values: dict[int, float] = {}
        values_post: dict[int, float] = {}
        for row in rows:
            item_raw = row.get(KEY_ITEM)
            try:
                item_no = int(item_raw)
            except (TypeError, ValueError):
                continue
            val = parse_numeric(row.get(KEY_VALUE))
            if val is not None:
                values[item_no] = val
            if KEY_VALUE_POST in row:
                post = parse_numeric(row.get(KEY_VALUE_POST))
                if post is not None:
                    values_post[item_no] = post
        return cls(code=code, name=name, quarter=quarter, values=values, values_post=values_post)

    def get(self, item_no: int, *, post: bool = False) -> Optional[float]:
        if post and item_no in self.values_post:
            return self.values_post[item_no]
        return self.values.get(item_no)


def _group_records(records: Iterable[Mapping[str, Any]]) -> list[QuarterBucket]:
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for rec in records:
        code = str(rec.get(KEY_CODE, "")).strip()
        quarter = str(rec.get(KEY_QUARTER, "")).strip()
        if not code or not quarter:
            continue
        groups.setdefault((code, quarter), []).append(rec)
    return [QuarterBucket.from_records(rows) for rows in groups.values()]


def _finding(
    bucket: QuarterBucket,
    rule_id: str,
    *,
    status: str,
    expected: Optional[float],
    actual: Optional[float],
    diff: Optional[float],
    detail: str = "",
) -> dict[str, Any]:
    return {
        "rule": rule_id,
        KEY_CODE: bucket.code,
        KEY_NAME: bucket.name,
        KEY_QUARTER: bucket.quarter,
        "status": status,
        "expected": expected,
        "actual": actual,
        "diff": diff,
        "detail": detail,
    }


def _check_numeric(
    bucket: QuarterBucket,
    rule_id: str,
    expected: float,
    actual: Optional[float],
    tolerance: float,
) -> dict[str, Any]:
    if actual is None:
        return _finding(
            bucket,
            rule_id,
            status=STATUS_RED,
            expected=expected,
            actual=None,
            diff=None,
            detail="missing actual item value",
        )
    diff = actual - expected
    return _finding(
        bucket,
        rule_id,
        status=classify_diff(diff, tolerance),
        expected=expected,
        actual=actual,
        diff=diff,
    )


def _sum_optional(bucket: QuarterBucket, item_nos: Iterable[int]) -> float:
    total = 0.0
    for n in item_nos:
        v = bucket.get(n)
        if v is not None:
            total += v
    return total


def _diversified_sqrt(vector: np.ndarray, matrix: np.ndarray) -> float:
    v = np.asarray(vector, dtype=float)
    m = np.asarray(matrix, dtype=float)
    inner = float(v @ m @ v)
    if inner < 0:
        inner = 0.0
    return float(np.sqrt(inner))


def _validate_market_irr(
    bucket: QuarterBucket,
    findings: list[dict[str, Any]],
    source_has_breakdown: Optional[frozenset],
    eff_tol: float,
) -> None:
    """Market-risk decomposition (19_market) and interest-rate-risk IRR (36_irr).
    Both are cadence-aware: a disclosed parent with the breakdown missing is RED on
    even quarters (full form) but a legit SKIP on odd quarters (간이공시), with
    per-(company,quarter) documented exemptions. Split out of _validate_bucket
    2026-07-22; pinned by tests/test_kics_rules_golden.py."""
    # Rule 19_market: 시장위험액(item19) = sqrt(V'·M·V), V=[36,37,38,39,40].
    # 8_life와 동형이나 부분결측 허용(부동산/자산집중 미보유 정상): 없는 하위=0.
    # 핵심(2026-06-12): 부모 item19 공시인데 36-40이 *전부* 결측이면 SKIP이 아니라 RED.
    #   부모를 공시한 회사가 표준모형 시장위험 분해(36-40)를 안 낼 수 없다 → parser gap
    #   (하나손해 2025.4Q: 표가 <!-- image -->로 분절 / 삼성생명: "1.금리위험액"+충격시나리오방식 라벨변형).
    #   진짜 미공시 legit 케이스만 MARKET_BREAKDOWN_EXEMPT에 (회사,분기) 문서화 면제.
    mkt_items = list(range(36, 41))
    mkt_present = [bucket.get(i) for i in mkt_items if bucket.get(i) is not None]
    cq = (bucket.code, bucket.quarter)
    if bucket.get(19) is not None and mkt_present:
        v = np.array([bucket.get(i) or 0.0 for i in mkt_items], dtype=float)
        expected = _diversified_sqrt(v, MARKET_M)
        mkt_tol = max(eff_tol, 0.05 * abs(expected))
        findings.append(_check_numeric(bucket, "19_market", expected, bucket.get(19), mkt_tol))
    elif bucket.get(19) is None or cq in MARKET_BREAKDOWN_EXEMPT:
        findings.append(
            _finding(
                bucket, "19_market", status=STATUS_SKIP, expected=None,
                actual=bucket.get(19), diff=None,
                detail="item19 absent (nothing to check) or documented breakdown-exempt",
            )
        )
    elif (
        source_has_breakdown is not None
        and cq not in source_has_breakdown
        and not bucket.quarter.endswith(("2Q", "4Q"))
    ):
        # cadence-SKIP은 **홀수분기(1Q/3Q)만** — 간이공시라 세부표 원천부재(MD 키워드<3로 확인).
        # 짝수분기(2Q/4Q)는 반기/연간 full form이라 표가 반드시 있어야 함 → 결측은 아래 else에서 RED
        # (텍스트 스캔만으론 이미지/스캔표를 못 보므로, 짝수는 source 부재여도 숨기지 않음. 2026-06-13).
        findings.append(
            _finding(
                bucket, "19_market", status=STATUS_SKIP, expected=None,
                actual=bucket.get(19), diff=None,
                detail="item19 present but breakdown 36-40 absent from odd-quarter source (abbreviated 1Q/3Q form / cadence) — legit absent",
            )
        )
    else:
        # 짝수분기 full form 결측, 또는 홀수분기인데 원천에 표 있음(MD 키워드>=3), 또는 source 확인불가 -> 파서갭. RED.
        findings.append(
            _finding(
                bucket, "19_market", status=STATUS_RED, expected=None,
                actual=bucket.get(19), diff=None,
                detail="item19 present + breakdown 36-40 expected (even-qtr full form, or source has table) but missing in JSON — parser gap (image-split/label-variant/MD-truncation/OCR)",
            )
        )

    # Rule 36_irr: 금리위험액(item36) = sqrt(max(R상승,R하락)² + max(R평탄,R경사)²) + R평균회귀.
    # R = base(item41) − 시나리오 순자산가치; 평균회귀는 signed(no max).
    # 핵심(2026-06-13, 19_market과 동형 SKIP맹점 폐쇄): 41-46(시나리오 순자산가치 6종)은
    #   **짝수분기(2Q/4Q) 서식에만** 존재. 홀수분기(1Q/3Q)는 서식 원천부재라 SKIP 정당.
    #   짝수분기인데 item36 공시·41-46 결측/불완전이면 SKIP 아니라 RED(parser gap). 진짜 부재만
    #   IRR_SCENARIO_EXEMPT 문서화 면제. 검증 empirics: 41-46은 전 분기 짝수에만 적재됨.
    irr_items = [36, 41, 42, 43, 44, 45, 46]
    is_even_q = bucket.quarter.endswith(("2Q", "4Q"))
    irr_vals = {i: bucket.get(i) for i in irr_items}
    # documented exception (owner 2026-08-21) — **잔차 박제**. 통째 skip 이 아니라
    # "이 잔차인 동안만 차단하지 않는다". 드리프트·결측은 둘 다 RED. 상세는
    # IRR_DERIVE_ISSUER_INCONSISTENT 주석 참조.
    pin_verdict, pinned_resid, actual_resid = irr_pin_verdict(
        bucket.code, bucket.quarter, "적용전", irr_vals)
    if (bucket.code, bucket.quarter) in INTERNAL_MODEL_36IRR_EXEMPT:
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_SKIP, expected=None,
                actual=bucket.get(36), diff=None,
                detail="internal-model insurer: 표준 derive식 불適用 (회사 시나리오별 금리위험액 직접공시) — owner-approved exempt (2026-06-14)",
            )
        )
    elif pin_verdict == "MATCH":
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_SKIP,
                expected=irr_derive_expected(irr_vals), actual=bucket.get(36),
                diff=actual_resid,
                detail=f"documented exception (owner 2026-08-21, 잔차 박제): 적용전 잔차 "
                       f"{actual_resid:.4f} == 박제 {pinned_resid:.4f} (tol {IRR_PIN_TOL}). "
                       "item36 은 19_market 축에서 닫히고 41-46 은 원문 그대로 — 재현식이 이 "
                       "회사에 안 맞는 것이며 원인 미규명(UNEXPLAINED). 잔차가 움직이면 RED 로 복귀",
            )
        )
    elif pin_verdict == "DRIFT":
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_RED,
                expected=irr_derive_expected(irr_vals), actual=bucket.get(36),
                diff=actual_resid,
                detail=f"IRR_EXEMPTION_RESIDUAL_DRIFT — 박제 {pinned_resid:.4f} → 실측 "
                       f"{actual_resid:.4f} (Δ{actual_resid - pinned_resid:+.4f}, tol {IRR_PIN_TOL}). "
                       "owner 판단의 전제(item36·41-46 모두 원문 그대로)가 바뀌었다 — 면제 무효",
            )
        )
    elif pin_verdict == "INPUT_MISSING":
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_RED, expected=None,
                actual=bucket.get(36), diff=None,
                detail=f"IRR_EXEMPTION_INPUT_MISSING — 면제 등재분인데 item36/41-46 [적용전]이 "
                       f"결측이라 박제잔차 {pinned_resid:.4f} 를 확인할 수 없다. 결측은 SKIP 이 아니라 RED",
            )
        )
    elif all(bucket.get(i) is not None for i in irr_items):
        expected = irr_derive_expected(irr_vals)
        irr_tol = max(eff_tol, 0.05 * abs(expected))
        findings.append(_check_numeric(bucket, "36_irr", expected, bucket.get(36), irr_tol))
    elif (bucket.get(36) is not None and is_even_q
          and (bucket.code, bucket.quarter) not in IRR_SCENARIO_EXEMPT):
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_RED, expected=None,
                actual=bucket.get(36), diff=None,
                detail="item36(금리위험액) present in even quarter but scenario table 41-46 missing/incomplete — parser gap, not legit (scenario table is in 2Q/4Q form)",
            )
        )
    else:
        findings.append(
            _finding(
                bucket, "36_irr", status=STATUS_SKIP, expected=None,
                actual=bucket.get(36), diff=None,
                detail="item36 absent, or odd quarter (scenario table not in 1Q/3Q form), or documented scenario-exempt",
            )
        )


def _validate_transition_capital(
    bucket: QuarterBucket,
    findings: list[dict[str, Any]],
    eff_tol: float,
) -> None:
    """경과조치 monotonicity: 기본자본 적용후>=적용전 (rule 9, grandfathered 신종자본
    증권) and 지급여력기준금액 적용전>=적용후 (rule 10, risk-charge phase-in). Split out
    of _validate_bucket 2026-07-22; pinned by tests/test_kics_rules_golden.py."""
    # Rule 9: 기본자본 (item2) 적용후 >= 적용전.
    # Transitional grandfather: pre-2022 신종자본증권 fully recognized in basic capital
    # under 적용 후, but limit-deducted under 적용 전. So post should be >= pre (within tol).
    item2_pre = bucket.get(2)
    item2_post = bucket.get(2, post=True)
    if item2_pre is not None and item2_post is not None and item2_post != item2_pre:
        diff = item2_post - item2_pre  # should be >= -tol
        # 대형사 grandfather 미세감소 허용: 절대 2.0은 수조원대 기본자본에 과도하게 엄격.
        # 경과조치 2차효과(보완자본 한도 재계산 등)로 극소량 감소는 정상(한화손해 2024.2Q raw
        # 확인: 기본자본 2,638,159→2,637,797 백만 = −0.015%). rule 8_life 동적허용오차와 동일 발상.
        gf_tol = max(eff_tol, 0.0005 * abs(item2_pre))
        if diff >= -gf_tol:
            status = STATUS_GREEN
        else:
            status = STATUS_RED
        findings.append(_finding(
            bucket, "9",
            status=status,
            expected=item2_pre, actual=item2_post, diff=diff,
            detail="item2(기본자본) 적용후 >= 적용전 expected (transitional grandfather, dynamic tol)",
        ))
    else:
        findings.append(_finding(
            bucket, "9",
            status=STATUS_SKIP, expected=None, actual=item2_post, diff=None,
            detail="no post-transition item2 (or equal to pre)",
        ))

    # Rule 10: 지급여력기준금액 (item14) 적용전 >= 적용후.
    # Transitional risk-ramp: some risk charges phase in gradually, so SCR_post
    # (currently effective) typically <= SCR_pre (strict end-state). Pre >= post (within tol).
    item14_pre = bucket.get(14)
    item14_post = bucket.get(14, post=True)
    if item14_pre is not None and item14_post is not None and item14_post != item14_pre:
        diff = item14_pre - item14_post  # should be >= -tol
        if diff >= -eff_tol:
            status = STATUS_GREEN
        else:
            status = STATUS_RED
        findings.append(_finding(
            bucket, "10",
            status=status,
            expected=item14_post, actual=item14_pre, diff=diff,
            detail="item14(SCR) 적용전 >= 적용후 expected (transitional risk ramp)",
        ))
    else:
        findings.append(_finding(
            bucket, "10",
            status=STATUS_SKIP, expected=None, actual=item14_pre, diff=None,
            detail="no post-transition item14 (or equal to pre)",
        ))


def _validate_transition_basic(
    bucket: QuarterBucket,
    findings: list[dict[str, Any]],
    eff_tol: float,
) -> None:
    """경과조치 적용후 기본자본비율 (8_post, item2후/item14후) and 생명장기 R7 sub-risk
    diversification (8_life, item17 = sqrt(S·R7·S)). Both use a dynamic tolerance for
    sub-scale denominators / accumulated sqrt rounding. Split out of _validate_bucket
    2026-07-22; pinned by tests/test_kics_rules_golden.py."""
    # Rule 8_post: post-transition basic capital ratio.
    # expected = item2_post / item14_post * 100  (use POST values for both
    # numerator and denominator). bucket.get(..., post=True) falls back to
    # pre value when post is missing, which is correct: if pre==post then
    # ratio is unchanged. SKIP only when neither item2 nor item14 has any
    # post-transition data AND item28 has no post value either (no
    # transitional reported at all).
    post2 = bucket.get(2, post=True)
    post14 = bucket.get(14, post=True)
    has_any_post = (
        2 in bucket.values_post
        or 14 in bucket.values_post
        or 28 in bucket.values_post
    )
    # 분자(item2)와 분모(item14)가 반드시 같은 기준(둘 다 genuine post, 또는 둘 다
    # pre 폴백)이어야 한다. 한쪽만 post이면(예: item14후는 채워졌는데 item2후는 결측 →
    # pre로 폴백) expected = pre2/post14 라는 무의미값이 나와 spurious RED가 뜬다
    # (흥국생명 2024.4Q·에이비엘 2025.3Q·푸본 2023.1Q, 2026-07-07 validation 적발).
    # 기준이 어긋나면 SKIP — 진짜 결측은 transition-after-capture MISSING 체크가 별도로 잡음.
    same_basis = (2 in bucket.values_post) == (14 in bucket.values_post)
    if has_any_post and same_basis and post2 is not None and post14 is not None and post14 != 0:
        expected = post2 / post14 * 100.0
        actual = bucket.get(28, post=True)
        if actual is None:
            actual = bucket.get(28)
        # rule 8(적용전)과 동일한 dynamic tol: micro사(작은 item14후)는 억원-coarse 반올림으로
        # 산출비율이 공시비율과 어긋남(카카오 2023.4Q item14후=20 → 974/20=4870 vs 공시4777).
        # 8_post만 eff_tol 쓰던 불일치 교정(2026-07-12).
        ratio_tol = max(eff_tol, abs(expected) * 0.5 / abs(post14) + 50.0 / abs(post14))
        findings.append(_check_numeric(bucket, "8_post", expected, actual, ratio_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "8_post",
                status=STATUS_SKIP,
                expected=None,
                actual=bucket.get(28, post=True),
                diff=None,
                detail="no post data or mixed pre/post basis for item2/14 (skip; MISSING caught by transition check)",
            )
        )

    sub_items = list(range(29, 36))
    if bucket.get(17) is not None and all(bucket.get(i) is not None for i in sub_items):
        s = np.array([bucket.get(i) for i in sub_items], dtype=float)
        expected = _diversified_sqrt(s, R7)
        # 8_life only: dynamic tolerance = max(eff_tol, 5% of expected).
        # Rationale: R7 diversified sqrt accumulates rounding from 7 sub-items,
        # so absolute 2.0 tol is too tight when expected is large (hundreds-thousands).
        life_tol = max(eff_tol, 0.05 * abs(expected))
        findings.append(_check_numeric(bucket, "8_life", expected, bucket.get(17), life_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "8_life",
                status=STATUS_SKIP,
                expected=None,
                actual=bucket.get(17),
                diff=None,
                detail="missing item17 or any of items 29-35",
            )
        )


def _validate_bucket(
    bucket: QuarterBucket,
    findings: list[dict[str, Any]],
    tolerance: float,
    source_has_breakdown: Optional[frozenset],
) -> None:
    """Apply all 14 rules to one (company, quarter) bucket, appending to `findings`.

    Split verbatim out of run_validation's per-bucket loop 2026-07-22; behaviour
    pinned by tests/test_kics_rules_golden.py."""
    eff_tol = (
        IMAGE_OCR_TOLERANCE
        if bucket.code in IMAGE_OCR_COMPANIES
        else tolerance
    )
    if all(bucket.get(i) is not None for i in (1, 2, 3)):
        expected = (bucket.get(2) or 0) + (bucket.get(3) or 0)
        findings.append(_check_numeric(bucket, "1", expected, bucket.get(1), eff_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "1",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(1),
                diff=None,
                detail="missing items 1-3",
            )
        )

    if bucket.get(4) is not None:
        expected = _sum_optional(bucket, range(5, 12))
        findings.append(_check_numeric(bucket, "2", expected, bucket.get(4), eff_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "2",
                status=STATUS_RED,
                expected=None,
                actual=None,
                diff=None,
                detail="missing item4",
            )
        )

    findings.append(
        _finding(
            bucket,
            "3",
            status=STATUS_SKIP,
            expected=None,
            actual=bucket.get(1),
            diff=None,
            detail="deferred: item4-item12+item13 bridge unreliable vs disclosure; rule 1 is authoritative for item1",
        )
    )

    if all(bucket.get(i) is not None for i in (15, 17, 18, 19, 20, 21)):
        v = np.array(
            [bucket.get(17), bucket.get(18), bucket.get(19), bucket.get(20)],
            dtype=float,
        )
        expected = _diversified_sqrt(v, R4) + float(bucket.get(21))
        findings.append(_check_numeric(bucket, "4", expected, bucket.get(15), eff_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "4",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(15),
                diff=None,
                detail="missing items for R4 (15,17-21)",
            )
        )

    if all(bucket.get(i) is not None for i in (14, 15, 22)):
        item23 = bucket.get(23)
        if item23 is None:
            item23 = 0.0
        expected = (bucket.get(15) or 0) - (bucket.get(22) or 0) + item23
        findings.append(_check_numeric(bucket, "5", expected, bucket.get(14), eff_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "5",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(14),
                diff=None,
                detail="missing items 14,15,22",
            )
        )

    if all(bucket.get(i) is not None for i in (15, 16, 17, 18, 19, 20, 21)):
        expected = (
            (bucket.get(17) or 0)
            + (bucket.get(18) or 0)
            + (bucket.get(19) or 0)
            + (bucket.get(20) or 0)
            + (bucket.get(21) or 0)
            - (bucket.get(15) or 0)
        )
        findings.append(_check_numeric(bucket, "6", expected, bucket.get(16), eff_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "6",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(16),
                diff=None,
                detail="missing items for rule 6",
            )
        )

    if all(bucket.get(i) is not None for i in (1, 14, 27)) and bucket.get(14) != 0:
        expected = (bucket.get(1) or 0) / (bucket.get(14) or 1) * 100.0
        # ratio rule: integer-rounding of a tiny denominator (item14) swings the
        # recomputed ratio hugely (카카오페이손해 2023.4Q item14=20억 → ±~120%p),
        # while the disclosed item27 is exact. dynamic tol mirrors 8_life: propagate
        # ±0.5 rounding on denom (expected×0.5/|denom|) + num (50/|denom|). Negligible
        # for normal denominators; only loosens for sub-scale ones.
        d14 = abs(bucket.get(14))
        ratio_tol = max(eff_tol, abs(expected) * 0.5 / d14 + 50.0 / d14)
        findings.append(_check_numeric(bucket, "7", expected, bucket.get(27), ratio_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "7",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(27),
                diff=None,
                detail="missing items 1,14,27 or item14=0",
            )
        )

    if all(bucket.get(i) is not None for i in (2, 14, 28)) and bucket.get(14) != 0:
        expected = (bucket.get(2) or 0) / (bucket.get(14) or 1) * 100.0
        # same sub-scale denominator rounding as rule 7 (see note above).
        d14 = abs(bucket.get(14))
        ratio_tol = max(eff_tol, abs(expected) * 0.5 / d14 + 50.0 / d14)
        findings.append(_check_numeric(bucket, "8", expected, bucket.get(28), ratio_tol))
    else:
        findings.append(
            _finding(
                bucket,
                "8",
                status=STATUS_RED,
                expected=None,
                actual=bucket.get(28),
                diff=None,
                detail="missing items 2,14,28 or item14=0",
            )
        )

    _validate_transition_basic(bucket, findings, eff_tol)

    _validate_market_irr(bucket, findings, source_has_breakdown, eff_tol)

    _validate_transition_capital(bucket, findings, eff_tol)


def run_validation(
    records: Iterable[Mapping[str, Any]], *, tolerance: float = 2.0,
    source_has_breakdown: Optional[frozenset] = None,
) -> dict[str, Any]:
    buckets = _group_records(records)
    findings: list[dict[str, Any]] = []

    for bucket in buckets:
        _validate_bucket(bucket, findings, tolerance, source_has_breakdown)

    summary_status: dict[str, int] = {
        STATUS_YELLOW: 0,
        STATUS_GREEN: 0,
        STATUS_SKIP: 0,
        STATUS_ERROR: 0,
    }
    by_rule: dict[str, dict[str, int]] = {}
    for f in findings:
        st = f.get("status", STATUS_ERROR)
        summary_status[st] = summary_status.get(st, 0) + 1
        rid = str(f.get("rule"))
        by_rule.setdefault(rid, {})
        by_rule[rid][st] = by_rule[rid].get(st, 0) + 1

    return {
        "summary": {
            "buckets": len(buckets),
            "findings": len(findings),
            "by_status": summary_status,
            "by_rule": by_rule,
            "tolerance": tolerance,
        },
        "findings": findings,
    }
