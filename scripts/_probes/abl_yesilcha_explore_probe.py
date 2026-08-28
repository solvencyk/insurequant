"""Exploration probe for inbox/parser/20260828T2100Z__orchestrator__KR0070__abl_yesilcha_both_legs.md.

Dumps, for a given ABL(KR0070) quarter's raw XML: every non-rollforward table whose
caption or row labels mention "보험영업수익" / "보험영업비용" / "재보험수익" / "재보험비용",
plus which table `extract_tier2_abl`'s existing `find()` picks for rev_t/re_t (items 4/5/9/10)
-- to determine whether the note the ticket quotes (주석 26 보험영업수익과 보험영업비용) is the
SAME table object already used for items 4/5/9/10, or a separate one.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/abl_yesilcha_explore_probe.py [quarter_key]
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.ifrs17.csm_extractor import _iter_tables_with_context
from scripts.pl_breakdown.common import _norm, _row_nums
from scripts.pl_breakdown.tier2 import _is_rollforward

QUARTERS = [
    ("2023.1Q", REPO / "data/dart/FY2023_Q1/raw/KR0070_에이비엘생명보험"),
    ("2023.2Q", REPO / "data/dart/FY2023_Q2/raw/KR0070_에이비엘생명보험"),
    ("2023.3Q", REPO / "data/dart/FY2023_Q3/raw/KR0070_에이비엘생명보험"),
    ("2023.4Q", REPO / "data/dart/FY2023_Q4/raw/KR0070_에이비엘생명보험_20240329001518"),
    ("2024.1Q", REPO / "data/dart/FY2024_Q1/raw/KR0070_에이비엘생명보험"),
    ("2024.2Q", REPO / "data/dart/FY2024_Q2/raw/KR0070_에이비엘생명보험"),
    ("2024.3Q", REPO / "data/dart/FY2024_Q3/raw/KR0070_에이비엘생명보험"),
    ("2024.4Q", REPO / "data/dart/FY2024_Q4/raw/KR0070_에이비엘생명보험_20250331001358"),
    ("2025.1Q", REPO / "data/dart/FY2025_Q1/raw/KR0070_에이비엘생명보험"),
    ("2025.2Q", REPO / "data/dart/FY2025_Q2/raw/KR0070_에이비엘생명보험"),
    ("2025.3Q", REPO / "data/dart/FY2025_Q3/raw/KR0070_에이비엘생명보험"),
    ("2025.4Q", REPO / "data/dart/FY2025_Q4/raw/KR0070_에이비엘생명보험_20260331003080"),
    ("2026.1Q", REPO / "data/dart/FY2026_Q1/raw/KR0070_에이비엘생명보험"),
    ("2026.2Q", REPO / "data/dart/FY2026_Q2/raw/KR0070_에이비엘생명보험"),
]


def find_xml(d):
    if not d.exists():
        return None
    xmls = [p for p in d.glob("*.xml")]
    return xmls[0] if xmls else None


def find_abl_rev_t(tables):
    for t in tables:
        if _is_rollforward(t):
            continue
        capf = _norm(t.caption or "").replace(" ", "")
        if all(n in capf for n in ["잔여보장", "회수", "보험수익"]) and "재보험" not in capf:
            return t
    return None


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for q, d in QUARTERS:
        if only and q != only:
            continue
        xml = find_xml(d)
        if xml is None:
            print(f"=== {q}: NO XML FOUND in {d} ===")
            continue
        print(f"\n=== {q}  ({xml.relative_to(REPO)}) ===")
        tables = list(_iter_tables_with_context(xml))
        print(f"  total tables: {len(tables)}")

        rev_t = find_abl_rev_t(tables)
        print(f"  extract_tier2_abl rev_t caption: {(rev_t.caption if rev_t else None)!r}")
        if rev_t is not None:
            print(f"    rev_t row labels: {[_norm(r[0]) for r in rev_t.rows][:15]}")

        hits = []
        for i, t in enumerate(tables):
            cap = _norm(t.caption or "")
            labs = " ".join(_norm(r[0]) for r in t.rows)
            blob = cap + " " + labs
            if ("보험영업수익" in blob and "보험영업비용" in blob) or \
               ("예상보험금" in blob and "발생보험금" in blob):
                hits.append((i, t))

        print(f"  candidate 주석26-style tables: {len(hits)}")
        for i, t in hits:
            print(f"  --- table[{i}] rollforward={_is_rollforward(t)} caption={_norm(t.caption)!r}")
            print(f"      header: {t.header}")
            for r in t.rows:
                lab = _norm(r[0])
                nums = _row_nums(r)
                print(f"      {lab!r:40s} {nums}")


if __name__ == "__main__":
    main()
