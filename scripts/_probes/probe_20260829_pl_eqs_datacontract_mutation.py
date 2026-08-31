# -*- coding: utf-8 -*-
"""CONSTRUCTIVE 변이를 **data-contract 게이트 전체**(push 를 실제로 막는 게이트)에 물린다.

probe_20260829_pl_eqs_mutation.py 는 validate_master_tables 의 두 룰만 봤다. 여기서는
scripts/validate_data_contract.py 의 run_gate() 를 통째로 돌려 **RED 이 하나라도 늘어나는지**
를 센다. 안 늘면 그 항목의 상류 오추출은 push 를 막는 어떤 룰에도 안 걸린다.

디스크를 건드리지 않는다 — Env(inject={"pl": ...}) 로 메모리 사본만 주입한다.
"""
from __future__ import annotations

import copy
import io
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import validate_data_contract as G  # noqa: E402
import validate_master_tables as V  # noqa: E402

from probe_20260829_pl_eqs_mutation import CASES, N, perturb, rederive  # noqa: E402


def reds(pl):
    buf = io.StringIO()
    with redirect_stdout(buf):
        env = G.Env(inject={"pl": pl})
        res = G.run_gate(env)
    return {(f.rule, f.company, f.quarter) for f in res.red}


def main():
    base_pl = V.load_long(V.PL_PATH)
    t0 = time.time()
    base = reds(copy.deepcopy(base_pl))
    print(f"baseline RED = {len(base)}  ({time.time()-t0:.1f}s / run)")
    print()
    print(f"{'mutation (CONSTRUCTIVE)':<34} {'buckets':>7} {'new RED':>8} {'det%':>7}  rules")
    print("-" * 100)
    for desc, item, downstream in CASES:
        key = N[item]
        pl = copy.deepcopy(base_pl)
        t = 0
        for (co, q), m in pl.items():
            if m.get(key) is None:
                continue
            t += 1
            m[key] = perturb(m[key])
            rederive(m, downstream)
        new = reds(pl) - base
        hit = {(c, q) for _r, c, q in new}
        rules = sorted({r for r, _c, _q in new})
        print(f"{desc:<34} {t:>7} {len(new):>8} {100.0*len(hit)/t if t else 0:>6.1f}%  "
              f"{', '.join(rules)[:60]}")


if __name__ == "__main__":
    main()
