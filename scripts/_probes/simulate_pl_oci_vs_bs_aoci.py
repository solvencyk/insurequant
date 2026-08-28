#!/usr/bin/env python3
"""Simulate PL_OCI_VS_BS_AOCI BEFORE wiring it into the gate: for every (code, quarter) where
PL item25's 값_당분기 (quarterly OCI flow) is available, compare it against the QoQ delta of
IFRS17_BS.json item4 (기타포괄손익 누계액, AOCI balance, point-in-time). Reports the residual
distribution so the gate's tolerance is set from evidence, not a guess.
Ticket: inbox/parser/20260828T0113Z §작업3 rule 2 ("먼저 전 버킷 시뮬레이션을 돌려 실제 잔차
분포를 보고 허용오차를 정한다")."""
import json
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q",
      "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q",
      "2026.1Q", "2026.2Q"]


def prev_quarter(q):
    i = QS.index(q) if q in QS else -1
    return QS[i - 1] if i > 0 else None


def main():
    pl = json.loads(Path("PL_breakdown.json").read_text(encoding="utf-8"))
    bs = json.loads(Path("IFRS17_BS.json").read_text(encoding="utf-8"))

    oci_dangi = {}   # (code, quarter) -> 값_당분기 for item25
    for r in pl:
        if r["항목번호"] == 25:
            oci_dangi[(r["원보험사코드"], r["공시분기"])] = r.get("값_당분기")

    aoci = {}        # (code, quarter) -> 값 for BS item4
    for r in bs:
        if r["항목번호"] == 4:
            aoci[(r["원보험사코드"], r["공시분기"])] = r.get("값")

    print(f"PL item25 rows: {sum(1 for r in pl if r['항목번호']==25)}  "
          f"BS item4 rows: {sum(1 for r in bs if r['항목번호']==4)}")

    rows = []   # (code, quarter, delta_bs, oci_dangi, residual)
    skip_no_pl = skip_no_bs_cur = skip_no_bs_prev = 0
    for (code, q), v in oci_dangi.items():
        if v is None:
            skip_no_pl += 1
            continue
        cur = aoci.get((code, q))
        if cur is None:
            skip_no_bs_cur += 1
            continue
        pq = prev_quarter(q)
        if pq is None:
            skip_no_bs_prev += 1
            continue
        prev = aoci.get((code, pq))
        if prev is None:
            skip_no_bs_prev += 1
            continue
        delta_bs = cur - prev
        resid = delta_bs - v
        rows.append((code, q, delta_bs, v, resid))

    print(f"comparable cells: {len(rows)}  "
          f"(skip: no_pl_dangi={skip_no_pl}, no_bs_cur={skip_no_bs_cur}, no_bs_prev/pq={skip_no_bs_prev})")

    abs_resid = sorted(abs(r[4]) for r in rows)
    if not abs_resid:
        print("NO comparable cells -- cannot simulate.")
        return
    n = len(abs_resid)

    def pct(p):
        return abs_resid[min(n - 1, int(n * p))]

    print(f"\n=== |residual| distribution (백만원) ===")
    print(f"  min={abs_resid[0]:.2f}  p25={pct(.25):.2f}  median={pct(.5):.2f}  "
          f"p75={pct(.75):.2f}  p90={pct(.9):.2f}  p95={pct(.95):.2f}  max={abs_resid[-1]:.2f}")

    # relative residual: resid / max(|delta_bs|, floor)
    FLOOR = 500.0  # 백만원 (5억) -- avoid exploding ratios on tiny AOCI deltas
    rel = sorted(abs(r[4]) / max(abs(r[2]), FLOOR) for r in rows)
    def pctr(p):
        return rel[min(n - 1, int(n * p))]
    print(f"\n=== relative |residual|/max(|ΔBS|,{FLOOR:.0f}) distribution ===")
    print(f"  min={rel[0]*100:.1f}%  p25={pctr(.25)*100:.1f}%  median={pctr(.5)*100:.1f}%  "
          f"p75={pctr(.75)*100:.1f}%  p90={pctr(.9)*100:.1f}%  p95={pctr(.95)*100:.1f}%  max={rel[-1]*100:.1f}%")

    # candidate tolerance bands -- how many cells would PASS at each threshold
    for tol_rel, tol_abs in [(0.10, 1000), (0.20, 2000), (0.30, 3000), (0.50, 5000), (1.0, 10000)]:
        ok = sum(1 for r in rows if abs(r[4]) <= max(tol_rel * abs(r[2]), tol_abs))
        print(f"  tol rel={tol_rel*100:.0f}% abs={tol_abs}백만: {ok}/{len(rows)} pass "
              f"({ok/len(rows)*100:.1f}%)")

    print(f"\n=== worst 30 residuals (by relative size) ===")
    ranked = sorted(rows, key=lambda r: -abs(r[4]) / max(abs(r[2]), FLOOR))
    for code, q, dbs, dg, resid in ranked[:30]:
        rel_pct = abs(resid) / max(abs(dbs), FLOOR) * 100
        print(f"  {code:8s} {q}  ΔBS={dbs:>12.1f}  PL당분기={dg:>12.1f}  "
              f"resid={resid:>12.1f}  rel={rel_pct:>7.1f}%")

    print(f"\n=== best 15 (near-exact closes, sanity check the concept is right) ===")
    best = sorted(rows, key=lambda r: abs(r[4]))
    for code, q, dbs, dg, resid in best[:15]:
        print(f"  {code:8s} {q}  ΔBS={dbs:>12.1f}  PL당분기={dg:>12.1f}  resid={resid:>+10.3f}")

    out = Path("artifacts/parser/pl_oci_vs_bs_aoci_simulation.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        [{"code": c, "quarter": q, "delta_bs": round(dbs, 3), "pl_oci_dangi": round(dg, 3),
          "residual": round(resid, 3)} for c, q, dbs, dg, resid in rows],
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {out}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
