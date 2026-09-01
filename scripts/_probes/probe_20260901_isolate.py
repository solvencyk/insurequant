# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "src")
from solvency.parser.kics_baseline_match import _label_matches, match_baseline_value_or_zero
from solvency.parser.kics_disclosure_parser import normalise_label, core_words, match_baseline_value

item_name = '2. 비례성원칙을 적용한 종속회사의 요구자본 대응치'
table_label = '2. 비례성원칙을 적용한 종속회사의 요구 자본 대응치'
print("normalise_label(item_name)  =", normalise_label(item_name))
print("normalise_label(table_label)=", normalise_label(table_label))
print("_label_matches =", _label_matches(item_name, table_label))

# now test match_baseline_value (the FIRST thing match_baseline_value_or_zero tries)
lookup = {}
core = {}
r = match_baseline_value(item_name, lookup, core)
print("match_baseline_value(empty lookups) =", r)

table_pairs = [(table_label, "0")]
r2 = match_baseline_value_or_zero(item_name, lookup, core, table_pairs)
print("match_baseline_value_or_zero =", r2)
