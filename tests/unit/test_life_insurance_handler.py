"""Unit tests for the Life Insurance Association handler — pure-logic only.

Selenium / Chrome are not exercised here; we test the filename → insurer
resolver and the URL/period helpers because those are the parts most likely
to silently mis-route a PDF into the wrong company directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from solvency.downloader.handlers.life_insurance_association import (  # noqa: E402
    _load_registry,
    _match_insurer,
    _normalise,
    _period_from,
    _with_year,
    _year_from_fy,
    _REGISTRY_FILE,
)


@pytest.fixture(scope="module")
def insurers() -> list[dict]:
    return _load_registry(_REGISTRY_FILE)


# --- _normalise ---------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("한화생명 2025 4Q.pdf", "한화생명20254qpdf"),
        ("(주) 삼성생명_25_4Q", "주삼성생명254q"),
        ("ABL-생명/공시.pdf", "abl생명공시pdf"),
        ("BNP파리바 카디프 (주).pdf", "bnp파리바카디프주pdf"),
    ],
)
def test_normalise_strips_whitespace_punctuation(raw, expected):
    assert _normalise(raw) == expected


# --- _match_insurer -----------------------------------------------------------

@pytest.mark.parametrize(
    "filename,expected_code",
    [
        ("한화생명 2025년 4분기 경영공시.pdf", "KR0068"),
        ("삼성생명_25_4Q.pdf", "KR0069"),
        ("ABL생명_4Q.pdf", "KR0070"),
        ("에이비엘생명보험_경영공시.pdf", "KR0070"),
        ("KDB생명보험_4Q.pdf", "KR0072"),
        ("케이디비생명_25_4Q.pdf", "KR0072"),
        ("교보생명보험_25Q4.pdf", "KR0073"),
        ("BNP파리바카디프생명.pdf", "KR0075"),
        ("카디프생명.pdf", "KR0075"),
        ("AIA생명_경영공시.pdf", "KR0080"),
        ("DB생명보험_25_4Q.pdf", "KR0082"),
        ("푸본현대생명보험.pdf", "KR0083"),
        ("신한라이프생명_25Q4.pdf", "KR0094"),
        ("KB라이프생명.pdf", "KR0099"),
        ("처브라이프생명보험.pdf", "KR0100"),
        ("NH농협생명_25Q4.pdf", "KR0104"),
        ("교보라이프플래닛_25Q4.pdf", "KR1010"),
    ],
)
def test_match_insurer_resolves_known_filenames(filename, expected_code, insurers):
    matched = _match_insurer(filename, insurers)
    assert matched is not None, f"no match for {filename}"
    assert matched["code"] == expected_code


def test_match_insurer_returns_none_for_non_life_pdf(insurers):
    assert _match_insurer("KR0008_삼성화재해상보험.pdf", insurers) is None


def test_match_insurer_disambiguates_kyobo_vs_lifeplanet(insurers):
    """교보생명 vs 교보라이프플래닛 — alias ordering must keep them separate."""
    assert _match_insurer("교보생명_25Q4.pdf", insurers)["code"] == "KR0073"
    assert _match_insurer("교보라이프플래닛_25Q4.pdf", insurers)["code"] == "KR1010"


def test_match_insurer_disambiguates_shinhan_vs_lifeplanet(insurers):
    """신한라이프 wins over a hypothetical 신한 prefix (ordering by length)."""
    assert _match_insurer("신한라이프생명.pdf", insurers)["code"] == "KR0094"


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


@pytest.mark.parametrize(
    "fy,expected",
    [("FY2025", "2025"), ("FY25", "2025"), ("2024", "2024")],
)
def test_year_from_fy(fy, expected):
    assert _year_from_fy(fy) == expected


# --- _with_year ---------------------------------------------------------------

def test_with_year_replaces_existing_param():
    url = "https://pub.insure.or.kr/list.do?search_stdYear=2024"
    assert _with_year(url, "2025") == "https://pub.insure.or.kr/list.do?search_stdYear=2025"


def test_with_year_appends_when_missing_param():
    url = "https://pub.insure.or.kr/list.do"
    assert _with_year(url, "2025") == "https://pub.insure.or.kr/list.do?search_stdYear=2025"


def test_with_year_appends_with_amp_when_other_params_present():
    url = "https://pub.insure.or.kr/list.do?foo=bar"
    assert _with_year(url, "2025") == "https://pub.insure.or.kr/list.do?foo=bar&search_stdYear=2025"
