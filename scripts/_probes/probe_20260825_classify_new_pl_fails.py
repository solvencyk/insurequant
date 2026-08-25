# -*- coding: utf-8 -*-
"""소스 재조준으로 **새로 뜬** PL_BRIDGE 실패 전건 분류.

각 실패에 대해:
  · 그 (회사,분기) 키가 배포본에만 있는 신규 키인가 (= 처음 검사받는 셀인가)
  · 방정식 각 항의 값이 viz / 배포본에서 각각 무엇인가
  · 잔차의 성격 (한 항 결측 / 한 항만 다름 / 전부 다름)
를 인쇄한다. "진짜 결함 / 발행사 모순 / 우리 룰 결함 / 유령" 분류의 입력.

사용: python scripts/_probes/probe_20260825_classify_new_pl_fails.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIZ = "data/dart/viz/pl_breakdown_master.json"
DEP = "PL_breakdown.json"


def load_mod():
    spec = importlib.util.spec_from_file_location(
        "vmt", ROOT / "scripts" / "validate_master_tables.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    m = load_mod()
    pl_viz = m.load_long(VIZ)
    pl_dep = m.load_long(DEP)
    wf = m.load_long(m.WF_PATH)

    buf = io.StringIO()
    with redirect_stdout(buf):
        _, fail_viz, _, _, _ = m._check_pl_bridge(pl_viz)
        _, fail_dep, _, _, _ = m._check_pl_bridge(pl_dep)
    sv = {repr(x) for x in fail_viz}
    new = [x for x in fail_dep if repr(x) not in sv]

    eqs = {label: (lhs, rhs) for label, lhs, rhs in m.PL_EQS}

    print(f"새로 뜬 PL_BRIDGE 실패 {len(new)}건\n" + "=" * 88)
    rows = []
    for co, q, label, lhs_v, rhs_v in new:
        key = (co, q)
        new_key = key not in pl_viz
        cells_v = pl_viz.get(key, {})
        cells_d = pl_dep.get(key, {})
        print(f"\n[{co} {q}] {label}")
        print(f"   LHS={lhs_v}  RHS={rhs_v}  잔차={lhs_v - rhs_v:,.1f}")
        print(f"   키가 배포본에만 있는 신규 키? {'YES (처음 검사받음)' if new_key else 'NO'}")
        print(f"   셀수 viz={len(cells_v)}  배포본={len(cells_d)}")
        if label in eqs:
            lhs_k, rhs_terms = eqs[label]
            terms = [(lhs_k, 1)] + list(rhs_terms)
        else:
            terms = []
            # dual-form 보험손익은 PL_EQS 밖 — 관련 항 전부 덤프
            for k in sorted(set(cells_d) | set(cells_v)):
                if any(t in k for t in ("보험손익", "손익", "기타영업수익", "기타사업비용")):
                    terms.append((k, 1))
        diff_terms = []
        for k, _sg in terms:
            a = cells_v.get(k)
            b = cells_d.get(k)
            mark = ""
            if a is None and b is not None:
                mark = "  <== 배포본에만 존재 (처음 검사)"
            elif a is not None and b is None:
                mark = "  <== viz 에만 존재"
            elif a != b:
                mark = f"  <== 값 불일치 (Δ={(b or 0) - (a or 0):,.1f})"
            if mark:
                diff_terms.append(k)
            print(f"     {k:38s} viz={str(a):>14s}  dep={str(b):>14s}{mark}")
        cls = ("신규키-처음검사" if new_key else
               ("항목추가/값변경" if diff_terms else "동일입력-룰경계"))
        print(f"   -> 1차분류: {cls}  (차이난 항: {diff_terms or '없음'})")
        rows.append({"company": co, "quarter": q, "eq": label, "lhs": lhs_v, "rhs": rhs_v,
                     "residual": lhs_v - rhs_v, "new_key": new_key,
                     "diff_terms": diff_terms, "class1": cls})

    out = ROOT / "scripts" / "_probes" / "_classify_new_pl_fails_out.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
