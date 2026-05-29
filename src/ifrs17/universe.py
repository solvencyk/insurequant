"""Operational universe and slice rules for IFRS17 analysis.

User decisions (2026-05-24 Open Q1-Q9):
  Q1-Q5:
  - Skip 12 non-listed insurers (no OpenDART pblntf_ty=A).
  - Skip AIG (no corp_master match).
  - Exclude Seoul Guarantee (no CSM / PAA-only).
  - Effective CSM universe: 23 listed insurers with annual-report data.
  - Life insurers: slice = whole-company total.
  - Property insurers: slice = long-term line only.
  Q6-Q9:
  - CSM: total_csm representative; preserve 3 measurement-model cols when disclosed.
  - Reinsurance: long-term ceded only (no separate general/auto table_ids).
  - Sensitivity (B5): K-ICS quarterly primary; DART notes secondary/future.
  - B3 liability_rollforward unified with section 8 multi-index (same table).
"""

from __future__ import annotations

NON_LISTED_SKIP: frozenset[str] = frozenset({
    "IBK\uC5F0\uAE08\uBCF4\uD5D8",
    "\uAD50\uBCF4\uB77C\uC774\uD504\uD50C\uB7AB",
    "\uB77C\uC774\uB098\uC0DD\uBA85",
    "\uBA54\uD2B8\uB77C\uC774\uD504\uC0DD\uBA85",
    "\uBE44\uC5D4\uD53C\uD30C\uB9AC\uBC14\uCE74\uB514\uD504",
    "\uC2E0\uD55C\uC774\uC988\uC190\uD574",
    "\uC544\uC774\uC5FC\uB77C\uC774\uD504",
    "\uC545\uC0AC\uC190\uD574",
    "\uCC98\uBE0C\uB77C\uC774\uD504",
    "\uCE74\uCE74\uC624\uD398\uC774\uC190\uD574",
    "\uD558\uB098\uC0DD\uBA85",
    "\uD558\uB098\uC190\uD574",
})

EXCLUDED_SKIP: frozenset[str] = frozenset({
    "AIG\uC190\uD574\uBCF4\uD5D8",
    "\uC11C\uC6B8\uBCF4\uC99D\uBCF4\uD5D8",
})

# Foreign-affiliate life insurers (\uD55C\uAD6D\uBC95\uC778 \uC8FC\uC2DD\uD68C\uC0AC). They file no pblntf_ty=A
# periodic disclosure, but the \uC678\uBD80\uAC10\uC0AC\uBC95 audit report (pblntf_ty="F" \uAC10\uC0AC\uBCF4\uACE0\uC11C)
# carries the same IFRS17 \uBCF4\uD5D8\uACC4\uC57D \uC8FC\uC11D, including the CSM amort schedule.
# Annual only. Names use the K-ICS \uC6D0\uC218\uC0AC\uBA85 full form; \uC5D0\uC774\uC544\uC774\uC5D0\uC774\uC0DD\uBA85\uBCF4\uD5D8 is NOT
# in kics_disclosure.json (no public K-ICS row) and is carried here only.
# (Feasibility verified 2026-05-29: existing csm_extractor parses all 5.)
AUDIT_REPORT_ANNUAL: frozenset[str] = frozenset({
    "\uB77C\uC774\uB098\uC0DD\uBA85\uBCF4\uD5D8",
    "\uBA54\uD2B8\uB77C\uC774\uD504\uC0DD\uBA85\uBCF4\uD5D8",
    "\uC5D0\uC774\uC544\uC774\uC5D0\uC774\uC0DD\uBA85\uBCF4\uD5D8",
    "\uD558\uB098\uC0DD\uBA85\uBCF4\uD5D8",
    "\uCC98\uBE0C\uB77C\uC774\uD504\uC0DD\uBA85\uBCF4\uD5D8",
})

ALL_EXCLUDED: frozenset[str] = NON_LISTED_SKIP | EXCLUDED_SKIP
LISTED_UNIVERSE_SIZE = 37 - len(NON_LISTED_SKIP)
OPERATIONAL_CSM_COUNT = 23


def is_audit_report_annual(name: str) -> bool:
    return name in AUDIT_REPORT_ANNUAL

_SLICE_LONGTERM = (
    "\uC7A5\uAE30",
    "\uC0DD\uBA85\uC7A5\uAE30",
    "\uC7A5\uAE30\uC190\uD574",
    "\uC7A5\uAE30\uC190\uD574\uBCF4\uD5D8",
    "\uC7A5\uAE30\uC6D0\uC218",
)

_SHORT_TERM_MARKERS = (
    "일반",
    "자동차",
    "보험료배분접근법을 적용하는",
    "보험료배분접근법을 적용하는",
)

# Non-PAA / GMM context proxies long-term slice for property insurers when
# disclosures omit an explicit \uC7A5\uAE30 column (KB Sonhae, Hanwha Sonhae).
_NON_PAA_GMM_MARKERS = (
    "보험료배분접근법을 적용하지 않",
    "보험료배분접근법 미적용",
    "보험료배분접근법을 적용한 보험계약 이외",
    "일반모형",
    "구성요소별",
)


def is_excluded(kics_name: str) -> bool:
    return kics_name in ALL_EXCLUDED


def is_life_insurer(name: str) -> bool:
    markers = ("\uC0DD\uBA85", "\uC5F0\uAE08", "\uB77C\uC774\uD504", "Life")
    return any(m in name for m in markers)


def is_reinsurer(name: str) -> bool:
    markers = ("\uC7AC\uBCF4\uD5D8", "Reinsurance", "Re ")
    return any(m in name for m in markers)


def expected_slice_policy(name: str) -> str:
    if is_life_insurer(name):
        return "whole_company_life"
    return "long_term"


def has_short_term_markers(text: str) -> bool:
    return any(m in text for m in _SHORT_TERM_MARKERS)


def is_non_paa_gmm_context(text: str) -> bool:
    """True when caption/footnote context indicates GMM (non-PAA) blocks."""
    if has_short_term_markers(text):
        return False
    if any(m in text for m in _NON_PAA_GMM_MARKERS):
        return True
    if "\uC77C\uBC18\uBAA8\uD615" in text and "\uC218\uC7AC" in text:
        return True
    return False


def table_has_long_term_label(texts: list[str]) -> bool:
    joined = " ".join(texts)
    return any(k in joined for k in _SLICE_LONGTERM)
