#!/usr/bin/env python3
"""병합 후 `validate_master_tables` PL_BRIDGE 신규 실패 153건의 계보 진단 (2026-09-20, parser/ifrs17).

**읽기전용.** 마스터·사이드카·등재부를 한 바이트도 쓰지 않는다.

묻는 것: 경영공시 백필 155셀을 병합하자 `보험손익(leg-coverage)` 등식이 153건 새로 깨졌다.
이게 데이터 결함인가, 아니면 룰이 소스를 안 가리는 것인가?

leg-coverage 는 결측 LOB 다리를 **0 으로 채워** `item1 = 2+13+14(+15-16)` 을 검산한다
(validate_master_tables.py L1046~). 경영공시 §2-1 요약 포괄손익계산서는 LOB 분해를 **싣지
않으므로**(같은 파일 L55~ `PL_DISCLOSURE_ITEM_NOS = (1,16,22,23,24)`) 그 셀의 2/13/14 는
"추출 실패"가 아니라 **원천 부재**다. 0-fill 하면 우변이 0 이 되어 잔차 = item1 전액이 된다 —
즉 실패가 아니라 **검산 불가(NOT_TESTABLE)** 다.

같은 문제를 `coverage_holes` 는 2026-09-20 에 이미 소스인식으로 풀었다
(`pl_key_items_for(pl_cell_source_ids())`). leg-coverage(2e) · ZERO_LEGS(2b) 는 그 배선에서 빠졌다.

실행:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
        scripts/_probes/_probe_20260920_pl_bridge_after_merge.py
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import validate_master_tables as V  # noqa: E402


def main():
    pl = V.load_long(V.PL_PATH)
    src = V.pl_cell_source_ids()
    extra, unknown = V.load_pl_extra_lob(V.PL_PATH)
    with contextlib.redirect_stdout(io.StringIO()):      # 게이트 인쇄는 삼킨다
        pb_pass, pb_fail, pb_skip, zleg_rows, zerolegs_rows = V._check_pl_bridge(
            pl, extra, unknown, {})
    base = V._pl_bridge_baseline().get("entries", {})

    print("=" * 78)
    print("1. 계보 census (사이드카 기준) · PL_BRIDGE 집계")
    print("=" * 78)
    print("   계보:", dict(Counter(src.values())))
    print(f"   pass={pb_pass} fail={len(pb_fail)} skip={pb_skip} "
          f"zero_legs={len(zleg_rows)} impossible0={len(zerolegs_rows)}")
    ids = {V._pl_fail_id(r) for r in pb_fail}
    new = sorted(i for i in ids if i not in base)
    stale = sorted(i for i in base if i not in ids)
    print(f"   baseline: 기지={len(ids) - len(new)} 신규={len(new)} 등재부에만={len(stale)}")
    print()

    print("=" * 78)
    print(f"2. 신규 실패 {len(new)}건의 계보 — 전부 DISCLOSURE 인가?")
    print("=" * 78)
    by_src, by_label = Counter(), Counter()
    exact_all_legs_zero = 0
    for row in pb_fail:
        co, q, label, lhs, diff = row[0], row[1], row[2], row[3], row[4]
        if V._pl_fail_id(row) not in new:
            continue
        s = src.get((co, q)) or "UNKNOWN"
        by_src[s] += 1
        by_label[label] += 1
        if s == V.PL_DISCLOSURE_SOURCE_ID and abs(abs(diff) - abs(lhs)) < 0.51:
            exact_all_legs_zero += 1
    print("   계보별:", dict(by_src))
    print("   등식별:", dict(by_label))
    print(f"   DISCLOSURE 신규실패 중 '잔차 절대값 == item1 절대값'(우변 통째 0) = "
          f"{exact_all_legs_zero} / {by_src.get(V.PL_DISCLOSURE_SOURCE_ID, 0)}")
    print()

    print("=" * 78)
    print("3. 병합 155셀 중 leg-coverage 신규실패에 안 걸린 셀")
    print("=" * 78)
    merged = {k for k, v in src.items() if v == V.PL_DISCLOSURE_SOURCE_ID}
    hit = {(r[0], r[1]) for r in pb_fail
           if V._pl_fail_id(r) in new and r[2] == "보험손익(leg-coverage)"}
    for k in sorted(merged - hit):
        m = pl.get(k, {})
        print(f"   {k}  보험손익={m.get('보험손익')} 생명장기손익={m.get('생명장기손익')} "
              f"자동차손익={m.get('자동차손익')} 일반손익={m.get('일반손익')} "
              f"기타사업비용={m.get('기타사업비용')}")
    print()

    print("=" * 78)
    print("4. ZERO_LEGS(2b) 도 같은 원인인가")
    print("=" * 78)
    zsrc = Counter(src.get((r[0], r[1])) or "UNKNOWN" for r in zleg_rows)
    print("   zero_legs 계보별:", dict(zsrc))
    print()

    print("=" * 78)
    print("5. 등재부에만 남은 것 (parser 가 고쳐서 이제 안 깨지는 줄 — 지워야 한다)")
    print("=" * 78)
    for i in stale:
        print("   STALE:", i, "->", base.get(i))
    print()


if __name__ == "__main__":
    main()
