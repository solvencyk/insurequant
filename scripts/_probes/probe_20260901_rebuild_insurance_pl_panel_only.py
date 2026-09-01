# -*- coding: utf-8 -*-
"""Rebuild ONLY data/dart/viz/insurance_pl_breakdown.json, not the other 3 panels
scripts/viz_build_ifrs17_panels.py::main() would also touch (csm_amort_schedule.json /
bs_snapshot.json / sensitivity_heatmap.json). bs_snapshot.json is explicitly out of
scope for this ticket (17BS agent's file) -- this avoids even a transient rewrite of it.

Mirrors main()'s own per-panel call exactly:
  build_panel("*_insurance_pl_mvp.json", extract_pl_breakdown, add_as_of=False, apply_overrides=False)

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260901_rebuild_insurance_pl_panel_only.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

import scripts.viz_build_ifrs17_panels as vb  # noqa: E402

OUT_PATH = vb.OUT / "insurance_pl_breakdown.json"


def main() -> None:
    payload = vb.build_panel("*_insurance_pl_mvp.json", vb.extract_pl_breakdown, add_as_of=False, apply_overrides=False)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    ok_count = sum(1 for item in payload["companies"] if str(item.get("status")) == "ok")
    total_count = len(payload["companies"])
    print(f"Wrote {OUT_PATH} ({ok_count}/{total_count} ok)")

    for target in ("하나손해보험", "아이엠라이프생명보험", "카카오페이손해보험"):
        entry = next((c for c in payload["companies"] if c.get("company") == target), None)
        print(f"  {target}: {'FOUND status=' + str(entry.get('status')) if entry else 'MISSING'}")
        if entry:
            print(f"    rcept_no={entry.get('rcept_no')} caption={str(entry.get('caption'))[:60]!r}")


if __name__ == "__main__":
    main()
