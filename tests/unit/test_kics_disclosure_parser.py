import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from solvency.parser.kics_disclosure_parser import (
    build_label_lookups,
    extract_kics_detail_rows,
    labels_compatible,
    match_baseline_value,
    parse_value,
)

KR0005_MD = next((ROOT / "md_inbox" / "FY2025_Q4").glob("KR0005_*.md"))
KR0005_EXPECTED = {
    18: "782",
    19: "5653",
    20: "2371",
    21: "2385",
    22: "6205",
    27: "156.48",
}


def _kr0005_baseline_names() -> dict[int, str]:
    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    out = {}
    for row in rows:
        if row["\uc6d0\ubcf4\ud5d8\uc0ac\ucf54\ub4dc"] != "KR0005":
            continue
        if row["\uacf5\uc2dc\ubd84\uae30"] != "2025.3Q":
            continue
        out[row["\ud56d\ubaa9\ubc88\ud638"]] = row["\ud56d\ubaa9\uba85"]
    return out


def test_kr0005_split_table_extracts_items_18_to_22():
    md = KR0005_MD.read_text(encoding="utf-8")
    table = extract_kics_detail_rows(md, "2025.4Q")
    labels = {label for label, _ in table}
    assert any(
        "\uc704\ud5d8\uc561" in label and label.strip().startswith("2.")
        for label in labels
    )
    assert any(
        label.strip().startswith("3.") and "\uc704\ud5d8\uc561" in label
        for label in labels
    )
    assert len(table) >= 27


@pytest.mark.parametrize("item_no,expected", list(KR0005_EXPECTED.items()))
def test_kr0005_golden_values(item_no, expected):
    md = KR0005_MD.read_text(encoding="utf-8")
    lookup, core = build_label_lookups(extract_kics_detail_rows(md, "2025.4Q"))
    item_name = _kr0005_baseline_names()[item_no]
    assert match_baseline_value(item_name, lookup, core) == expected


def test_labels_compatible_blocks_balance_sheet_general_insurance():
    risk = "2. \uc77c\ubc18\uc190\ud574\ubcf4\ud5d8\uc704\ud5d8\uc561"
    liability = "2. \uc77c\ubc18\uc190\ud574\ubcf4\ud5d8"
    assert labels_compatible(risk, liability) is False
    assert labels_compatible(risk, risk) is True


def test_labels_compatible_blocks_capital_amount_vs_ratio():
    assert labels_compatible("\uae30\ubcf8\uc790\ubcf8\ube44\uc728", "\uae30\ubcf8\uc790\ubcf8") is False
    assert labels_compatible("\uae30\ubcf8\uc790\ubcf8", "\uae30\ubcf8\uc790\ubcf8\ube44\uc728") is False


def test_samsung_life_2024_2q_summary_and_detail_extract():
    md = (ROOT / "md_inbox" / "FY2024_Q2" / "KR0069_\uc0bc\uc131\uc0dd\uba85.md").read_text(
        encoding="utf-8"
    )
    table = extract_kics_detail_rows(md, "2024.2Q")
    lookup, core = build_label_lookups(table)
    solvency = match_baseline_value("\uac00. \uc9c0\uae09\uc5ec\ub825\uae08\uc561", lookup, core)
    scr = match_baseline_value("\ub098. \uc9c0\uae09\uc5ec\ub825\uae30\uc900\uae08\uc561", lookup, core)
    assert solvency == "532470"
    assert scr == "264194"
    basic = match_baseline_value("\uae30\ubcf8\uc790\ubcf8", lookup, core)
    assert basic == "437468"


def test_samsung_life_2023_1q_bullet_section_extract():
    md = (ROOT / "md_inbox" / "FY2023_Q1" / "KR0069_\uc0bc\uc131\uc0dd\uba85.md").read_text(
        encoding="utf-8"
    )
    table = extract_kics_detail_rows(md, "2023.1Q")
    lookup, core = build_label_lookups(table)
    assert len(table) >= 25
    assert match_baseline_value("\uac00. \uc9c0\uae09\uc5ec\ub825\uae08\uc561", lookup, core) == "479030"
    assert match_baseline_value("\ub098. \uc9c0\uae09\uc5ec\ub825\uae30\uc900\uae08\uc561", lookup, core) == "218255"
    assert match_baseline_value("\uae30\ubcf8\uc790\ubcf8", lookup, core) == "428262"


def test_samsung_life_2023_3q_detail_extract():
    md = (ROOT / "md_inbox" / "FY2023_Q3" / "KR0069_\uc0bc\uc131\uc0dd\uba85.md").read_text(
        encoding="utf-8"
    )
    table = extract_kics_detail_rows(md, "2023.3Q")
    lookup, core = build_label_lookups(table)
    assert len(table) >= 25
    assert match_baseline_value("\uac00. \uc9c0\uae09\uc5ec\ub825\uae08\uc561", lookup, core) == "531538"
    assert match_baseline_value("\ub098. \uc9c0\uae09\uc5ec\ub825\uae30\uc900\uae08\uc561", lookup, core) == "241047"


def test_parse_value_spaced_negative_sign():
    assert parse_value("- 3,094") == "-3094"


def test_parse_value_trailing_minus_ocr():
    assert parse_value("256 -") == "-256"


def test_quarter_picker_prefers_lag_column_over_current():
    from solvency.parser.kics_disclosure_parser import make_quarter_column_picker, split_row

    header = split_row(
        "| 구분 | 당분기 (24.2Q) | 당분기-1분기 (24.1Q) | 당분기-2분기 (23.4Q) |"
    )
    pick = make_quarter_column_picker("2024.1Q")
    assert pick(header) == 2


def test_hana_item6_capital_securities_label_match():
    md_path = next((ROOT / "md_inbox" / "FY2025_Q4").glob("KR0050_*.md"))
    md = md_path.read_text(encoding="utf-8")
    lookup, core = build_label_lookups(extract_kics_detail_rows(md, "2025.4Q"))
    item_name = "2. 자본항목 중 보통주 이외의 자본증권"
    assert match_baseline_value(item_name, lookup, core) == "1000"


def test_shinhan_ez_2024_1q_lag_column_extract():
    md_path = next((ROOT / "md_inbox" / "FY2024_Q2").glob("KR0051_*.md"))
    md = md_path.read_text(encoding="utf-8")
    lookup, core = build_label_lookups(extract_kics_detail_rows(md, "2024.1Q"))
    item4 = match_baseline_value(
        "Ⅰ. 건전성감독기준 재무상태표 상의 순자산", lookup, core
    )
    retained = match_baseline_value("3. 이익잉여금", lookup, core)
    reserve = match_baseline_value("7. 조정준비금", lookup, core)
    assert item4 == "1170"
    assert retained == "-205"
    assert reserve == "-113"


def test_chubb_life_2023_1q_negative_retained_earnings():
    md_path = next((ROOT / "md_inbox" / "FY2023_Q1").glob("KR0100_*.md"))
    md = md_path.read_text(encoding="utf-8")
    table = extract_kics_detail_rows(md, "2023.1Q")
    retained = next(v for label, v in table if "\uc774\uc775\uc789\uc5ec\uae08" in label)
    assert parse_value(retained) == "-3094"


def test_shinhan_life_item22_tax_adjustment_positive_magnitude():
    from solvency.parser.kics_disclosure_parser import normalise_item_value

    assert (
        normalise_item_value(22, "\u2161. \ubc95\uc778\uc138\uc870\uc815\uc561", "-17370")
        == "17370"
    )


def test_shinhan_life_item17_middle_dot_label():
    md_path = next((ROOT / "md_inbox" / "FY2025_Q4").glob("KR0094_*.md"))
    md = md_path.read_text(encoding="utf-8")
    lookup, core = build_label_lookups(extract_kics_detail_rows(md, "2025.4Q"))
    item_name = "1. \uc0dd\uba85\uc7a5\uae30\uc190\ud574\ubcf4\ud5e8\uc704\ud5d8\uc561"
    assert match_baseline_value(item_name, lookup, core) == "49951"


def test_shinhan_life_item16_not_life_subtable_diversification():
    md_path = next((ROOT / "md_inbox" / "FY2024_Q4").glob("KR0094_*.md"))
    md = md_path.read_text(encoding="utf-8")
    lookup, core = build_label_lookups(extract_kics_detail_rows(md, "2024.4Q"))
    item_name = "- \ubd84\uc0b0\ud6a8\uacfc : (1+2+3+4+5) - \u2160"
    assert match_baseline_value(item_name, lookup, core) == "16820"


def test_samsung_life_item10_fill_from_supplemented_baseline():
    sys.path.insert(0, str(ROOT / "scripts"))
    from fill_period_to_disclosure import _supplement_core_baseline, _fields
    import json

    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    F = _fields()
    partial = [
        r
        for r in rows
        if r.get(F["code"]) == "KR0069"
        and r.get(F["quarter"]) == "2024.2Q"
        and int(r.get(F["item"], 99)) <= 28
    ]
    supplemented = _supplement_core_baseline(partial, rows, "KR0069", F)
    items = {int(r[F["item"]]) for r in supplemented}
    assert 10 in items


def test_kakaopay_2025_1q_reversed_capital_labels():
    md_path = next((ROOT / "md_inbox" / "FY2025_Q1").glob("KR1098_*.md"))
    md = md_path.read_text(encoding="utf-8")
    lookup, core = build_label_lookups(extract_kics_detail_rows(md, "2025.1Q"))
    assert match_baseline_value("1. 보통주", lookup, core) == "2000"
    assert match_baseline_value("3. 이익잉여금", lookup, core) == "-1315"
    assert match_baseline_value("7. 조정준비금", lookup, core) == "-241"
    item4 = match_baseline_value(
        "Ⅰ. 건전성감독기준 재무상태표 상의 순자산", lookup, core
    )
    assert item4 == "421"


def test_metlife_2023_3q_item4_label():
    md_path = next((ROOT / "md_inbox" / "FY2023_Q3").glob("KR0095_*.md"))
    md = md_path.read_text(encoding="utf-8")
    lookup, core = build_label_lookups(extract_kics_detail_rows(md, "2023.3Q"))
    item4 = match_baseline_value(
        "Ⅰ. 건전성감독기준 재무상태표 상의 순자산", lookup, core
    )
    assert item4 == "50082"


def test_kyobo_planet_2024_3q_non_controlling_interest():
    md_path = next((ROOT / "md_inbox" / "FY2024_Q3").glob("KR1010_*.md"))
    md = md_path.read_text(encoding="utf-8")
    lookup, core = build_label_lookups(extract_kics_detail_rows(md, "2024.3Q"))
    assert match_baseline_value("6. 비지배지분", lookup, core) == "4"