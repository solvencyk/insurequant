# -*- coding: utf-8 -*-
"""Golden no-regression test for the K-ICS parsing-variant registry
(REFACTOR-3 slice 1, 2026-06-13).

Locks that moving the parser's section-heading recognisers, OCR label fixes, and
audit-label aliases out of kics_disclosure_parser.py into company_handlers.py left
the compiled regexes / behaviour BYTE-IDENTICAL to the pre-refactor constants.
The end-to-end proof is tests/unit/test_kics_disclosure_parser.py (real MD); this
file locks the registry contract directly so a careless config edit is caught."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from solvency.parser import company_handlers as ch  # noqa: E402
from solvency.parser import kics_disclosure_parser as P  # noqa: E402

# Sources copied verbatim from the pre-refactor parser core (the values the
# refactor must not change). Korean literals compile to the same pattern string
# regardless of source representation.
_ORIG_START = (
    (r"#{1,3}\s*\[?\s*경과조치\s*적용\s*전.{0,40}지급여력비율\s*세부", re.I),
    (r"#{1,3}\s*\[?\s*경과조치\s*적용\s*전.{0,40}세부", re.I),
    (r"#{1,3}\s*\[?\s*경과조치\s*적용\s*전.{0,30}\]?", re.I),
    (r"#{1,3}\s*4-2-2\.?\s*지급여력비율[^\n]*세부", re.I),
    (r"#{1,3}\s*[^\n]*\[\s*경과조치\s*적용\s*전\s*지급여력비율\s*세부\s*\]", re.I),
    (r"\[\s*경과조치\s*적용\s*전[^\]]*지급여력비율\s*세부\s*\]", re.I),
    (r"#{1,3}\s*[※\*﻿]?\s*경과조치\s*적용\s*전[^\n]*지급여력비율\s*세부", re.I),
    (r"^[\-\*]\s*[※\*﻿]?\s*경과조치\s*적용\s*전[^\n]*지급여력비율\s*세부", re.I | re.M),
    (r"^[※\*﻿]?\s*경과조치\s*적용\s*전[^\n]*지급여력비율\s*세부", re.I | re.M),
    (r"#{1,3}\s*\[?\s*건전성감독기준\s*요약\s*재무상태표\s*\]?", re.I),
)
_ORIG_END = (
    (r"#{1,3}\s*\[?지급여력비율의\s*경과조치", re.I),
    (r"#{1,3}\s*\(?1\)?\s*공통적용\s*경과조치", re.I),
)


def test_section_start_patterns_byte_identical():
    pats = ch.build_section_start_patterns()
    assert len(pats) == 10
    for i, ((src, flags), p) in enumerate(zip(_ORIG_START, pats)):
        assert p.pattern == src, f"start[{i}] pattern changed"
        assert p.flags == re.compile(src, flags).flags, f"start[{i}] flags changed"


def test_section_end_patterns_byte_identical():
    pats = ch.build_section_end_patterns()
    assert len(pats) == 2
    for i, ((src, flags), p) in enumerate(zip(_ORIG_END, pats)):
        assert p.pattern == src, f"end[{i}] pattern changed"
        assert p.flags == re.compile(src, flags).flags, f"end[{i}] flags changed"


def test_parser_consumes_registry_patterns():
    # the parser's module-level tuples must be the ones built from the registry
    assert P.SECTION_START_PATTERNS == ch.build_section_start_patterns()
    assert P.SECTION_END_PATTERNS == ch.build_section_end_patterns()


def test_label_fixes_byte_identical():
    def orig_strip(s):
        for c in ("·", "ㆍ", "∙", "•"):
            s = s.replace(c, "")
        s = s.replace("보헨위", "보험위")
        s = s.replace("장기손액보헨", "장기손해보험")
        s = s.replace("장기손액보험", "장기손해보험")
        return s

    fixtures = [
        "보헨위험액",
        "장기손액보헨위험액",
        "장기손액보험위험액",
        "1·ㆍ∙•가",
        "일반손해보험위험액",
        "",
    ]
    for t in fixtures:
        assert ch.apply_label_fixes(t) == orig_strip(t), f"label-fix changed on {t!r}"
        # parser delegates to the registry
        assert P._strip_label_punct(t) == orig_strip(t)


def test_audit_label_aliases_byte_identical():
    expected = {
        "Ⅰ.순자산": "Ⅰ. 건전성감독기준 재무상태표 상의 순자산",
        "Ⅷ. 지급여력금액": "가. 지급여력금액",
        "Ⅴ.기본자본": "기본자본",
        "Ⅵ.보완자본": "보완자본",
        "(분산효과)": "- 분산효과 : (1+2+3+4+5) - Ⅰ",
        "Ⅴ. 지급여력기준금액": "나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)",
        "6. 조정준비금": "7. 조정준비금",
        "6.조정준비금": "7. 조정준비금",
        "건전성감독기준 재무상태표 상의 Ⅰ. 순자산": "Ⅰ. 건전성감독기준 재무상태표 상의 순자산",
    }
    assert ch.AUDIT_LABEL_ALIASES == expected
    # parser uses the registry dict (same object)
    assert P._AUDIT_LABEL_ALIASES is ch.AUDIT_LABEL_ALIASES


def test_specs_carry_attribution_for_freeze_rule():
    # each variant must carry a non-empty ASCII attribution label so a new entry
    # documents which company/quarter motivated it (the freeze-rule landing spot).
    for label, src, _flags in ch.SECTION_START_SPECS + ch.SECTION_END_SPECS:
        assert label and label.isascii() and isinstance(src, str)
    for wrong, right, note in ch.LABEL_FIXES:
        # note describes the OCR typo so it legitimately carries Korean; just non-empty.
        assert wrong and right and note
