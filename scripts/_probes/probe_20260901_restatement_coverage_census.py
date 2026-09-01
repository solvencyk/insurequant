# -*- coding: utf-8 -*-
"""재작성 탐지기의 **커버리지 census** — '비교 안 된 칸' 을 회사x항목으로 전부 센다.

`CLEAN` 은 '그 칸을 봤는데 같았다' 일 때만 의미가 있다. 순회조차 안 된 칸을 CLEAN 에
섞으면 그게 바로 이 저장소가 반복해서 데인 false-green 이다. 그래서 미비교 칸을
두 종류로 가른다:
  · SOURCE_DASH  — 마스터도 그 (회사,분기,항목)을 안 갖고 있다 = 원문이 '-' 다(정상)
  · EXTRACT_GAP  — 마스터는 값을 갖고 있는데 우리 추출이 그 행을 못 잡았다(진짜 구멍)
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("d", ROOT / "scripts" / "detect_kics_restatement.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def main():
    mv, names = d.load_master()
    codes = sorted({c for (c, _q) in mv})
    tot_cmp = tot_dash = tot_gap = 0
    gaps = []
    for code in codes:
        cur, _s1, _m1, e1 = d.extract("FY2026_Q2", code, "prev")
        pri, _s2, _m2, e2 = d.extract("FY2026_Q1", code, "cur")
        if cur is None or pri is None:
            print(f"{code} UNCOVERED {e1} {e2}")
            continue
        m1 = mv.get((code, "2026.1Q"), {})
        m2 = mv.get((code, "2026.2Q"), {})
        c_dash, c_gap, c_cmp = [], [], 0
        for it in range(1, 28):
            if it in d.DERIVED_ITEMS:
                continue
            a = cur.get(it, (None, 0))[0]
            b = pri.get(it, (None, 0))[0]
            if a is not None and b is not None:
                c_cmp += 1
                continue
            mval1, mval2 = m1.get(it), m2.get(it)
            has_master = any(isinstance(x, (int, float)) or
                             (isinstance(x, str) and x.strip() not in ("", "-"))
                             for x in (mval1, mval2))
            (c_gap if has_master else c_dash).append(
                (it, "q2본직전" if a is None else "", "q1본해당" if b is None else "",
                 mval1, mval2))
        tot_cmp += c_cmp
        tot_dash += len(c_dash)
        tot_gap += len(c_gap)
        flag = "  <<< GAP" if c_gap else ""
        print(f"{code:8s} {(names.get(code) or '')[:22]:22s} cmp={c_cmp:2d} "
              f"dash={len(c_dash):2d} gap={len(c_gap):2d}{flag}")
        for g in c_gap:
            gaps.append((code, names.get(code), *g))
            print(f"         GAP item{g[0]:<3d} missing_in=[{g[1]} {g[2]}] "
                  f"master1Q={g[3]!r} master2Q={g[4]!r}")
    print()
    print(f"TOTAL compared={tot_cmp}  source_dash={tot_dash}  EXTRACT_GAP={tot_gap}")
    print(f"기대 그리드 = {len(codes)}사 x 26항목 = {len(codes)*26}칸")
    Path(sys.argv[1]).write_text(json.dumps(
        {"compared": tot_cmp, "dash": tot_dash, "gap": tot_gap, "gaps": gaps},
        ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
