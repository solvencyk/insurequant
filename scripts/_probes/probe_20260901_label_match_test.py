# -*- coding: utf-8 -*-
import sys, io
sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from solvency.parser.kics_baseline_match import _label_matches
from solvency.parser.kics_disclosure_parser import normalise_label, core_words

canonical = "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치"
variant = "2. 비례성원칙을 적용한 종속회사의 요구자본 대용치"
print("normalise_label(canonical) =", normalise_label(canonical))
print("normalise_label(variant)   =", normalise_label(variant))
print("core_words(canonical) =", core_words(canonical))
print("core_words(variant)   =", core_words(variant))
print("_label_matches(canonical, variant) =", _label_matches(canonical, variant))

# also test with spacing variant "요구 자본 대응치"
spaced = "2. 비례성원칙을 적용한 종속회사의 요구 자본 대응치"
print()
print("_label_matches(canonical, spaced) =", _label_matches(canonical, spaced))
