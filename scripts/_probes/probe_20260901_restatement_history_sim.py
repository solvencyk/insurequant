# -*- coding: utf-8 -*-
"""과거 전 분기 시뮬레이션 — 이 축이 과거에 몇 건을 켰을지 센다.

RED/YELLOW 판단의 근거가 된다. 재작성이 흔하면(매 분기 여러 회사) RED 은 배포를 상시
차단하게 되므로 명백히 YELLOW 여야 하고, 드물면(연 1~2건) RED 도 논의 대상이 된다.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import detect_kics_restatement as det      # noqa: E402

DISC = ROOT / "data" / "disclosure"


def main():
    periods = sorted(p.name for p in DISC.iterdir()
                     if re.match(r"FY\d{4}_Q\d$", p.name))
    print("periods:", periods)
    out = {}
    for prior, cur in zip(periods, periods[1:]):
        try:
            r = det.scan(cur, prior)
        except Exception as e:                      # noqa: BLE001
            print(f"{prior} -> {cur}: ERROR {type(e).__name__}: {e}")
            continue
        comp = r["companies"]
        n_re = sum(1 for v in comp.values() if v["status"] == "RESTATED")
        n_cl = sum(1 for v in comp.values() if v["status"] == "CLEAN")
        n_un = sum(1 for v in comp.values() if v["status"] == "UNCOVERED")
        cells = sum(len(v["restated"]) for v in comp.values())
        cmpd = sum(v["compared"] for v in comp.values())
        blind = sum(len(v.get("uncompared") or []) for v in comp.values())
        out[f"{prior}->{cur}"] = {"restated_co": n_re, "clean": n_cl, "uncovered": n_un,
                                  "cells": cells, "compared": cmpd, "blind": blind,
                                  "who": {c: [x["item"] for x in v["restated"]]
                                          for c, v in comp.items() if v["restated"]}}
        print(f"{prior} -> {cur}  재작성사={n_re:2d}  셀={cells:3d}  clean={n_cl:2d} "
              f"uncovered={n_un:2d}  비교칸={cmpd:5d}  사각={blind:3d}")
        for c, v in sorted(comp.items()):
            if v["restated"]:
                print(f"      {c} {v['name']}: items "
                      f"{[x['item'] for x in v['restated']]} "
                      f"maxΔ={max(abs(x['delta']) for x in v['restated']):,.1f}")
    Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                 encoding="utf-8")
    print()
    print("총 재작성 (회사,분기) 버킷 =",
          sum(v["restated_co"] for v in out.values()),
          "| 총 셀 =", sum(v["cells"] for v in out.values()),
          "| 총 미판독사 =", sum(v["uncovered"] for v in out.values()))


if __name__ == "__main__":
    sys.exit(main())
