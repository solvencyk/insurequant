"""Unit tests for the Non-life Insurance Association handler — pure-logic only.

Selenium / Chrome are not exercised here; we test the company name → insurer
resolver and helper functions.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from solvency.downloader.handlers.nonlife_insurance_association import (  # noqa: E402
    _load_registry,
    _match_insurer,
    _normalise,
    _period_from,
    _REGISTRY_FILE,
)


@pytest.fixture(scope="module")
def insurers() -> list[dict]:
    return _load_registry(_REGISTRY_FILE)


# --- _normalise ---------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("삼성화재 2025년 4분기", "삼성화재2025년4분기"),
        ("현대해상_25_Q4.pdf", "현대해상25q4pdf"),
        ("한화손보-경영공시", "한화손보경영공시"),
        ("KB손해보험(주)", "kb손해보험주"),
    ],
)
def test_normalise_strips_whitespace_punctuation(raw, expected):
    assert _normalise(raw) == expected


# --- _match_insurer -----------------------------------------------------------


@pytest.mark.parametrize(
    "company_name,expected_code",
    [
        ("메리츠화재", "KR0001"),
        ("한화손보", "KR0002"),
        ("롯데손보", "KR0003"),
        ("흥국화재", "KR0005"),
        ("삼성화재", "KR0008"),
        ("현대해상", "KR0009"),
        ("KB손보", "KR0010"),
        ("DB손보", "KR0011"),
        ("농협손보", "KR0032"),
        ("AXA손보", "KR0049"),
        ("하나손보", "KR0050"),
        ("신한EZ손해보험", "KR0051"),
        ("서울보증", "KR0150"),
        ("코리안리", "KR1000"),
        ("캐롯손해보험", "KR1059"),
        ("카카오페이손해보험", "KR1098"),
    ],
)
def test_match_insurer_resolves_known_names(company_name, expected_code, insurers):
    matched = _match_insurer(company_name, insurers)
    assert matched is not None, f"no match for {company_name}"
    assert matched["code"] == expected_code


def test_match_insurer_returns_none_for_unknown(insurers):
    assert _match_insurer("비보험회사", insurers) is None


# --- _period_from / _year_from_fy --------------------------------------------


@pytest.mark.parametrize(
    "fiscal_year,quarter,expected",
    [
        ("FY2025", "Q4", "FY2025_Q4"),
        ("FY25", "Q1", "FY2025_Q1"),
        ("2024", "Q3", "FY2024_Q3"),
    ],
)
def test_period_from(fiscal_year, quarter, expected):
    assert _period_from(fiscal_year, quarter) == expected
