# -*- coding: utf-8 -*-
"""PL 축 소스 재조준 시뮬레이션 — 배포본으로 바꾸면 무엇이 닫히고 무엇이 깨지나.

룰 수정 전 전 버킷 양방향 시뮬레이션(memory feedback_simulate_rule_change_before_editing).
`validate_master_tables` 를 모듈로 import 해 `PL_PATH` 만 갈아끼우고 두 번 돌린다.

산출: 버킷별 카운트 diff + 새로 뜬 실패 전건 열거.
사용: python scripts/_probes/probe_20260825_simulate_pl_source_reaim.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

VIZ = "data/dart/viz/pl_breakdown_master.json"
DEP = "PL_breakdown.json"


def load_mod():
    spec = importlib.util.spec_from_file_location(
        "vmt", ROOT / "scripts" / "validate_master_tables.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(pl_path: str) -> dict:
    m = load_mod()
    m.PL_PATH = pl_path
    pl = m.load_long(pl_path)
    wf = m.load_long(m.WF_PATH)
    buf = io.StringIO()
    with redirect_stdout(buf):
        wf_holes, pl_holes = m._check_coverage(wf, pl)
        pb_pass, pb_fail, pb_skip, zleg, zerolegs = m._check_pl_bridge(pl)
        cc_pass, cc_fail, cc_minor, cc_skip = m._check_csm_crosscheck(pl, wf)
    return {
        "rows": sum(len(v) for v in pl.values()),
        "cells": sum(len(v) for v in pl.values()),
        "keys": len(pl),
        "pl_holes": pl_holes,
        "pb_pass": pb_pass, "pb_fail": pb_fail, "pb_skip": pb_skip,
        "zleg": zleg, "zerolegs": zerolegs,
        "cc_pass": cc_pass, "cc_fail": cc_fail, "cc_minor": cc_minor, "cc_skip": cc_skip,
    }


def key_of(x):
    """실패 행을 비교 가능한 키로. 구조를 모르므로 repr 로 안정화."""
    return repr(x)


def main() -> int:
    a = run(VIZ)
    b = run(DEP)

    print("=" * 80)
    print("PL 축 소스 재조준 시뮬레이션  (viz 중간산출물 -> 배포본)")
    print("=" * 80)
    print(f"  (회사,분기) 키    : {a['keys']:6d} -> {b['keys']:6d}   ({b['keys']-a['keys']:+d})")
    print(f"  셀 수             : {a['cells']:6d} -> {b['cells']:6d}   ({b['cells']-a['cells']:+d})")
    print()
    for label, ka in [("HOLE-PL(coverage)", "pl_holes"), ("PL_BRIDGE fail", "pb_fail"),
                      ("zero_legs", "zleg"), ("impossible0", "zerolegs"),
                      ("crosscheck fail", "cc_fail")]:
        na, nb = len(a[ka]), len(b[ka])
        print(f"  {label:22s} {na:5d} -> {nb:5d}  ({nb-na:+d})")
    for label, ka in [("PL_BRIDGE pass", "pb_pass"), ("PL_BRIDGE skip", "pb_skip"),
                      ("crosscheck pass", "cc_pass"), ("crosscheck skip", "cc_skip"),
                      ("crosscheck minor", "cc_minor")]:
        print(f"  {label:22s} {a[ka]:5d} -> {b[ka]:5d}  ({b[ka]-a[ka]:+d})")

    for label, ka in [("HOLE-PL", "pl_holes"), ("PL_BRIDGE fail", "pb_fail"),
                      ("zero_legs", "zleg"), ("impossible0", "zerolegs"),
                      ("crosscheck fail", "cc_fail")]:
        sa = {key_of(x) for x in a[ka]}
        sb = {key_of(x) for x in b[ka]}
        gone = sorted(sa - sb)
        new = sorted(sb - sa)
        print("\n" + "-" * 80)
        print(f"[{label}]  사라짐(=phantom) {len(gone)}건 / 새로 뜸 {len(new)}건")
        print("-" * 80)
        for x in gone:
            print(f"   PHANTOM  {x[:180]}")
        for x in new:
            print(f"   NEW      {x[:180]}")

    out = ROOT / "scripts" / "_probes" / "_simulate_pl_source_reaim_out.json"
    out.write_text(json.dumps(
        {"viz": {k: (v if isinstance(v, int) else [key_of(x) for x in v])
                 for k, v in a.items()},
         "deployed": {k: (v if isinstance(v, int) else [key_of(x) for x in v])
                      for k, v in b.items()}},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
