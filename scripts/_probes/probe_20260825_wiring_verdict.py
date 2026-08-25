# -*- coding: utf-8 -*-
"""최종 판정: 라이브가 fetch 하는 파일 × 런타임 추적으로 확인한 검사기 READ.

입력: _trace_validator_reads_out.json (런타임 정본) + _gate_file_wiring_census_out.json (HTML fetch)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "scripts" / "_probes"


def main() -> int:
    trace = json.loads((P / "_trace_validator_reads_out.json").read_text(encoding="utf-8"))
    census = json.loads((P / "_gate_file_wiring_census_out.json").read_text(encoding="utf-8"))

    reader_of: dict[str, list[str]] = {}
    for name, d in trace.items():
        for f in d.get("reads", []):
            if f.endswith(".json"):
                reader_of.setdefault(f, []).append(name)

    fetched: set[str] = set()
    for v in census["fetches"].values():
        fetched |= set(v)

    print("=" * 82)
    print("라이브 fetch .json × 런타임 READ 하는 검사기 (정본)")
    print("=" * 82)
    unread = []
    for f in sorted(fetched):
        rd = sorted(set(reader_of.get(f, [])))
        if not rd:
            unread.append(f)
        print(f"  {'UNREAD' if not rd else 'ok    '} {f:46s} {rd or '-'}")
    print(f"\n  fetched={len(fetched)}  UNREAD={len(unread)}")
    for f in unread:
        print(f"     -> {f}")

    # 배포본 vs 중간산출물 짝 (같은 개념의 두 파일)
    print("\n" + "=" * 82)
    print("배포본 vs 중간산출물 — 검사기가 어느 쪽을 읽는가")
    print("=" * 82)
    pairs = [("PL_breakdown.json", "data/dart/viz/pl_breakdown_master.json"),
             ("CSM_waterfall.json", "data/dart/viz/csm_waterfall.json"),
             ("NB_CSM_multiple.json", "data/ir/nb_csm_ratio.json")]
    for dep, mid in pairs:
        rd_dep = sorted(set(reader_of.get(dep, [])))
        rd_mid = sorted(set(reader_of.get(mid, [])))
        print(f"\n  배포본  {dep:34s} R={rd_dep or '-'}")
        print(f"  중간산출 {mid:34s} R={rd_mid or '-'}")
        only_mid = sorted(set(rd_mid) - set(rd_dep))
        if only_mid:
            print(f"  !! 중간산출물만 읽는 검사기: {only_mid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
