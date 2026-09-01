# -*- coding: utf-8 -*-
"""Patch labels_compatible() in kics_disclosure_parser.py: compare on
whitespace-stripped copies so a Docling mid-word space insertion (e.g.
"요구자본" -> "요구자 본" / "요 구자본") doesn't wrongly reject an
otherwise-identical label. Confirmed root cause of KR0051(신한이지손해) item24/25/26
rows returning None despite the source row being present with a matchable
(dash) value after normalise_label already treats the two labels as equal.
"""
from __future__ import annotations
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "src" / "solvency" / "parser" / "kics_disclosure_parser.py"

OLD = (
    'def labels_compatible(baseline_name: str, table_label: str) -> bool:\n'
    '    if "위험액" in baseline_name and "위험액" not in table_label:\n'
    '        return False\n'
    '    if "요구자본" in baseline_name and "요구자본" not in table_label:\n'
    '        return False\n'
    '    if "비율" in baseline_name and "비율" not in table_label:\n'
    '        return False\n'
    '    if "비율" in table_label and "비율" not in baseline_name:\n'
    '        return False\n'
    '    if "순자산" in baseline_name and "순자산" not in table_label:\n'
    '        return False\n'
    '    if "순자산" in baseline_name and "지급여력금액" in table_label:\n'
    '        return False\n'
    "    # item12(지급여력금액으로 \"불인정\"하는 항목) starts with item1's bare label\n"
    '    # "지급여력금액", so when item12\'s own row is unmatched/dropped (e.g. a\n'
    '    # "-" value gets filtered out of `lookup` before this ever runs), the\n'
    '    # startswith() fallback in match_baseline_value() below silently\n'
    '    # substitutes item1\'s value for item12 (found live in ~154 rows across\n'
    "    # ~15 companies, e.g. KR0004 2023.1Q, KR0005 2023.3Q). Likewise item13\n"
    '    # (보완자본으로 "재분류"하는 항목) starts with item3\'s bare "보완자본" —\n'
    '    # same latent defect, not yet observed to fire but closed here too.\n'
    '    if "불인정" in baseline_name and "불인정" not in table_label:\n'
    '        return False\n'
    '    if "재분류" in baseline_name and "재분류" not in table_label:\n'
    '        return False\n'
    '    # Reverse direction, mirroring the 순자산/비율 guards above: some companies\'\n'
    '    # OWN stored baseline name for item1 is a bare "지급여력금액" (missing the "가."\n'
    '    # prefix + suffix a healthy baseline has) — e.g. KR0004(예별손해보험) 2023.2Q\'s own\n'
    "    # item1 항목명 field is literally '지급여력금액'. Without this check, that bare\n"
    '    # baseline_name.startswith() the item12 table row ("지급여력금액으로 불인정하는 ...")\n'
    "    # and wrongly returns item12's value (usually 0) AS item1's — the same\n"
    '    # collision as above but triggered from the opposite side.\n'
    '    if "불인정" in table_label and "불인정" not in baseline_name:\n'
    '        return False\n'
    '    if "재분류" in table_label and "재분류" not in baseline_name:\n'
    '        return False\n'
    '    return True\n'
)

NEW = (
    'def labels_compatible(baseline_name: str, table_label: str) -> bool:\n'
    "    # Compare on whitespace-stripped copies: Docling occasionally inserts a\n"
    "    # stray space mid-word when a long label wraps across two PDF lines\n"
    '    # (e.g. "요구자본" -> "요구자 본" / "요 구자본") — a raw substring check\n'
    '    # below would then wrongly reject an otherwise-identical label even\n'
    "    # though normalise_label() already treats the two as equal (item24-26\n"
    '    # 종속회사/관계회사 요구자본 rows going row-absent in the master, 2026-09-01 item23\n'
    '    # 자식 칸 감사 — KR0051 2023.1Q\'s own "요구자 본"/"요 구자본" labels).\n'
    '    bn = baseline_name.replace(" ", "")\n'
    '    tl = table_label.replace(" ", "")\n'
    '    if "위험액" in bn and "위험액" not in tl:\n'
    '        return False\n'
    '    if "요구자본" in bn and "요구자본" not in tl:\n'
    '        return False\n'
    '    if "비율" in bn and "비율" not in tl:\n'
    '        return False\n'
    '    if "비율" in tl and "비율" not in bn:\n'
    '        return False\n'
    '    if "순자산" in bn and "순자산" not in tl:\n'
    '        return False\n'
    '    if "순자산" in bn and "지급여력금액" in tl:\n'
    '        return False\n'
    "    # item12(지급여력금액으로 \"불인정\"하는 항목) starts with item1's bare label\n"
    '    # "지급여력금액", so when item12\'s own row is unmatched/dropped (e.g. a\n'
    '    # "-" value gets filtered out of `lookup` before this ever runs), the\n'
    '    # startswith() fallback in match_baseline_value() below silently\n'
    '    # substitutes item1\'s value for item12 (found live in ~154 rows across\n'
    "    # ~15 companies, e.g. KR0004 2023.1Q, KR0005 2023.3Q). Likewise item13\n"
    '    # (보완자본으로 "재분류"하는 항목) starts with item3\'s bare "보완자본" —\n'
    '    # same latent defect, not yet observed to fire but closed here too.\n'
    '    if "불인정" in bn and "불인정" not in tl:\n'
    '        return False\n'
    '    if "재분류" in bn and "재분류" not in tl:\n'
    '        return False\n'
    '    # Reverse direction, mirroring the 순자산/비율 guards above: some companies\'\n'
    '    # OWN stored baseline name for item1 is a bare "지급여력금액" (missing the "가."\n'
    '    # prefix + suffix a healthy baseline has) — e.g. KR0004(예별손해보험) 2023.2Q\'s own\n'
    "    # item1 항목명 field is literally '지급여력금액'. Without this check, that bare\n"
    '    # baseline_name.startswith() the item12 table row ("지급여력금액으로 불인정하는 ...")\n'
    "    # and wrongly returns item12's value (usually 0) AS item1's — the same\n"
    '    # collision as above but triggered from the opposite side.\n'
    '    if "불인정" in tl and "불인정" not in bn:\n'
    '        return False\n'
    '    if "재분류" in tl and "재분류" not in bn:\n'
    '        return False\n'
    '    return True\n'
)

src = TARGET.read_text(encoding="utf-8")
n = src.count(OLD)
print(f"occurrences of OLD block: {n}")
if n != 1:
    raise SystemExit("ABORT: expected exactly 1 occurrence")
TARGET.write_text(src.replace(OLD, NEW), encoding="utf-8")
print("patched", TARGET)
