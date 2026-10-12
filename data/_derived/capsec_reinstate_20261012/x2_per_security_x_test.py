# -*- coding: utf-8 -*-
"""x2: per-security issuer-treatment (X) test for every security the registry types tier2 (10 companies, 17 securities).

Owner rule (2026-10-12): the registry type follows what the issuer itself did in its K-ICS disclosure.
X = item13 - item49 = reclass into supplementary capital other than the lapse-reserve excess. It contains
(a) tier2-type securities (III.2.da.(2)) in full, (b) tier1-type securities only for the part above the limit
(10% x item14), (c) other small items. So at an issuance quarter: tier2-type -> X rises by the issue amount;
tier1-type -> X rises only by the new overflow. A total comparison (X >= deduction) proves nothing; this script
tests each security separately.

Test per event (issue quarter q, previous quarter p):
  obs   = X_q - X_p
  adj   = change of legacy hybrids that sit inside X (only where shown to be inside X; see notes)
  pred_T2 = A + adj ;  pred_T1 = [max(0, T1stack_q - cap10_q) - max(0, T1stack_p - cap10_p)] + adj
  tol   = 1.5 x max |dX| over the 3 most recent non-event quarter pairs before q, floor 30 (noise of other items);
          where no pre-issue pair exists (first disclosed quarter) tol_override=30 is used only because X equals item6 exactly in both quarters
  CONFIRMED_T2 if |obs - pred_T2| <= tol and every T1 variant misses by > tol;
  CONTRADICTED_T2 if the T2 prediction misses by > tol while a T1 variant fits; else INCONCLUSIVE.
Where no pre-issue quarter exists (first disclosed quarter) or other items move by thousands, a level test is used
and the result is stated as such. Inconclusive securities keep their current type (no guess).

Input : x1_panel.json (from kics_disclosure.json, read-only). Output: x2_per_security_x_test.txt / .json
Run (repo root): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capsec_reinstate_20261012/x2_per_security_x_test.py
"""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
P = json.loads((HERE / "x1_panel.json").read_text(encoding="utf-8"))


def qkey(q):
    y, p = q.split(".")
    return int(y), int(p[0])


def prevq(code, q):
    qs = sorted(P[code], key=qkey)
    i = qs.index(q)
    return qs[i - 1] if i else None


def g(code, q, k):
    return P[code][q].get(k)


def xs(code):
    return {q: v["X"] for q, v in P[code].items() if v["X"] is not None}


def noise(code, q, event_pairs):
    """tol = 1.5 x max |dX| over the 3 most recent non-event quarter pairs before q (floor 30); None if fewer than 2 pairs."""
    X = xs(code)
    qs = sorted(X, key=qkey)
    i = qs.index(q) - 1
    d = []
    while i >= 1 and len(d) < 3:
        pair = (qs[i - 1], qs[i])
        if (code, pair[1]) not in event_pairs:
            d.append(abs(X[qs[i]] - X[qs[i - 1]]))
        i -= 1
    if len(d) < 2:
        return None
    return max(30.0, 1.5 * max(d))


EVENTS = [
    dict(sec="KR0005 흥국화재 제5회 신종 (2025-03-21, 1,993)", code="KR0005", q="2025.1Q", A=1993.0, t1_before=46.0, adj=0.0,
         note="item53 2,120 unchanged (2024.4Q cell empty in master only); pre-issue X band 2,591~2,630; post-issue X - 1,993 = 2,620 -> 2,377 continues the band."),
    dict(sec="KR0032 NH농협손해 제3회 신종 (2024-12-27, 4,500)", code="KR0032", q="2024.4Q", A=4500.0, t1_before=0.0, adj=0.0,
         note="item53 = 0; X stays 4,820~5,125 for 7 quarters while cap10 moves 1,344~1,642 (a tier1-type overflow would move with it)."),
    dict(sec="KR0050 하나손해 제1회 신종 (2024-05-14, 1,000)", code="KR0050", q="2024.2Q", A=1000.0, t1_before=0.0, adj=0.0,
         note="pre-issue X band 15~39; X stays 1,000~1,052 for 8 quarters while cap10 rises 290~463."),
    dict(sec="KR0050 하나손해 2026.2Q 신규 신종 (999, 채권원장 미등재)", code="KR0050", q="2026.2Q", A=999.0, t1_before=0.0, adj=0.0,
         note="제1회 is tier2-type (event above), so the new one alone is the T1 stack: overflow 999 - cap10."),
    dict(sec="KR0068 한화생명 신종5+신종6 (2024-07-17 5,000 + 2024-09-24 6,000, same quarter)", code="KR0068", q="2024.3Q", A=11000.0, t1_before=0.0, adj=-4983.44,
         parts=[("신종5", 5000.0), ("신종6", 6000.0)],
         note="legacy hybrids (item53) sit inside X: 2023.1Q->2Q dX -10,691 vs d(item53) -10,600; 2023.2Q/3Q X - item53 = 3.3 / 3.9. Legacy 4,983 leaves in this quarter (item53 -> 0)."),
    dict(sec="KR0068 한화생명 신종8 (2025-03-26, 6,000)", code="KR0068", q="2025.1Q", A=6000.0, t1_before=0.0, adj=0.0,
         note="legacy gone; both earlier new ones are tier2-type, so only this one is the T1 stack."),
    dict(sec="KR0068 한화생명 외화 신종 (2025-06-24, 13,819)", code="KR0068", q="2025.2Q", A=13819.0, t1_before=0.0, adj=0.0,
         note="X - all four tier2 = 59 / 52 / 108 / 178 / 408 afterwards."),
    dict(sec="KR0072 KDB생명 제2회 신종 (2023-05-19, 2,160)", code="KR0072", q="2023.2Q", A=2160.0, t1_before=0.0, adj=-2160.0, tol_override=30.0,
         note="2023.1Q X = 2,160 = item53 (legacy 2,160 inside X; item6 4,965 incl. 2,805 not in X); the new 2,160 replaces it. Level: X - item6 within 0.5 for 13 quarters while cap10 moves 1,288~1,613."),
    dict(sec="KR0072 KDB생명 제3회 신종 (2024-12-26, 250)", code="KR0072", q="2024.4Q", A=245.0, t1_before=0.0, adj=0.0,
         note="book amount 245 (item6 change); face 250."),
    dict(sec="KR0073 교보생명 신종 (2023-05-12, 4,985)", code="KR0073", q="2023.2Q", A=4985.0, t1_before=0.0, adj=0.0, tol_override=30.0,
         note="legacy 11,089 unchanged and inside X (2023.1Q X = item6 = item53 = 11,089); 2023.2Q X = item6 = 16,074."),
    dict(sec="KR0073 교보생명 신종 (2024-11-12, 5,983)", code="KR0073", q="2024.4Q", A=5983.0, t1_before=0.0, adj=0.0,
         note="item47(pre) +202 as well; the issuer did not add it to supplementary capital."),
]


def run_event(e):
    code, q = e["code"], e["q"]
    p = prevq(code, q)
    Xq, Xp = g(code, q, "X"), g(code, p, "X")
    cq, cp = g(code, q, "cap10"), g(code, p, "cap10")
    obs = Xq - Xp
    adj = e["adj"]
    A = e["A"]
    tb = e["t1_before"]
    event_pairs = {(ev["code"], ev["q"]) for ev in EVENTS}
    tol = noise(code, q, event_pairs)
    if tol is None:
        tol = e["tol_override"]
    pT2 = A + adj

    def over(stack_new):
        return max(0.0, tb + stack_new - cq) - max(0.0, tb - cp) + adj

    variants = {"all T1": over(A)}
    if e.get("parts"):
        (n1, a1), (n2, a2) = e["parts"]
        base = max(0.0, tb - cp)
        variants = {
            "both T1": over(A),
            f"{n1} T1, {n2} T2": a2 + adj + (max(0.0, tb + a1 - cq) - base),
            f"{n1} T2, {n2} T1": a1 + adj + (max(0.0, tb + a2 - cq) - base),
        }
    gap2 = abs(obs - pT2)
    gaps1 = {k: abs(obs - v) for k, v in variants.items()}
    if gap2 <= tol and all(v > tol for v in gaps1.values()):
        verdict = "CONFIRMED_T2"
    elif gap2 > tol and any(v <= tol for v in gaps1.values()):
        verdict = "CONTRADICTED_T2"
    else:
        verdict = "INCONCLUSIVE"
    i47q, i47p = g(code, q, "i47"), g(code, p, "i47")
    return dict(security=e["sec"], code=code, quarter=q, prev=p, X_prev=Xp, X_q=Xq, obs_dX=round(obs, 2),
                d_item6=round((g(code, q, "i6") or 0) - (g(code, p, "i6") or 0), 2),
                d_item47_pre=None if i47q is None or i47p is None else round(i47q - i47p, 2),
                cap10_q=cq, adj_legacy_in_X=adj, pred_T2=round(pT2, 2),
                pred_T1_variants={k: round(v, 2) for k, v in variants.items()},
                tol=round(tol, 1), gap_T2=round(gap2, 2), gap_T1={k: round(v, 2) for k, v in gaps1.items()},
                verdict=verdict, note=e["note"])


def legacy_excess(code, q, basis=0.15):
    return max(0.0, (g(code, q, "i53") or 0) - basis * g(code, q, "i14"))


def level_koreanre_5():
    rows = []
    for q in ["2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"]:
        X = g("KR1000", q, "X")
        n5 = g("KR1000", q, "i6") - g("KR1000", q, "i53")
        le = legacy_excess("KR1000", q)
        cap10 = g("KR1000", q, "cap10")
        rows.append(dict(q=q, X=X, legacy_excess=round(le, 1), N5=round(n5, 1), O_if_T2=round(X - le - n5, 1),
                         O_if_T1_own10pct=round(X - le - max(0.0, n5 - cap10), 1)))
    return rows


def level_koreanre_6():
    rows = []
    n5 = 2494.9
    for q in ["2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"]:
        X = g("KR1000", q, "X")
        N = g("KR1000", q, "i6") - g("KR1000", q, "i53")
        le = legacy_excess("KR1000", q)
        cap10 = g("KR1000", q, "cap10")
        rows.append(dict(q=q, X=X, legacy_excess=round(le, 1), N_all=round(N, 1), O_if_5_T2_6_T2=round(X - le - N, 1),
                         O_if_5_T2_6_T1=round(X - le - n5 - max(0.0, (N - n5) - cap10), 1)))
    return rows


def level_generic(code, hyb_t2, extra_in_x):
    rows = []
    for q in sorted(P[code], key=qkey):
        X = g(code, q, "X")
        if X is None:
            continue
        rows.append(dict(q=q, X=X, cap10=g(code, q, "cap10"), O_if_T2=round(X - hyb_t2 - extra_in_x, 1),
                         O_if_T1=round(X - extra_in_x, 1)))
    return rows


def level_hanalife():
    A = 1798.75
    rows = []
    for q in sorted(P["KR0097"], key=qkey):
        X = g("KR0097", q, "X")
        if X is None:
            continue
        cap = g("KR0097", q, "cap10")
        ex = max(0.0, A - cap)
        rows.append(dict(q=q, X=X, cap10=cap, O_if_T2=round(X - A, 1), X_lt_amount=X < A,
                         tier1_overflow=round(ex, 1), O_if_T1=round(X - ex, 1)))
    return rows


def main():
    out = {"events": [run_event(e) for e in EVENTS]}
    out["level_koreanre_5"] = level_koreanre_5()
    out["level_koreanre_6"] = level_koreanre_6()
    out["level_nhlife_5"] = level_generic("KR0104", 2500.0, 2500.0)
    out["level_fubon"] = level_generic("KR0083", 600.0, 0.0)
    out["level_hanalife"] = level_hanalife()
    (HERE / "x2_per_security_x_test.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["== EVENT STUDY (X = item13 - item49, 억원) =="]
    for r in out["events"]:
        L.append(f"[{r['verdict']}] {r['security']}")
        L.append(f"   {r['prev']}->{r['quarter']}: X {r['X_prev']} -> {r['X_q']}  obs dX={r['obs_dX']:+}  d_item6={r['d_item6']:+}"
                 f"  d_item47pre={r['d_item47_pre']}  cap10={r['cap10_q']}  legacy-in-X adj={r['adj_legacy_in_X']:+}")
        L.append(f"   pred_T2={r['pred_T2']:+} gap={r['gap_T2']}  | "
                 + " ; ".join(f"pred[{k}]={v:+} gap={r['gap_T1'][k]}" for k, v in r['pred_T1_variants'].items())
                 + f"  | tol={r['tol']}")
        L.append(f"   note: {r['note']}")
    L.append("")
    L.append("== LEVEL TESTS ==")
    L.append("KR1000 코리안리 제5회: O = X - legacy excess over 15% x item14 - N5 (zero = tier2-type; own-10% tier1 reading leaves O = cap10)")
    L += ["   " + json.dumps(r, ensure_ascii=False) for r in out["level_koreanre_5"]]
    L.append("KR1000 코리안리 제6회: O after adding 제6회 (2,295): neither reading returns O to ~0 (other items entered X in 2024.4Q and 2025.1Q with item6 flat)")
    L += ["   " + json.dumps(r, ensure_ascii=False) for r in out["level_koreanre_6"]]
    L.append("KR0104 농협생명 제5회 (first disclosed quarter 2023.1Q, no pre-issue column): O = X - legacy 2,500 - [2,500 if T2]; cap10 never below 2,749 so no cap effect distinguishes")
    L += ["   " + json.dumps(r, ensure_ascii=False) for r in out["level_nhlife_5"]]
    L.append("KR0083 푸본현대 2023-02 (600; first disclosed quarter 2023.1Q): O swings 2,0xx~3,7xx either way")
    L += ["   " + json.dumps(r, ensure_ascii=False) for r in out["level_fubon"]]
    L.append("KR0097 하나생명 제1회 (1,798.75): necessary condition X >= amount fails when X_lt_amount=True")
    L += ["   " + json.dumps(r, ensure_ascii=False) for r in out["level_hanalife"]]
    n_lt = sum(1 for r in out["level_hanalife"] if r["X_lt_amount"])
    L.append(f"   X < amount in {n_lt} of {len(out['level_hanalife'])} quarters; O_if_T1 range "
             f"{min(r['O_if_T1'] for r in out['level_hanalife'])}~{max(r['O_if_T1'] for r in out['level_hanalife'])}")
    (HERE / "x2_per_security_x_test.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
