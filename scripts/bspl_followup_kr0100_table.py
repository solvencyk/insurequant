#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 4: the final side-by-side table of KR0100 (처브라이프) BS item 20 under both definitions.

D1  일반계정 보험계약부채 (the '보험계약부채' line of the supervisory 8-1)      SA  특별계정부채        D2 = D1 + SA
K   K-IFRS 보험계약부채 line of the audited year-end statements / the 2026 K-form interim statements (includes the variable-contract
    special-account liabilities; the K-IFRS statement has no 특별계정부채 line)
Numbers = printed amounts (원 -> 백만원) with the PDF page of every figure.  Where the table reader already produced the same figure
(bspl_followup_kr0100_item20.py -> kr0100_item20_definitions.json) the literal is asserted equal to it; the few figures it could not reach
(2023.1Q / 2023.3Q special account, which sit in an 8-1 whose label the canonicaliser rejects) were read from the page text.
Output: data/_derived/bspl_followup_20261011/kr0100_item20_table.json (+ printed markdown).  Read-only on the masters.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
W = ROOT / "data" / "_derived" / "bspl_followup_20261011"

# quarter: dict(D1, SA, K, src) -- 백만원; src = where each figure is printed
T = {
    "2023.1Q": dict(D1=846016.693679, SA=319040.371000, K=None, src="경영공시 2023.1Q 8-1 p10 (보험계약부채 · IV.특별계정부채)"),
    "2023.2Q": dict(D1=836476.647018, SA=319664.747532, K=None, src="경영공시 2023.2Q 8-1 p44 (보험계약부채) · p45 (특별계정부채)"),
    "2023.3Q": dict(D1=815336.273433, SA=307625.565257, K=None, src="경영공시 2023.3Q 8-1 p10 (1.보험계약부채 · IV.특별계정부채)"),
    "2023.4Q": dict(D1=906447.518062, SA=317390.401922, K=1222488.069199,
                    src="K = FY2023 감사 재무상태표 p80 보험계약부채; D1·SA = 2024.3Q 경영공시 8-1 p25·p30 의 전기말(2023.12.31) 열"),
    "2024.1Q": dict(D1=921654.878542, SA=317631.464243, K=None, src="경영공시 2024.1Q 8-1 p14 (보험계약부채 · 특별계정부채)"),
    "2024.2Q": dict(D1=957919.799083, SA=316541.318851, K=None, src="경영공시 2024.2Q 8-1 p56 (보험계약부채 · 특별계정부채)"),
    "2024.3Q": dict(D1=1001261.488868, SA=298931.010670, K=None, src="경영공시 2024.3Q 8-1 p29 (보험계약부채) · p30 (특별계정부채)"),
    "2024.4Q": dict(D1=1013938.851959, SA=287450.244385, K=1300423.982208,
                    src="K = FY2024 감사 재무상태표 p98 보험계약부채; D1·SA = 2025.1Q 경영공시 8-1 p28 의 전기말(2024.12.31) 열"),
    "2025.1Q": dict(D1=1071724.928099, SA=288894.240196, K=None, src="경영공시 2025.1Q 8-1 p28"),
    "2025.2Q": dict(D1=1056278.135300, SA=315683.776384, K=None, src="경영공시 2025.2Q 8-1 p56"),
    "2025.3Q": dict(D1=1055839.071905, SA=325812.255773, K=None, src="경영공시 2025.3Q 8-1 p28"),
    "2025.4Q": dict(D1=None, SA=None, K=1335767.369078, src="K = 2026.1Q 8-1 p25 / 2026.2Q 8-1 p55 의 전기말(2025.12.31) 열 (FY2025 경영공시 PDF 는 재무제표를 첨부로만 둠)"),
    "2026.1Q": dict(D1=None, SA=None, K=1275313.916144, src="경영공시 2026.1Q 8-1(K-IFRS 서식) p25"),
    "2026.2Q": dict(D1=None, SA=None, K=1336531.920613, src="경영공시 2026.2Q 8-1(K-IFRS 서식) p55"),
}


def main():
    bsrows = [r for r in json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8")) if r["원보험사코드"] == "KR0100"]
    master = {r["공시분기"]: r["값"] for r in bsrows if r["항목번호"] == 20}
    liab = {r["공시분기"]: r["값"] for r in bsrows if r["항목번호"] == 2}
    reins = {r["공시분기"]: r["값"] for r in bsrows if r["항목번호"] == 21}
    side = json.loads((ROOT / "data" / "_derived" / "bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
    ext = {r["quarter"]: r for r in json.loads((W / "kr0100_item20_definitions.json").read_text(encoding="utf-8"))}
    # assert the literals against the table reader where it has the figure
    for q, t in T.items():
        own = (ext.get(q) or {}).get("from_own_filing") or {}
        for lit, key in (("D1", "D1_보험계약부채"), ("SA", "SA_특별계정부채")):
            if q in ("2023.4Q", "2024.4Q", "2025.4Q", "2026.1Q", "2026.2Q"):
                continue
            v = own.get(key)
            if v is not None and t[lit] is not None:
                assert abs(v / 1.0 - t[lit]) < 0.01, (q, lit, v, t[lit])
    rows = []
    for q, t in T.items():
        d2 = None if (t["D1"] is None or t["SA"] is None) else t["D1"] + t["SA"]
        m = master.get(q)
        holds = None
        if m is not None:
            if t["D1"] is not None and abs(m - t["D1"]) < 0.01:
                holds = "D1(일반계정)"
            elif t["K"] is not None and abs(m - t["K"]) < 0.01:
                holds = "K-IFRS 라인(= D2 근사)"
            else:
                holds = "?"
        k_gap = None if (t["K"] is None or d2 is None) else t["K"] - d2
        L, R = liab.get(q), reins.get(q)
        # 부채총계 - 보험계약부채 - 재보험계약부채: what is left for 기타부채·투자계약부채·차입 ... under each definition
        res_d1 = None if (L is None or R is None or t["D1"] is None) else L - t["D1"] - R
        res_d2 = None if (L is None or R is None or d2 is None) else L - d2 - R
        res_k = None if (L is None or R is None or t["K"] is None) else L - t["K"] - R
        rows.append({"quarter": q, "master": m, "master_source": ("경영공시 사이드카" if f"KR0100|20|{q}" in side else "DART·감사 빌더" if m is not None else None),
                     "master_holds": holds, "D1": t["D1"], "SA": t["SA"], "D2": d2, "K_IFRS_line": t["K"], "K_minus_D2": k_gap,
                     "liab_total_item2": L, "reinsurance_item21": R, "residual_if_D1": res_d1, "residual_if_D2": res_d2, "residual_if_K": res_k,
                     "summary_책임준비금_일반계정_억원정밀도": (ext.get(q) or {}).get("summary_책임준비금_일반계정"), "source": t["src"]})
    OUT = W / "kr0100_item20_table.json"
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    f = lambda x: f"{x:,.3f}" if isinstance(x, (int, float)) else "-"
    print("| 분기 | 마스터 | 마스터 값의 정의 | D1 일반계정 | SA 특별계정부채 | D2 = D1+SA | K-IFRS 라인 | K − D2 | 부채총계−20−21 (D1 가정) | (D2 가정) | (K 가정) |")
    for r in rows:
        print(f"| {r['quarter']} | {f(r['master'])} | {r['master_holds'] or '-'} | {f(r['D1'])} | {f(r['SA'])} | {f(r['D2'])} | {f(r['K_IFRS_line'])} | {f(r['K_minus_D2'])} | {f(r['residual_if_D1'])} | {f(r['residual_if_D2'])} | {f(r['residual_if_K'])} |")


if __name__ == "__main__":
    main()
