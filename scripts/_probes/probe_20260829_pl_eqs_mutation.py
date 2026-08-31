# -*- coding: utf-8 -*-
"""PL_EQS 변이시험 (조사 전용, 마스터를 쓰지 않는다 — 메모리 사본만 흔든다).

두 모드로 같은 상류 오류를 주입한다.

  NAIVE        : 마스터의 그 셀 하나만 흔든다.
                 "이미 발행된 마스터가 한 칸 오염됐을 때 게이트가 잡는가"
  CONSTRUCTIVE : 같은 셀을 흔들고, **빌더가 그 셀로부터 계산하는 하류 항을
                 빌더와 똑같이 다시 계산한다.**
                 "파서가 상류에서 잘못 뽑았을 때 게이트가 잡는가" — 실제로 일어나는 형태.

CONSTRUCTIVE 에서 안 잡히면 그 등식은 그 축을 못 본다.

빌더의 plug (근거: scripts/build_pl_breakdown.py assemble(), scripts/fetch_dart_fs.py _parse()):
  item7  = 3 - (4+5+6)          build_pl_breakdown.py L166-174
  item12 = 8 - (9+10+11)        build_pl_breakdown.py L198-202
  item2  = 3 + 8   (v[2] None)  build_pl_breakdown.py L204-205
  item18 = 17 - 19              build_pl_breakdown.py L213-215 + fetch_dart_fs.py L403-404
  item23 = 22 - 24  (무조건)     build_pl_breakdown.py L226-228
  item21 = 22 - 20              fetch_dart_fs.py L392-394 (+ build L232-234)
  item20 = 1 + 17  (v[20] None) build_pl_breakdown.py L216-217
  item22 = 20 + 21 (v[22] None) build_pl_breakdown.py L219-220
"""
from __future__ import annotations

import copy
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import validate_master_tables as V  # noqa: E402

N = {1: "보험손익", 2: "생명장기손익", 3: "생명장기원수손익", 4: "원수CSM상각",
     5: "원수위험조정변동", 6: "원수예실차", 7: "기타생명장기원수손익",
     8: "생명장기재보험손익", 9: "재보험CSM상각", 10: "재보험위험조정변동",
     11: "재보험예실차", 12: "기타생명장기재보험손익", 13: "자동차손익", 14: "일반손익",
     15: "기타영업수익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익",
     19: "보험금융손익", 20: "영업이익", 21: "영업외손익", 22: "세전이익",
     23: "법인세", 24: "당기순이익", 25: "기타포괄손익", 31: "총포괄손익"}


def run_gate(pl, extra_lob, unknown_hyphen, wf=None):
    """PL 을 읽는 **차단성(RED) 룰 전부**를 돌린다 — PL_BRIDGE + CSM_AMORT_IDENTITY.
    (coverage census 는 key_items 3개의 결측만 보므로 값 오염에 무반응, 여기선 제외.
     data-contract 의 cohort-zero/peer-outlier 는 YELLOW 라 push 를 막지 않는다.)"""
    buf = io.StringIO()
    with redirect_stdout(buf):
        pb_pass, pb_fail, pb_skip, _z, _zl = V._check_pl_bridge(pl, extra_lob, unknown_hyphen)
        bridge = {(co, q, lab) for co, q, lab, _l, _d in pb_fail}
        amort = set()
        if wf is not None:
            _cp, cc_fail, _cpin, _cs = V._check_csm_crosscheck(pl, wf)
            amort = {(co, q, "CSM_AMORT_IDENTITY") for co, q, *_r in cc_fail}
    return pb_pass, bridge, amort


def rederive(m, touched):
    """빌더 assemble()/_parse() 와 동일한 순서로 하류 plug 를 다시 계산한다."""
    def g(i):
        return m.get(N[i])

    def setv(i, val):
        m[N[i]] = val

    # item18 = 17 - 19
    if 18 in touched and None not in (g(17), g(19)):
        setv(18, round(g(17) - g(19), 6))
    # item7 = 3 - (4+5+6)
    if 7 in touched and None not in (g(3), g(4), g(5), g(6)):
        setv(7, g(3) - (g(4) + g(5) + g(6)))
    # item12 = 8 - (9+10+11)
    if 12 in touched and None not in (g(8), g(9), g(10), g(11)):
        setv(12, g(8) - (g(9) + g(10) + g(11)))
    # item2 = 3 + 8
    if 2 in touched and None not in (g(3), g(8)):
        setv(2, g(3) + g(8))
    # item21 = 22 - 20
    if 21 in touched and None not in (g(22), g(20)):
        setv(21, round(g(22) - g(20), 6))
    # item23 = 22 - 24
    if 23 in touched and None not in (g(22), g(24)):
        setv(23, round(g(22) - g(24), 6))


# (설명, 흔들 항목번호, CONSTRUCTIVE 에서 다시 계산할 하류 항목)
CASES = [
    ("item4  원수CSM상각 오추출",        4,  {7}),
    ("item5  원수위험조정 오추출",        5,  {7}),
    ("item6  원수예실차 오추출",          6,  {7}),
    ("item9  재보험CSM상각 오추출",       9,  {12}),
    ("item10 재보험위험조정 오추출",      10, {12}),
    ("item11 재보험예실차 오추출",        11, {12}),
    ("item3  생명장기원수손익 오추출",     3,  {7, 2}),
    ("item8  생명장기재보험손익 오추출",   8,  {12, 2}),
    ("item19 보험금융손익 오추출",        19, {18}),
    ("item17 투자손익 오추출",           17, {18}),
    ("item22 세전이익 오추출",           22, {21, 23}),
    ("item24 당기순이익 오추출",          24, {23}),
    ("item20 영업이익 오추출",           20, {21}),
    ("item25 기타포괄손익 오추출",        25, set()),
    ("item23 법인세 오추출(빌더가 덮어씀)", 23, {23}),
]


def perturb(v):
    return v + max(10000.0, 0.30 * abs(v))


def main():
    base_pl = V.load_long(V.PL_PATH)
    wf = V.load_long(V.WF_PATH)
    extra_lob, unknown_hyphen = V.load_pl_extra_lob(V.PL_PATH)
    base_pass, base_bridge, base_amort = run_gate(
        copy.deepcopy(base_pl), extra_lob, unknown_hyphen, wf)
    print(f"baseline: PL_BRIDGE pass={base_pass} fail={len(base_bridge)} · "
          f"CSM_AMORT fail={len(base_amort)} · buckets={len(base_pl)}")
    print()
    hdr = (f"{'mutation':<32} {'buckets':>7} | {'NAIVE det%':>10} "
           f"| {'CONSTRUCTIVE det%':>17} {'bridge':>7} {'amort':>7}")
    print(hdr)
    print("-" * len(hdr))

    for desc, item, downstream in CASES:
        key = N[item]
        # 어느 버킷에 주입 가능한가
        targets = [(co, q) for (co, q), m in base_pl.items() if m.get(key) is not None]
        out = {}
        for mode in ("naive", "constructive"):
            pl = copy.deepcopy(base_pl)
            for co, q in targets:
                m = pl[(co, q)]
                m[key] = perturb(m[key])
                if mode == "constructive":
                    rederive(m, downstream)
            _p, bridge, amort = run_gate(pl, extra_lob, unknown_hyphen, wf)
            nb = {(co, q) for co, q, _l in bridge - base_bridge}
            na = {(co, q) for co, q, _l in amort - base_amort}
            out[mode] = (len(nb | na), len(nb), len(na))
        t = len(targets)
        nall, _nb, _na = out["naive"]
        call, cb, ca = out["constructive"]
        print(f"{desc:<32} {t:>7} | {100.0*nall/t if t else 0:>9.1f}% "
              f"| {100.0*call/t if t else 0:>16.1f}% {cb:>7} {ca:>7}")


if __name__ == "__main__":
    main()
