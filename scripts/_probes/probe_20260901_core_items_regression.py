"""Did re-conversion lose any of the core items 1-28 for any company?

`extract_kics_detail_rows` returns (label, value) pairs; the raw count is noisy
because a wider page window also drags in balance-sheet rows that are not K-ICS
items at all. What matters is the mapping onto master items 1-28.

For every company, map old-MD and new-MD extractions onto the master's item
names for 2026.2Q and report items that were extractable before and are not now.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from solvency.parser.kics_disclosure_parser import extract_kics_detail_rows  # noqa: E402

QUARTER = "2026.2Q"
NEW = REPO / "md_inbox" / "FY2026_Q2"
OLD = REPO / "data" / "_derived" / "md_backup_20260901_windowfix" / "md_inbox"


def _body(p: Path) -> str:
    t = p.read_text(encoding="utf-8")
    _, _, rest = t.partition("---\n")
    _, _, body = rest.partition("\n---\n")
    return body


def main() -> int:
    master = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    keys = list(master[0].keys())
    F = {"code": keys[0], "item": keys[4], "name": keys[5], "quarter": keys[6]}
    names: dict[str, dict[int, str]] = {}
    for r in master:
        if r.get(F["quarter"]) != QUARTER:
            continue
        try:
            item = int(r[F["item"]])
        except (TypeError, ValueError):
            continue
        if 1 <= item <= 28:
            names.setdefault(r[F["code"]], {})[item] = r[F["name"]]

    total_lost = 0
    print(f"\n{'code':<9}{'old':>5}{'new':>5}  lost items 1-28")
    print("-" * 60)
    for new_md in sorted(NEW.glob("*.md")):
        code = new_md.stem.split("_")[0]
        old_md = OLD / new_md.name
        if not old_md.exists() or code not in names:
            continue
        old_body, new_body = _body(old_md), _body(new_md)
        if old_body == new_body:
            continue
        item_names = names[code]

        def mapped(body: str) -> set[int]:
            got = set()
            rows = dict(extract_kics_detail_rows(body, QUARTER))
            for item, name in item_names.items():
                if name in rows:
                    got.add(item)
            return got

        old_set, new_set = mapped(old_body), mapped(new_body)
        lost = sorted(old_set - new_set)
        total_lost += len(lost)
        flag = "" if not lost else f"  <-- LOST {lost}"
        print(f"{code:<9}{len(old_set):>5}{len(new_set):>5}{flag}")
    print(f"\ntotal core items lost across all re-converted companies: {total_lost}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
