"""Mutation test for the new extra-LOB wiring in validate_master_tables.

Two things must be true, and "the gate printed 0" proves neither on its own:
  1. `load_pl_extra_lob` SUMS an extra-LOB parent `2-N` and does NOT sum its
     children `3-N`..`12-N` (double counting would silently re-break the equation).
  2. The unknown-hyphen census FIRES on a shape the equation does not know
     (e.g. a future `13-1`).  Today it reports 0 — that must mean "none exist",
     not "the check is dead".

Read-only w.r.t. the repo: builds synthetic masters in the system temp dir.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_master_tables as V  # noqa: E402


def _rows(extra):
    base = [{"원수사명": "테스트재보험", "공시분기": "2099.1Q", "항목번호": 1,
             "항목명": "보험손익", "값": 1000.0}]
    return base + extra


def _write(rows) -> str:
    fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(rows, fh, ensure_ascii=False)
    fh.close()
    return fh.name


def check(name, rows, want_sum, want_unknown):
    sums, unknown = V.load_pl_extra_lob(_write(rows))
    got_sum = sums.get(("테스트재보험", "2099.1Q"), 0.0)
    got_unk = len(unknown)
    ok = (got_sum == want_sum) and (got_unk == want_unknown)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: Σ2-N={got_sum} (want {want_sum}) "
          f"unknown={got_unk} (want {want_unknown})")
    if unknown:
        for u in unknown:
            print(f"          LEGUNK {u}")
    return ok


def main() -> None:
    print("mutation: extra-LOB summation + unknown-hyphen census")
    ok = True
    # 1. parent only -> summed
    ok &= check("parent 2-1 is summed",
                _rows([{"원수사명": "테스트재보험", "공시분기": "2099.1Q", "항목번호": "2-1",
                        "항목명": "장기재보험 손익", "값": 500.0}]), 500.0, 0)
    # 2. parent + its children -> children must NOT be added (no double count)
    ok &= check("children 3-1/8-1 are NOT summed",
                _rows([{"원수사명": "테스트재보험", "공시분기": "2099.1Q", "항목번호": "2-1",
                        "항목명": "장기재보험 손익", "값": 500.0},
                       {"원수사명": "테스트재보험", "공시분기": "2099.1Q", "항목번호": "3-1",
                        "항목명": "장기재보험 수재손익", "값": 300.0},
                       {"원수사명": "테스트재보험", "공시분기": "2099.1Q", "항목번호": "8-1",
                        "항목명": "장기재보험 출재손익", "값": 200.0}]), 500.0, 0)
    # 3. an unknown shape (13-1) must be REPORTED, not silently dropped
    ok &= check("unknown 13-1 fires the census",
                _rows([{"원수사명": "테스트재보험", "공시분기": "2099.1Q", "항목번호": "13-1",
                        "항목명": "자동차재보험 손익", "값": 77.0}]), 0.0, 1)
    # 4. two parents (2-1 + 2-2) both summed
    ok &= check("multiple parents 2-1+2-2 both summed",
                _rows([{"원수사명": "테스트재보험", "공시분기": "2099.1Q", "항목번호": "2-1",
                        "항목명": "A", "값": 500.0},
                       {"원수사명": "테스트재보험", "공시분기": "2099.1Q", "항목번호": "2-2",
                        "항목명": "B", "값": 60.0}]), 560.0, 0)
    # 5. plain integer 항목번호 must be untouched by both axes
    ok &= check("plain integer item numbers ignored",
                _rows([{"원수사명": "테스트재보험", "공시분기": "2099.1Q", "항목번호": 13,
                        "항목명": "자동차손익", "값": 999.0}]), 0.0, 0)
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
