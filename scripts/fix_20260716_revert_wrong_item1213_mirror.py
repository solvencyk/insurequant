"""Bugfix: scripts/backfill_post_transition_when_not_applied.py (run early
in the 2026-07-15 round-1 session) mirrored item12/13 (값_적용후 = 값) for
14 (name,quarter) pairs classified "safe" by its item1/14/27-only check.
For 12 of those pairs this was correct (all of items 1/2/3/12/13/14/27/28
전=후 exactly -- genuine zero-TFI-effect quarters). For 2 it was WRONG:

  KB라이프생명 2024.2Q, 동양생명 2024.1Q -- item2(기본자본)_적용후 was
  ALREADY correctly populated (from an earlier, unrelated extraction) with
  a value that genuinely differs from 값_전 (TFI capital-tier reallocation
  effect -- see 2026-07-16 owner note re: item28 diverging even for
  non-appliers). item2 = item4 - item12 - item13 (raw footnote formula,
  confirmed via dozens of raw PDF reads this session). item4 is confirmed
  전=후 (pure accounting figure, always TFI-invariant). Plugging the
  mirrored item12/13 into that identity reproduces item2_전, not the
  already-trusted item2_후 -- proof the mirror was wrong for these two.

  KB라이프: item4-item12-item13 = 61158-300-16677 = 44181 = item2_전
    (not 44678.96 = item2_후, diff exactly 497.96 = item28's diff)
  동양생명: 40214-0-19645 = 20569 ~= item2_전(20570) (not item2_후 23969.34)

Raw for both is TFI-only (abbreviated "1)공통적용" table only -- 5 rows:
27/1/2/3/14 -- no full items-1-26 경과조치후 breakdown exists), so the true
item12/13_후 split isn't independently derivable without more information.
Reverting to None (honest gap) rather than leaving the wrong mirrored value
in place. See scripts/_probes/audit_backfill_round1_correctness.py.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGET_FILES = [REPO / "kics_disclosure.json", REPO / "templates" / "kics_disclosure.json"]

REVERTS = [
    ("KB라이프생명", "2024.2Q", 12),
    ("KB라이프생명", "2024.2Q", 13),
    ("동양생명", "2024.1Q", 12),
    ("동양생명", "2024.1Q", 13),
]


def main():
    for path in TARGET_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        reverted = 0
        for r in data:
            key = (r["원수사명"], r["공시분기"], r["항목번호"])
            for name, q, n in REVERTS:
                if key == (name, q, n):
                    if "값_적용후" in r:
                        del r["값_적용후"]
                        reverted += 1
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{path.relative_to(REPO)}: reverted {reverted} cells")


if __name__ == "__main__":
    main()
