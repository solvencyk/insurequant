# -*- coding: utf-8 -*-
"""4개 '눈머는' 버킷을 **`validate_master_tables` 층**에서도 재측정한다 (read-only).

`probe_20260825_coverage_equivalence.py` 는 `validate_data_contract` + K-ICS 룰엔진만
잰다. 그런데 PL 항등식(브리지)·CSM closing identity·커버리지는 **`validate_master_tables.py`**
에 있고, 그 게이트는 `tests/test_master_tables_golden.py` 를 통해 **push 경로 안에서 돈다**.
즉 스윕이 "눈멈" 이라고 부른 4버킷이 실제로는 그쪽 층이 보고 있을 수 있다.

이 스크립트는 그 4버킷을 in-memory 로 흔들어 `_check_pl_bridge` / `_check_coverage` /
`_check_plausibility` / `_check_csm_crosscheck` 가 반응하는지 본다. **디스크는 안 건드린다**
(`main()` 도 `rebuild_root_masters()` 도 안 부른다 — 후자는 파괴적이다).
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_master_tables as vmt          # noqa: E402
from probe_20260825_coverage_equivalence import _shake   # noqa: E402

DARK = [("서울보증보험", "2026.2Q"), ("신한이지손해보험", "2024.4Q"),
        ("신한이지손해보험", "2025.4Q"), ("하나생명보험", "2025.4Q")]
# 대조군 — 반드시 반응해야 하는 버킷(다른 스윕에서 여러 룰이 반응한 곳)
CONTROL = [("DB생명보험", "2025.2Q"), ("삼성생명보험", "2025.4Q")]


def fingerprint(wf, pl):
    """`validate_master_tables` 의 판정층 지문 (main() 우회 — 디스크 무접촉)."""
    out = []
    n_pl, pl_fail, n_pl2, pl_fail2, pl_missing = vmt._check_pl_bridge(pl)
    out.append(("pl_bridge", n_pl, tuple(map(str, pl_fail)), n_pl2,
                tuple(map(str, pl_fail2)), tuple(map(str, pl_missing))))
    n_cl, cl_fail, n_cl_skip = vmt._check_closing_identity(wf)
    out.append(("closing", n_cl, tuple(map(str, cl_fail)), n_cl_skip))
    cov = vmt._check_coverage(wf, pl)
    out.append(("coverage", tuple(map(str, cov[0])), tuple(map(str, cov[1]))))
    plaus = vmt._check_plausibility(wf)
    out.append(("plausibility", tuple(tuple(map(str, x)) for x in plaus)))
    cross = vmt._check_csm_crosscheck(pl, wf)
    out.append(("crosscheck", str(cross)))
    return tuple(out)


def main() -> int:
    wf = vmt.load_long("CSM_waterfall.json")
    pl = vmt.load_long("PL_breakdown.json")
    base = fingerprint(wf, pl)
    print(f"BASE fingerprint 조각 {len(base)}개\n")

    for label, buckets in (("눈머는 4버킷", DARK), ("대조군(반드시 반응)", CONTROL)):
        print("=" * 78)
        print(label)
        print("=" * 78)
        for b in buckets:
            wf2, pl2 = copy.deepcopy(wf), copy.deepcopy(pl)
            n = 0
            for d in (wf2, pl2):
                for k, v in list(d.get(b, {}).items()):
                    nv = _shake(v)
                    if nv is not None:
                        d[b][k] = float(nv) if not isinstance(nv, float) else nv
                        n += 1
            if n == 0:
                print(f"  {b[0]} {b[1]}: 흔들 셀 0 — 버킷 없음")
                continue
            after = fingerprint(wf2, pl2)
            changed = [base[i][0] for i in range(len(base)) if base[i] != after[i]]
            mark = "반응" if changed else "★무반응★"
            print(f"  {b[0]} {b[1]}: {n}칸 흔듦 → {mark}  {changed}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
