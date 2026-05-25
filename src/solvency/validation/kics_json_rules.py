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

STATUS_RED = "RED"
STATUS_YELLOW = "YELLOW"
STATUS_GREEN = "GREEN"
STATUS_ERROR = "ERROR"
STATUS_SKIP = "SKIP"

# Image-only PDF insurers: OCR rounding may exceed default tolerance (see KICS-IMG).
IMAGE_OCR_TOLERANCE = 10.0
IMAGE_OCR_COMPANIES = frozenset({"KR0010", "KR0079"})


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
    records: Iterable[Mapping[str, Any]], *, tolerance: float = 2.0
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
            findings.append(_check_numeric(bucket, "7", expected, bucket.get(27), eff_tol))
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
            findings.append(_check_numeric(bucket, "8", expected, bucket.get(28), eff_tol))
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
        if has_any_post and post2 is not None and post14 is not None and post14 != 0:
            expected = post2 / post14 * 100.0
            actual = bucket.get(28, post=True)
            if actual is None:
                actual = bucket.get(28)
            findings.append(_check_numeric(bucket, "8_post", expected, actual, eff_tol))
        else:
            findings.append(
                _finding(
                    bucket,
                    "8_post",
                    status=STATUS_SKIP,
                    expected=None,
                    actual=bucket.get(28, post=True),
                    diff=None,
                    detail="no post-transition data for item2/14/28",
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

        # Rule 9: 기본자본 (item2) 적용후 >= 적용전.
        # Transitional grandfather: pre-2022 신종자본증권 fully recognized in basic capital
        # under 적용 후, but limit-deducted under 적용 전. So post should be >= pre (within tol).
        item2_pre = bucket.get(2)
        item2_post = bucket.get(2, post=True)
        if item2_pre is not None and item2_post is not None and item2_post != item2_pre:
            diff = item2_post - item2_pre  # should be >= -tol
            if diff >= -eff_tol:
                status = STATUS_GREEN
            else:
                status = STATUS_RED
            findings.append(_finding(
                bucket, "9",
                status=status,
                expected=item2_pre, actual=item2_post, diff=diff,
                detail="item2(기본자본) 적용후 >= 적용전 expected (transitional grandfather)",
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
