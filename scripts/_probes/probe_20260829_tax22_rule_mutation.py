# -*- coding: utf-8 -*-
"""2f(TAX22_SOURCE_CROSSCHECK) 변이시험 — **배선이 진짜 검사인지** 확인한다 (읽기 전용).

배선 전 실측(scripts/_probes/probe_20260829_pl_eqs_mutation.py):
  item22 세전이익 오추출  338버킷  NAIVE 100.0%  CONSTRUCTIVE **0.0%**  잡은 룰: 없음

배선 후 같은 주입을 하고 2f 가 몇 건을 잡는지 센다. 주입 크기는 그 변이시험과 동일한
max(10,000백만, |v|×30%) — floor(200백만)의 50배 이상이라 임계 문제가 아니다.

CONSTRUCTIVE 모드는 빌더가 item22 로부터 계산하는 하류(item21 = 22-20, item23 = 22-24)를
빌더와 똑같이 다시 계산한다 — 파서가 틀리면 실제로 일어나는 형태. 2f 의 좌변이 |22-24| 라
item24 는 그대로 두므로 CONSTRUCTIVE 에서도 잔차가 남아야 한다.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import validate_master_tables as V  # noqa: E402


def perturb(v):
    return v + max(10000.0, 0.30 * abs(v))


def main():
    rows = json.loads((ROOT / V.PL_PATH).read_text(encoding="utf-8"))
    base_p, base_f, base_s = V._check_tax22_crosscheck(rows, quiet=True)
    print(f"baseline  pass={base_p} fail={len(base_f)} skip={sum(base_s.values())}  {base_s}")

    for mode in ("naive", "constructive"):
        mut = copy.deepcopy(rows)
        # (co,q) -> {항목명: index}
        idx = {}
        for i, r in enumerate(mut):
            idx.setdefault((r["원수사명"], r["공시분기"]), {})[V.norm(r["항목명"])] = i
        n_touch = 0
        for k, names in idx.items():
            i22 = names.get("세전이익")
            if i22 is None or mut[i22]["값"] is None:
                continue
            old22 = mut[i22]["값"]
            new22 = perturb(old22)
            mut[i22]["값"] = new22
            n_touch += 1
            if mode == "constructive":
                # 빌더가 item22 로부터 계산하는 하류 두 항을 같은 식으로 다시 만든다
                i20, i21, i23, i24 = (names.get("영업이익"), names.get("영업외손익"),
                                      names.get("법인세"), names.get("당기순이익"))
                if i21 is not None and i20 is not None and mut[i20]["값"] is not None:
                    mut[i21]["값"] = round(new22 - mut[i20]["값"], 6)
                if i23 is not None and i24 is not None and mut[i24]["값"] is not None:
                    mut[i23]["값"] = round(new22 - mut[i24]["값"], 6)
        p, f, s = V._check_tax22_crosscheck(mut, quiet=True)
        newf = len(f) - len(base_f)
        cmp_n = p + len(f)
        print(f"{mode:<13s}  주입 {n_touch}건 · 대조가능 {cmp_n}  "
              f"-> pass={p} fail={len(f)} (신규 FAIL {newf})  탐지율 "
              f"{100.0 * newf / cmp_n if cmp_n else 0:.1f}%")


if __name__ == "__main__":
    main()
