"""Verify the UPDATED scripts/pl_breakdown/tier2.py::extract_tier2_abl (item6/item11 addition,
2026-08-28) against the population probe (abl_yesilcha_full_probe.py) and against the CURRENT
master (data/dart/viz/pl_breakdown_master.json), by calling the real handler function directly
on each quarter's freshly-parsed raw tables (same preprocessing parse_filing() uses:
_iter_tables_with_context + _tag_basis).  This is the authoritative source for the surgical
JSON patch values -- not hand-copied numbers.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/abl_yesilcha_verify_handler.py
"""
import glob
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.ifrs17.csm_extractor import _iter_tables_with_context
from scripts.pl_breakdown.common import _tag_basis
from scripts.pl_breakdown.tier2 import extract_tier2_abl

QUARTER_DIRS = {
    "2023.1Q": "data/dart/FY2023_Q1/raw/KR0070_에이비엘생명보험",
    "2023.2Q": "data/dart/FY2023_Q2/raw/KR0070_에이비엘생명보험",
    "2023.3Q": "data/dart/FY2023_Q3/raw/KR0070_에이비엘생명보험",
    "2023.4Q": "data/dart/FY2023_Q4/raw/KR0070_에이비엘생명보험_20240329001518",
    "2024.1Q": "data/dart/FY2024_Q1/raw/KR0070_에이비엘생명보험",
    "2024.2Q": "data/dart/FY2024_Q2/raw/KR0070_에이비엘생명보험",
    "2024.3Q": "data/dart/FY2024_Q3/raw/KR0070_에이비엘생명보험",
    "2024.4Q": "data/dart/FY2024_Q4/raw/KR0070_에이비엘생명보험_20250331001358",
    "2025.1Q": "data/dart/FY2025_Q1/raw/KR0070_에이비엘생명보험",
    "2025.2Q": "data/dart/FY2025_Q2/raw/KR0070_에이비엘생명보험",
    "2025.3Q": "data/dart/FY2025_Q3/raw/KR0070_에이비엘생명보험",
    "2025.4Q": "data/dart/FY2025_Q4/raw/KR0070_에이비엘생명보험_20260331003080",
    "2026.1Q": "data/dart/FY2026_Q1/raw/KR0070_에이비엘생명보험",
    "2026.2Q": "data/dart/FY2026_Q2/raw/KR0070_에이비엘생명보험",
}


def find_xml(rel_dir):
    d = REPO / rel_dir
    xs = glob.glob(str(d / "*.xml")) + glob.glob(str(d / "xml" / "*.xml"))
    if not xs:
        return None
    return Path(sorted(xs, key=lambda p: Path(p).stat().st_size, reverse=True)[0])


def main():
    master = json.loads((REPO / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))
    cur = {}
    for r in master:
        if r["원보험사코드"] == "KR0070":
            cur.setdefault(r["공시분기"], {})[r["항목번호"]] = r["값"]

    print(f"{'quarter':8s} {'item4':>9s} {'item5':>8s} {'item6_NEW':>10s} {'item6_OLD':>10s}  "
          f"{'item9':>8s} {'item10':>8s} {'item11_NEW':>11s} {'item11_OLD':>11s}")
    out = {}
    for q, rel_dir in QUARTER_DIRS.items():
        xml = find_xml(rel_dir)
        if xml is None:
            print(f"{q:8s}  NO XML")
            continue
        tables = list(_iter_tables_with_context(xml))
        _tag_basis(tables, xml)
        t2 = extract_tier2_abl(tables, quarter=q)
        old = cur.get(q, {})

        def f(x, w=9):
            return f"{x:>{w},.0f}" if isinstance(x, (int, float)) else f"{'None':>{w}s}"

        print(f"{q:8s} {f(t2.get(4))} {f(t2.get(5),8)} {f(t2.get(6),10)} {f(old.get(6),10)}  "
              f"{f(t2.get(9),8)} {f(t2.get(10),8)} {f(t2.get(11),11)} {f(old.get(11),11)}")
        out[q] = t2

    (REPO / "scripts/_probes/_tmp_abl_handler_output.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
