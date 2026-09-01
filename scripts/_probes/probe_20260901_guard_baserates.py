"""Base rates for the guard thresholds: how common is each section, per period?

Answers the questions the blast-radius run raised:
  * is `6-8 위험민감도` even part of the 2023 disclosure template?
  * do odd-quarter (간이공시) files legitimately select far fewer pages?
  * what is the real selected-page distribution per quarter type?
"""

from __future__ import annotations

import io
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from solvency.parser import quality_check as QC  # noqa: E402

PATTERNS = {
    "시장위험관리": re.compile(r"시장\s*위험\s*관리"),
    "금리위험액": re.compile(r"금리\s*위험액"),
    "주식위험액": re.compile(r"주식\s*위험액"),
    "위험민감도": re.compile(r"위험\s*민감도"),
    "금리민감도": re.compile(r"금리\s*민감도"),
    "민감도분석": re.compile(r"민감도\s*분석"),
}


def main() -> int:
    md_root = REPO / "md_inbox"
    per_period: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    pages: dict[str, list[int]] = defaultdict(list)
    for p in sorted(md_root.rglob("*.md")):
        meta, body = QC._read_md(p)
        period = p.parent.name
        per_period[period]["n"] += 1
        for name, pat in PATTERNS.items():
            if pat.search(body):
                per_period[period][name] += 1
        scope = (meta.get("parse_scope") or "").strip()
        if scope.startswith("keyword_window"):
            n = QC._selected_page_count(QC._parse_page_ranges(meta.get("source_page_ranges", "")))
            pages[period].append(n)

    print("\n=== section presence by period (count / total) ===\n")
    hdr = f"{'period':<12}{'n':>4}  " + "".join(f"{k:>13}" for k in PATTERNS)
    print(hdr)
    print("-" * len(hdr))
    for period in sorted(per_period):
        d = per_period[period]
        row = f"{period:<12}{d['n']:>4}  " + "".join(f"{d[k]:>13}" for k in PATTERNS)
        print(row)

    print("\n=== selected-page distribution (keyword_window scopes only) ===\n")
    print(f"{'period':<12}{'n':>4}{'min':>6}{'p10':>6}{'med':>6}{'max':>6}")
    print("-" * 42)
    for period in sorted(pages):
        v = sorted(pages[period])
        if not v:
            continue
        p10 = v[max(0, int(len(v) * 0.1) - 1)]
        print(
            f"{period:<12}{len(v):>4}{v[0]:>6}{p10:>6}"
            f"{int(statistics.median(v)):>6}{v[-1]:>6}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
