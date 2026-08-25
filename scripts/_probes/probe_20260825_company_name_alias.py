# -*- coding: utf-8 -*-
"""회사명 표기 차이 전수 — census 를 걸기 전에 별칭을 확정한다.

마스터는 (원보험사코드, 원수사명) 을 갖지만 viz 파일들은 이름만 갖는다. 이름 표기가
파일마다 달라(미래에셋생명 vs 미래에셋생명보험) 순진한 census 는 오탐을 낸다.
여기서 전 파일의 이름 집합을 뽑고 코드에 붙일 수 있는지 확인한다.

사용: python scripts/_probes/probe_20260825_company_name_alias.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def j(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def main() -> int:
    code_name = {}
    for rel in ("CSM_waterfall.json", "PL_breakdown.json", "IFRS17_BS.json"):
        for r in j(rel):
            c = r.get("원보험사코드")
            n = r.get("원수사명")
            if c and n:
                code_name.setdefault(c, set()).add(n)
    print(f"마스터 코드 {len(code_name)}개")
    multi = {c: v for c, v in code_name.items() if len(v) > 1}
    print(f"  같은 코드에 이름 2개 이상: {len(multi)}")
    for c, v in sorted(multi.items()):
        print(f"    {c}: {sorted(v)}")

    master_names = {n for v in code_name.values() for n in v}
    name_code = {}
    for c, v in code_name.items():
        for n in v:
            name_code[n] = c

    viz_names = {}
    for label, rel, path in [
        ("amort", "data/dart/viz/csm_amort_schedule.json", "companies"),
        ("history", "data/dart/viz/csm_waterfall_history.json", "companies"),
        ("ins_pl", "data/dart/viz/insurance_pl_breakdown.json", "companies"),
        ("viz_wf", "data/dart/viz/csm_waterfall.json", None),
    ]:
        d = j(rel)
        if path:
            names = {c["company"] for c in d[path]}
        else:
            names = {c.get("company") for c in (d.get("companies") or [])} if isinstance(d, dict) else set()
        viz_names[label] = names
        unknown = sorted(n for n in names if n not in name_code)
        print(f"\n[{label}] {len(names)}개, 마스터명과 불일치 {len(unknown)}")
        for n in unknown:
            # 접두 매칭 후보
            cands = sorted(m for m in master_names if m.startswith(n[:3]) or n.startswith(m[:3]))
            print(f"    {n:24s} -> 후보 {cands}")

    nb = j("NB_CSM_multiple.json")
    nb_codes = {r["원보험사코드"] for r in nb}
    print(f"\n[NB_CSM_multiple] 코드 보유 O — codes={len(nb_codes)}, "
          f"마스터에 없는 코드={sorted(nb_codes - set(code_name))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
