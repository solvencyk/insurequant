# -*- coding: utf-8 -*-
"""Final option-(c) computation for KR0005 2025.3Q/2026.2Q, using ONLY values already resident
in the (gate-verified, item36/19-fixed) master -- no fresh raw re-scan for 17/18/19/20/21 (those
cells are out of this session's scope and already correct). This is the direct application of
the formula the task specified:

  item15후 = sqrt(W' R4 W) + item21후,   W = (item17, item18, item19, item20)후   [all MASTER, current]
  item14후 = unchanged (원문 헤드라인 anchor, already in master)
  item23후 = unchanged (already in master, 0 both quarters)
  item22후 = item15후 - item14후 + item23후          (residual against the anchor)
  item16후 = (item17+item18+item19+item20+item21)후 - item15후

R4 imported from src/solvency/validation/kics_json_rules.py (not retyped).

Cross-checked separately against:
  (A) scripts/_probes/verify_20260901_kr0005_combined_after.py -- independent raw-PDF re-scan
      via the canonical scan_occurrences()/resolve_leaf() pipeline (fresh leaf derivation).
  (B) scripts/rebuild_combined_transition_after.py --dry-run --only KR0005 (KICS_VERBOSE=1) --
      the canonical script's own full pipeline, unmodified methodology.
  (C) data/_derived/_patch_2026q2_KR0005.json -- prior (2026-08-31) session's own computation.
All four agree to within 0.4 (~0.002% relative) on item15/16/22 -- see report.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
from solvency.validation.kics_json_rules import R4  # noqa: E402

TARGET = ROOT / "kics_disclosure.json"
CODE = "KR0005"
QUARTERS = ["2025.3Q", "2026.2Q"]


def _num(x):
    if x is None or x == "":
        return None
    return float(str(x).replace(",", ""))


def main():
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    by_cq = {}
    for r in data:
        c, q = r["원보험사코드"], r["공시분기"]
        by_cq.setdefault((c, q), {})[int(r["항목번호"])] = r

    for q in QUARTERS:
        items = by_cq[(CODE, q)]
        it17 = _num(items[17]["값_적용후"])
        it18 = _num(items[18]["값_적용후"])
        it19 = _num(items[19]["값_적용후"])
        it20 = _num(items[20]["값_적용후"])
        it21 = _num(items[21]["값_적용후"])
        it14 = _num(items[14]["값_적용후"])
        it23 = _num(items[23]["값_적용후"]) or 0.0

        W = np.array([it17, it18, it19, it20], float)
        item15_new = float(np.sqrt(W @ R4 @ W)) + it21
        item16_new = (it17 + it18 + it19 + it20 + it21) - item15_new
        item22_new = item15_new - it14 + it23

        print(f"\n=== {CODE} {q} ===")
        print(f"  inputs (master, already-fixed): item17후={it17} item18후={it18} "
              f"item19후={it19} item20후={it20} item21후={it21} item14후(anchor)={it14} item23후={it23}")
        print(f"  item15후 = sqrt(W'R4W)+item21 = {item15_new:.4f}  -> round2 = {round(item15_new,2)}")
        print(f"  item16후 = sum(17..21)-item15 = {item16_new:.4f}  -> round2 = {round(item16_new,2)}")
        print(f"  item22후 = item15-item14+item23 = {item22_new:.4f}  -> round2 = {round(item22_new,2)}")

        cur15 = _num(items[15]["값_적용후"])
        cur16 = _num(items[16]["값_적용후"])
        cur22 = _num(items[22]["값_적용후"])
        print(f"  MASTER 현재(pre-patch): item15후={cur15}  item16후={cur16}  item22후={cur22}")
        print(f"  DELTA: item15 {cur15}->{round(item15_new,2)} ({round(item15_new,2)-cur15:+.2f})  "
              f"item16 {cur16}->{round(item16_new,2)} ({round(item16_new,2)-cur16:+.2f})  "
              f"item22 {cur22}->{round(item22_new,2)} ({round(item22_new,2)-cur22:+.2f})")

        # identity re-check with the NEW values plugged back in
        check_R6 = (it17 + it18 + it19 + it20 + it21) - item15_new - item16_new
        check_R5 = item15_new - item22_new + it23 - it14
        print(f"  [self-check] R6 residual (children-15-16) = {check_R6:.6f} (want ~0)")
        print(f"  [self-check] R5 residual (15-22+23-14)    = {check_R5:.6f} (want ~0)")


if __name__ == "__main__":
    main()
