# -*- coding: utf-8 -*-
"""커버리지 스윕 결과를 **분기별·룰별로 분해**한다 (read-only).

`probe_20260825_coverage_equivalence.py --out X.json` 산출을 읽어, 쳐내기로
**눈머는 버킷이 어디에 몰리는지**를 본다. 특히 확인할 것:

  · `validate_data_contract.check_census` 는 RED/YELLOW 를 **표시 7분기로 스코프**한다
    (`_DISPLAY_QUARTERS`). CHECK 5 는 2023.* 만 건너뛰고 나머지를 전부 본다.
  · 따라서 **2024.1Q·2024.2Q·2024.3Q·2026.2Q** 는 census 가 안 보고 CHECK 5 만 보던
    구간이다 — 쳐내면 그 버킷이 눈멀 수 있다. 그 크기를 여기서 잰다.

사용: probe_20260825_sweep_breakdown.py cov_before.json [cov_after.json]
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DISPLAY = {"2023.4Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"}
PRUNED = {"ANOMALY_PEER_OUTLIER", "ANOMALY_COHORT_ZERO"}


def main() -> int:
    before = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    after = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")) if len(sys.argv) > 2 else None

    sw = before["sweep_pl_csm"]
    print("=" * 78)
    print("SWEEP A — 분기별 반응 (현행 vs 쳐낸 뒤 모의)")
    print("=" * 78)
    per_q: dict = defaultdict(lambda: Counter())
    dark: list = []
    for key, v in sw.items():
        co, q = key.rsplit("|", 1)
        c = per_q[q]
        c["buckets"] += 1
        c["reacts"] += bool(v["reacts"])
        c["reacts_pruned"] += bool(v.get("reacts_sim_pruned"))
        if v["reacts"] and not v.get("reacts_sim_pruned"):
            c["dark"] += 1
            dark.append((q, co, v["rules"]))
    print(f"{'분기':9s} {'표시':4s} {'버킷':>5s} {'반응':>5s} {'쳐낸뒤':>6s} {'눈멈':>5s}")
    for q in sorted(per_q):
        c = per_q[q]
        print(f"{q:9s} {'O' if q in DISPLAY else 'X':4s} {c['buckets']:5d} "
              f"{c['reacts']:5d} {c['reacts_pruned']:6d} {c['dark']:5d}")
    tot_dark = sum(c["dark"] for c in per_q.values())
    print(f"\n눈머는 버킷 총계: {tot_dark}")
    if dark:
        print("  (표시분기 여부 · 회사 · 현행 반응룰)")
        for q, co, rules in dark[:25]:
            only_pruned = set(rules) <= PRUNED
            print(f"   {'표시' if q in DISPLAY else '비표시'} {q} {co}  "
                  f"rules={rules}{'  ← 쳐낸 룰만' if only_pruned else ''}")
        if len(dark) > 25:
            print(f"   ...+{len(dark)-25}")

    print()
    print("=" * 78)
    print("SWEEP A — 어떤 룰이 반응하나 (현행)")
    print("=" * 78)
    rc: Counter = Counter()
    for v in sw.values():
        rc.update(v["rules"])
    for rule, n in rc.most_common(20):
        print(f"  {n:5d}  {rule}{'   ← 이번에 쳐냄' if rule in PRUNED else ''}")

    b = before.get("sweep_kics", {})
    if b:
        print()
        print("=" * 78)
        print("SWEEP B — kics 항목x컬럼")
        print("=" * 78)
        react = sum(1 for v in b.values() if v["reacts"])
        pruned_react = sum(1 for v in b.values() if v.get("reacts_sim_pruned"))
        blind = sorted(k for k, v in b.items() if not v["reacts"])
        print(f"  표적 {len(b)} · 반응 {react} · 쳐낸 뒤 {pruned_react}")
        print(f"  무반응(사각) {len(blind)}: {blind}")
        lost = [k for k, v in b.items() if v["reacts"] and not v.get("reacts_sim_pruned")]
        print(f"  쳐내기로 눈머는 표적: {len(lost)} {lost}")

    print()
    print(f"대조군: {before.get('controls')}")
    if after:
        print(f"after 대조군: {after.get('controls')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
