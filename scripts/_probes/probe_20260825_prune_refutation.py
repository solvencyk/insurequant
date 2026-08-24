# -*- coding: utf-8 -*-
"""휴리스틱 룰 쳐내기(2026-08-25) **반증 실측** — read-only.

각 후보 룰이 "지우면 무엇을 잃는가" 를 숫자로 잰다. 쳐내기 전에 반드시 돌린다.

  (b) 텍스트밀도 판독성: `_source_readability` 를 빈 맵으로 바꾸면 '판정불가(unverifiable)'
      로 세어지던 칸이 몇 개나 '구조적으로 정당' 버킷으로 넘어가는가.
  (c) 축 평가율 / 동어반복: 실데이터에서 현재 몇 건 발화하는가(비용) 와
      임계를 흔들면 발화하는가(살아있는 검사인가).
  (d) 일반 이상치 스캐너(CHECK 5): 몇 건을 만들고, 그것이 data_contract YELLOW 의 몇 % 인가.
"""
from __future__ import annotations

import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_data_contract as dc          # noqa: E402
import validate_kics_disclosure as kg        # noqa: E402


def main() -> int:
    records = kg._load_records(ROOT / "kics_disclosure.json")

    print("=" * 74)
    print("(b) 텍스트밀도 판독성 — 죽이면 몇 칸이 '정당' 으로 넘어가나")
    print("=" * 74)
    real = kg._source_readability()
    print(f"  사이드카 상태분포: {Counter(real.values())}")
    for label, rmap in (("현행(밀도 사이드카 사용)", real), ("밀도 휴리스틱 제거(빈 맵)", {})):
        mm, submissing, skipped, unver = kg._transition_mmult_after(records, rmap)
        print(f"  {label}:")
        print(f"      mmult 불일치      = {len(mm)}")
        print(f"      판정불가(unverifiable) = {len(unver)}")
        print(f"      세부결측 집계     = {sum(submissing.values()) if hasattr(submissing,'values') else submissing}")
    print("  → 판정불가 칸이 0 이 되면 그 칸들은 '구조적으로 정당' 으로 재분류된다"
          " (= 무검사 통과). 원장(kics_source_vision_verified.json)은 이 칸에만 붙으므로"
          " 밀도 휴리스틱을 죽이면 원장도 같이 죽는다.")

    print()
    print("=" * 74)
    print("(c) 축 평가율 / 동어반복 — 현재 비용과 살아있음 여부")
    print("=" * 74)
    ac = kg._axis_evaluation_census(records)
    ared, arev = kg._axis_eval_findings(ac)
    print(f"  현재 발화: AXIS_NOT_EVALUATED={len(ared)}  AXIS_EVAL_RATE_LOW={len(arev)}"
          f"  (축 census 행 {len(ac)}개)")
    # 살아있음: 바닥을 100% 로 올리면 전 축이 review 로 떠야 한다(탐지기가 죽지 않았음)
    _floor = kg._AXIS_EVAL_RATE_FLOOR
    try:
        kg._AXIS_EVAL_RATE_FLOOR = 1.01
        _r2, rev2 = kg._axis_eval_findings(ac)
    finally:
        kg._AXIS_EVAL_RATE_FLOOR = _floor
    print(f"  음성대조군(바닥 101%): AXIS_EVAL_RATE_LOW={len(rev2)}"
          f"  → {'살아있음' if rev2 else '★죽은 검사★'}")
    # 실질평가 0 을 강제로 만들어 RED 가 뜨는지
    fake = [dict(r, effective=0) for r in ac if r["grid"] >= kg._AXIS_MIN_GRID][:3]
    r3, _ = kg._axis_eval_findings(fake)
    print(f"  음성대조군(effective=0 강제 3축): AXIS_NOT_EVALUATED={len(r3)}"
          f"  → {'살아있음' if r3 else '★죽은 검사★'}")

    tc, tskip = kg._identity_tautology_census(records)
    tred, texempt, trev = kg._identity_tautology_findings(tc)
    print(f"  IDENTITY_TAUTOLOGY: census축={len(tc)} RED={len(tred)} EXEMPT={len(texempt)}"
          f" REVIEW={len(trev)}")
    hot = sorted(tc, key=lambda r: -(r.get("excess") or 0))[:6]
    for r in hot:
        print(f"      {r['axis']:24s}[{r['column']}] n={r.get('n'):4} zero={r.get('zero')}"
              f" excess={r.get('excess')} z={r.get('z')}")

    print()
    print("=" * 74)
    print("(d) CHECK 5 일반 이상치 스캐너 — 비용")
    print("=" * 74)
    env = dc.Env()
    t0 = time.perf_counter()
    probe = dc.GateResult()
    dc.check_generic_anomalies(probe, env)
    t1 = time.perf_counter()
    print(f"  CHECK5 단독: YELLOW={len(probe.yellow)} RED={len(probe.red)}  ({t1-t0:.2f}s)")
    print(f"  룰별: {Counter(getattr(f,'rule',None) for f in probe.yellow)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
