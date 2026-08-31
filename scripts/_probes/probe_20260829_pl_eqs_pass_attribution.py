# -*- coding: utf-8 -*-
"""PL_BRIDGE 의 `pass=3057` 을 등식별로 쪼개고, 각 pass 를 **구성상 참 / 진짜 검산** 으로
귀속한다. 게이트와 동일한 허용오차를 쓴다."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_master_tables as V  # noqa: E402

# 변이시험(probe_20260829_pl_eqs_mutation.py) + 빌더 write-path 로 판정한 결과.
VERDICT = {
    "생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수": "TAUTOLOGY (item7 = 3-(4+5+6) plug)",
    "생명장기재보험손익 = 재보험CSM상각+재보험RA+재보험예실차+기타재보험": "TAUTOLOGY (item12 = 8-(9+10+11) plug)",
    "생명장기손익 = 원수손익+재보험손익": "PARTIAL (item2 = 3+8 plug, 단 item1 bridge 가 별도로 봄)",
    "투자손익 = 투자이익+보험금융손익": "TAUTOLOGY (item18 = 17-19 plug, 2층 모두)",
    "영업이익 = 보험손익+투자손익": "REAL (독립 3계정, 되맞춤 3/410)",
    "세전이익 = 영업이익+영업외손익": "TAUTOLOGY (item21 = 22-20 plug, 410/418)",
    "당기순이익 = 세전-법인세": "TAUTOLOGY (item23 = 22-24 plug, 418/418)",
    "총포괄손익 = 당기순이익+기타포괄손익": "REAL (독립 3태그)",
    "기타포괄손익 = FVOCI채무증권+보험계약금융(OCI)+위험회피파생상품+FVOCI지분증권+재보험금융(OCI)+기타(미분류)":
        "REAL (item32 는 leaf 카탈로그 합, 25 의 잔차가 아님)",
}


def main():
    pl = V.load_long(V.PL_PATH)
    extra_lob, _u = V.load_pl_extra_lob(V.PL_PATH)
    LOB_KEYS = ("생명장기손익", "자동차손익", "일반손익")

    # --- 보험손익 dual-form / leg-coverage (PL_EQS 밖) ---
    dp = df = ds = 0
    for (co, q), m in pl.items():
        bo = m.get("보험손익")
        if bo is None:
            ds += 1
            continue
        raw = [m.get(k) for k in LOB_KEYS]
        bare = sum(0.0 if v is None else v for v in raw) + extra_lob.get((co, q), 0.0)
        cands = [bare]
        oi, oe = m.get("기타영업수익"), m.get("기타사업비용")
        if oi is not None and oe is not None:
            cands.append(bare + oi - oe)
        diff = min((c - bo for c in cands), key=abs)
        if abs(diff) > max(0.001 * abs(bo), V.DEFAULT_FLOOR):
            df += 1
        else:
            dp += 1

    tot_pass = dp
    rows = [("보험손익(dual/leg-coverage)  [PL_EQS 밖]", dp, df, ds,
             "REAL (item1 vs 2/13/14, 독립소스)")]

    for label, lhs_key, terms in V.PL_EQS:
        p = f = s = 0
        for (co, q), m in pl.items():
            lhs = m.get(lhs_key)
            if lhs is None or any(m.get(k) is None for k, _ in terms):
                s += 1
                continue
            rhs = sum(sg * m[k] for k, sg in terms)
            adj = V.PL_EQ_ADJ.get(label)
            if adj and all(m.get(k) is not None for k, _ in adj):
                rhs = min((rhs, rhs + sum(x * m[k] for k, x in adj)), key=lambda c: abs(c - lhs))
            if abs(rhs - lhs) > max(0.001 * abs(lhs), V.EQ_FLOOR.get(label, V.DEFAULT_FLOOR)):
                f += 1
            else:
                p += 1
        tot_pass += p
        rows.append((label, p, f, s, VERDICT[label]))

    print(f"{'equation':<50} {'pass':>5} {'fail':>5} {'skip':>5}  verdict")
    print("-" * 132)
    taut = real = 0
    for label, p, f, s, verdict in rows:
        print(f"{label[:50]:<50} {p:>5} {f:>5} {s:>5}  {verdict}")
        if verdict.startswith("TAUTOLOGY"):
            taut += p
        elif verdict.startswith("REAL"):
            real += p
    partial = tot_pass - taut - real
    print("-" * 132)
    print(f"{'TOTAL':<50} {tot_pass:>5}")
    print(f"  구성상 참(TAUTOLOGY) pass = {taut:>5}  ({100.0*taut/tot_pass:.1f}%)")
    print(f"  진짜 검산(REAL)      pass = {real:>5}  ({100.0*real/tot_pass:.1f}%)")
    print(f"  부분(PARTIAL)        pass = {partial:>5}  ({100.0*partial/tot_pass:.1f}%)")
    print(f"\n게이트가 인쇄하는 PL_BRIDGE pass 는 위 합계와 같아야 한다 (실측 3057).")


if __name__ == "__main__":
    main()
