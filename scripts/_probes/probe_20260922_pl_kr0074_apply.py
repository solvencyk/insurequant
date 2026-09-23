# -*- coding: utf-8 -*-
"""KR0074(라이나생명) 2023.4Q PL 20칸을 셀 단위로 채운다 — 통째 재빌드 대신.

`build_pl_breakdown._GOLD_CELL_OVERRIDE` 에 방금 등재한 값을 정본으로 읽어
data/dart/viz/pl_breakdown_master.json 과 루트 PL_breakdown.json 두 곳에 upsert 한다.

가드(하나라도 어기면 아무것도 안 쓰고 중단):
  · 대상은 (KR0074, 2023.4Q) 뿐. 다른 회사·분기 셀은 한 개도 안 건드린다.
  · 현재 값이 None 인 칸만 채운다. 값이 이미 있으면(4·9·13·14) 건너뛴다.
  · 쓰기 전후 두 파일의 행 수가 같아야 한다(행 추가·삭제 없음).
  · 항등식 재검산: 2=3+8 · 1=2-16 · 17=18+19 · 20=1+17 · 22=20+21 · 24=22-23.

Usage: python scripts/_probes/probe_20260922_pl_kr0074_apply.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from scripts.build_pl_breakdown import _GOLD_CELL_OVERRIDE  # noqa: E402

CODE, QUARTER = "KR0074", "2023.4Q"
VIZ = ROOT / "data" / "dart" / "viz" / "pl_breakdown_master.json"
ROOTM = ROOT / "PL_breakdown.json"
DRY = "--dry-run" in sys.argv


def check_identities(v):
    """override 값만으로 닫혀야 하는 항등식. 허용오차 1(백만원, 반올림 누적)."""
    tests = [
        ("2 = 3 + 8", v[2], v[3] + v[8]),
        ("1 = 2 - 16", v[1], v[2] - v[16]),
        ("17 = 18 + 19", v[17], v[18] + v[19]),
        ("20 = 1 + 17", v[20], v[1] + v[17]),
        ("22 = 20 + 21", v[22], v[20] + v[21]),
        ("24 = 22 - 23", v[24], v[22] - v[23]),
    ]
    bad = [(n, a, b) for n, a, b in tests if abs(a - b) > 1.0]
    for n, a, b in tests:
        print(f"    {'OK ' if abs(a - b) <= 1.0 else 'FAIL'} {n:<14} {a:>12,.0f} vs {b:>12,.0f}")
    return bad


def apply(path):
    rows = json.loads(path.read_text(encoding="utf-8"))
    before = len(rows)
    ov = _GOLD_CELL_OVERRIDE[(CODE, QUARTER)]
    filled, skipped, absent = [], [], []
    idx = {}
    for r in rows:
        if r.get("원보험사코드") == CODE and r.get("공시분기") == QUARTER:
            idx[int(r["항목번호"])] = r
    for item, val in sorted(ov.items()):
        r = idx.get(item)
        if r is None:
            absent.append(item)
            continue
        if r.get("값") is not None:
            skipped.append((item, r["값"]))
            continue
        r["값"] = float(val)
        filled.append(item)
    print(f"  {path.name}: 행 {before} · 채움 {len(filled)} {filled} · "
          f"기존값유지 {len(skipped)} {[i for i, _ in skipped]} · 행없음 {absent}")
    if absent:
        sys.exit(f"REFUSE: {path.name} 에 항목 {absent} 행이 없다 — 행 추가는 이 스크립트 범위 밖")
    if len(rows) != before:
        sys.exit("REFUSE: 행 수가 바뀌었다")
    if not DRY:
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return filled


def main():
    ov = _GOLD_CELL_OVERRIDE[(CODE, QUARTER)]
    print(f"{CODE} {QUARTER} override {len(ov)}칸 — 항등식 검산")
    bad = check_identities(ov)
    if bad:
        sys.exit(f"REFUSE: 항등식 {len(bad)}건 불성립 {bad}")
    print()
    for p in (VIZ, ROOTM):
        apply(p)
    print("\n(dry-run: 파일 안 씀)" if DRY else "\nwrote both files")


main()
