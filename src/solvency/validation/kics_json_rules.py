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

# 36_irr 내부모형 면제: 내부모형사 — 41-46 순자산가치는 정확 추출되나 표준 derive식(R=충격전−시나리오)이
# 공시 금리위험액과 불일치. 회사가 시나리오별 금리위험액을 **직접 공시**하고 그 값을 같은 식에 넣으면
# 공시총액과 정확 일치(KR0094 2025.4Q=578,999 검증) = 내부모형. owner 승인(2026-06-14, "한화 선례 동형").
# 41-46이 present라 위 if 분기로 들어가 _check_numeric RED가 나므로 블록 최상단에서 SKIP 단락.
INTERNAL_MODEL_36IRR_EXEMPT: frozenset[tuple[str, str]] = frozenset({
    ("KR0073", "2025.2Q"),
    ("KR0094", "2024.2Q"), ("KR0094", "2024.4Q"),
    ("KR0094", "2025.2Q"), ("KR0094", "2025.4Q"),
})


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


def run_validation(
    records: Iterable[Mapping[str, Any]], *, tolerance: float = 2.0,
    source_has_breakdown: Optional[frozenset] = None,
) -> dict[str, Any]:
    buckets = _group_records(records)
    findings: list[dict[str, Any]] = []

    for bucket in buckets:
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
        if (bucket.code, bucket.quarter) in INTERNAL_MODEL_36IRR_EXEMPT:
            findings.append(
                _finding(
                    bucket, "36_irr", status=STATUS_SKIP, expected=None,
                    actual=bucket.get(36), diff=None,
                    detail="internal-model insurer: 표준 derive식 불適用 (회사 시나리오별 금리위험액 직접공시) — owner-approved exempt (2026-06-14)",
                )
            )
        elif all(bucket.get(i) is not None for i in irr_items):
            base = float(bucket.get(41))
            r_up = max(base - float(bucket.get(43)), 0.0)
            r_dn = max(base - float(bucket.get(44)), 0.0)
            r_flat = max(base - float(bucket.get(45)), 0.0)
            r_steep = max(base - float(bucket.get(46)), 0.0)
            r_mr = base - float(bucket.get(42))  # 평균회귀: signed
            expected = float(np.sqrt(max(r_up, r_dn) ** 2 + max(r_flat, r_steep) ** 2)) + r_mr
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
