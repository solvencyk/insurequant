# -*- coding: utf-8 -*-
"""비표시분기 스팟체크 — 쳐내기로 **눈머는 버킷이 생기나** (read-only).

`check_census` 는 PL/CSM 판정을 표시 7분기(`_DISPLAY_QUARTERS`)로 스코프하는데
CHECK 5 는 2023.* 만 건너뛰고 나머지를 전부 봤다. 따라서 **2024.1Q·2024.2Q·2024.3Q·2026.2Q**
는 "census 는 안 보고 CHECK 5 만 보던" 구간일 수 있다. 전수 스윕이 끝나기 전에
대표 버킷 몇 개로 먼저 확인한다.

사용: probe_20260825_nondisplay_spotcheck.py [분기...]
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_data_contract as dc                              # noqa: E402
from probe_20260825_coverage_equivalence import _shake, dc_fingerprint  # noqa: E402

QUARTERS = sys.argv[1:] or ["2024.2Q", "2024.3Q", "2026.2Q", "2025.2Q"]


def main() -> int:
    env = dc.Env()
    res0 = dc.run_gate(env)
    base, base_np = dc_fingerprint(res0), dc_fingerprint(res0, drop_anomaly=True)
    print(f"BASE findings={len(base)} (CHECK5 제외 {len(base_np)})\n")

    keep_wf, keep_pl = env.wf, env.pl
    for q in QUARTERS:
        bucket = next((b for b in sorted(set(keep_wf) | set(keep_pl)) if b[1] == q), None)
        if bucket is None:
            print(f"{q}: 버킷 없음")
            continue
        wf2, pl2 = copy.deepcopy(keep_wf), copy.deepcopy(keep_pl)
        n = 0
        for d in (wf2, pl2):
            for k, v in list(d.get(bucket, {}).items()):
                nv = _shake(v)
                if nv is not None:
                    d[bucket][k] = nv
                    n += 1
        env.wf, env.pl = wf2, pl2
        try:
            res = dc.run_gate(env)
            full, nop = dc_fingerprint(res), dc_fingerprint(res, drop_anomaly=True)
        finally:
            env.wf, env.pl = keep_wf, keep_pl
        d1, d2 = base ^ full, base_np ^ nop
        disp = "표시" if q in dc._DISPLAY_QUARTERS else "비표시"
        print(f"{q} [{disp}] {bucket[0]} — {n}칸 흔듦")
        print(f"    현행     반응={bool(d1)}  룰={sorted({x[5] for x in d1})}")
        print(f"    쳐낸 뒤  반응={bool(d2)}  룰={sorted({x[5] for x in d2})}")
        if d1 and not d2:
            print("    ★ 눈멈 — 쳐내기로 이 버킷을 보는 룰이 없어진다")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
