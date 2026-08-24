# -*- coding: utf-8 -*-
"""CHECK 5 를 빼면 **어떤 룰도 안 보게 되는 4버킷**을 해부한다 (read-only).

커버리지 스윕(`probe_20260825_coverage_equivalence.py`) 결과:
  · 366버킷 중 **4버킷**이 현행에서는 반응하는데 CHECK 5 를 빼면 무반응이 된다.
  · 반응룰이 `ANOMALY_COHORT_ZERO` · `ANOMALY_PEER_OUTLIER` **둘뿐**이다.
  · 그중 3버킷은 **표시분기**(사이트에 뜨는 분기)다.

왜 산술 룰이 이 버킷을 안 보는지 원인을 본다 — 셀이 없나(census 가 봐야 함),
0 이라 SKIP 되나, 아니면 룰 스코프 밖인가.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_data_contract as dc          # noqa: E402

DARK = [("서울보증보험", "2026.2Q"), ("신한이지손해보험", "2024.4Q"),
        ("신한이지손해보험", "2025.4Q"), ("하나생명보험", "2025.4Q")]


def main() -> int:
    env = dc.Env()
    res = dc.run_gate(env)
    for co, q in DARK:
        disp = "표시" if q in dc._DISPLAY_QUARTERS else "비표시"
        print("=" * 78)
        print(f"{co} {q}  [{disp}]")
        print("=" * 78)
        for master, idx in (("CSM_waterfall", env.wf), ("PL_breakdown", env.pl)):
            m = idx.get((co, q))
            if m is None:
                print(f"  {master}: 버킷 없음")
                continue
            nz = {k: v for k, v in m.items() if v not in (None, "", 0)}
            zero = [k for k, v in m.items() if v == 0]
            missing = [k for k, v in m.items() if v in (None, "")]
            print(f"  {master}: 셀 {len(m)} · nonzero {len(nz)} · 0 {len(zero)} · 결측 {len(missing)}")
            if len(nz) <= 12:
                print(f"      nonzero: {nz}")
            if zero:
                print(f"      0 인 항목({len(zero)}): {zero[:14]}")
            if missing:
                print(f"      결측 항목({len(missing)}): {missing[:14]}")
        hits = [f for f in res.findings if f.company == co and f.quarter == q]
        print(f"  현재 게이트 finding {len(hits)}건: "
              f"{sorted({(f.severity, f.rule) for f in hits})}")
        # 이 버킷을 보는 다른 마스터/축 (kics 등)
        other = [f for f in res.findings if f.company == co and f.quarter != q]
        print(f"  같은 회사 타분기 finding: {len(other)}건 "
              f"{sorted({f.rule for f in other})[:6]}")
    print()
    print("=" * 78)
    print("전체 회사-분기 커버리지: 몇 버킷이 finding 을 하나도 못 받나")
    print("=" * 78)
    all_b = sorted(set(env.wf) | set(env.pl))
    have = {(f.company, f.quarter) for f in res.findings}
    silent = [b for b in all_b if b not in have]
    print(f"  버킷 {len(all_b)} 중 finding 0건 = {len(silent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
