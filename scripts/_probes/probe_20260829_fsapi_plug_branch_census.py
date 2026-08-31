# -*- coding: utf-8 -*-
"""FS-API 캐시 전수로 **plug 분기가 실제로 몇 번 발화하는가** 를 센다 (읽기 전용).

빌더가 등식을 되맞추는 자리는 두 층이다.

  fetch_dart_fs._parse()      L392-394  item21 = item22 - item20   (20·22 둘 다 있으면)
                              L403-404  item18 = item17 - item19
                              L385-390  item17 += item19  (단, `20 = 1+17` 이 닫힐 때만)
  build_pl_breakdown.assemble L213-215  item18 = item17 - item19  (무조건 재계산)
                              L226-228  item23 = item22 - item24  (무조건 재계산)

여기서는 첫 층(원천)을 캐시 1,040개로 전수 확인한다. 두 번째 층은 코드상 무조건이라
셀 수가 아니라 조건문 자체가 근거다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_dart_fs as F  # noqa: E402


def main():
    cache = ROOT / "data" / "dart" / "_fs_api_cache"
    files = sorted(cache.glob("*.json"))
    c = Counter()
    for p in files:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            c["unreadable"] += 1
            continue
        if d.get("status") not in ("000", "013"):
            continue
        annual = p.stem.split("_")[2] == "11011"
        vals = {}
        for a in d.get("list", []):
            if a.get("sj_div") not in ("IS", "CIS"):
                continue
            aid = a.get("account_id") or ""
            raw = a.get("thstrm_amount") if annual else \
                (a.get("thstrm_add_amount") or a.get("thstrm_amount"))
            v = F._to_num(raw)
            if v is not None and aid and aid not in vals:
                vals[aid] = v / 1e6
        if not vals:
            continue
        raw_items = {n: vals.get(aid) for n, aid in F.ACCT.items()}
        if raw_items.get(1) is None and raw_items.get(24) is None:
            continue                      # _parse 가 손익계산서 없음으로 버리는 응답
        c["responses_with_IS"] += 1

        has = {n: raw_items.get(n) is not None for n in F.ACCT}
        # item21: 20·22 둘 다 있으면 무조건 plug (독립 NONOP 계정은 이때 안 쓰인다)
        if has[22] and has[20]:
            c["item21_PLUGGED (22-20) -> EQ6 구성상 참"] += 1
            if vals.get(F.NONOP_INC) is not None or vals.get(F.NONOP_EXP) is not None:
                c["  ...그 중 독립 영업외수익/비용 계정이 실제로 있었는데 안 쓴 건"] += 1
        elif vals.get(F.NONOP_INC) is not None or vals.get(F.NONOP_EXP) is not None:
            c["item21 독립소스(영업외수익-비용) -> EQ6 진짜 검산"] += 1
        else:
            c["item21 없음"] += 1

        # item23: 원천에는 법인세 계정이 있지만 assemble() 이 22-24 로 무조건 덮는다
        if has[23]:
            c["item23 원천 계정 존재(그러나 assemble 이 22-24 로 덮어씀)"] += 1
        if has[22] and has[24]:
            c["item23_PLUGGED (22-24) -> EQ7 구성상 참"] += 1

        # item18 = 17-19
        t1 = F._parse(d, annual)
        if t1 and t1.get(17) is not None and t1.get(19) is not None:
            c["item18_PLUGGED (17-19) -> EQ4 구성상 참"] += 1

        # item17 gross->net 되맞춤(EQ5 를 닫히게 만드는 fit) — _parse L385-390 재현
        r1, r17, r19, r20 = (raw_items.get(1), raw_items.get(17),
                             (t1 or {}).get(19), raw_items.get(20))
        if None not in (r1, r17, r19, r20):
            c["EQ5 대조가능(1·17·19·20 존재)"] += 1
            tol = max(0.01 * abs(r20), 200)
            d_net = abs(r20 - (r1 + r17))
            d_gross = abs(r20 - (r1 + r17 + r19))
            if d_gross <= tol < d_net:
                c["EQ5_FITTED (item17 += item19 로 20=1+17 을 닫아줌)"] += 1
            elif d_net <= tol:
                c["EQ5 원천에서 이미 닫힘(되맞춤 없음)"] += 1
            else:
                c["EQ5 원천에서 안 닫힘(되맞춤도 안 됨 -> 진짜 검산 대상)"] += 1

    print(f"cache files = {len(files)}")
    for k, v in c.most_common():
        print(f"  {v:>6}  {k}")


if __name__ == "__main__":
    main()
