# -*- coding: utf-8 -*-
"""c2 (v2, bidirectional): PER-SECURITY X test of EVERY registry hybrid issued on/after 2023-01-01 against the issuer's own K-ICS table,
and comparison with the registry type (tier1 = 기본자본형, tier2 = 보완자본형) at the pinned revision.

Owner rule (2026-10-12): the registry type must follow the issuer's own treatment, evidenced by the movement of
    X_t = item13_t - item49_t   (보완자본으로 재분류하는 항목, 해약환급금 초과분 제외; 값 = 경과조치 적용 전 column; 억원).
Do NOT argue from "total X >= sum of deductions" (item 13 mixes tier2-type securities, tier1-type overflow and other items).

Model of one issue block (all registry securities of the company issued in quarter q; A1 = tier1-typed amount, A2 = tier2-typed amount):
    X moves by   dL(legacy item53 replaced in the same quarter)  +  A2  +  d(overflow)         under the registry assignment
    pure H2 (whole block tier2-type)   : dL + A1 + A2
    pure H1 (whole block tier1-type)   : dL + d(overflow with the block in the tier1 pool)
    overflow_t = max(0, tier1-type pool_t - 10% x item14_t),  tier1-type pool_t = item6_t - item53_t - (tier2-typed amounts outstanding at t)
Each hypothesis is evaluated with legacy L inside X and outside X; every hypothesis gets its better variant (benefit of the doubt to the registry).
local scale = largest |change of (X - L)| among the two nearest non-event quarters before and after q ; tolerance t = max(scale, 5% of block, 20).
Verdict of the data:  T2 (pure H2 within t, registry mixture/pure H1 not)  |  T1 (pure H1 within t, pure H2 not)  |  MIXED (registry mixture within t, both pure not)
                     |  INDETERMINATE.
Identity test: X_t ~ item6_t (within max(5, 1%)) at the issue quarter and the quarter before or the next 3 quarters => the issuer reclassifies the whole
hybrid stock => tier2-type.   Level test (issue quarter = 2023.1Q, first master quarter, no flow):
   tier2 hypothesis needs X_t >= company's tier2-type amounts at every quarter, tier1 (overflow-only) hypothesis needs other_t = X_t - max(0, pool_t - cap_t) >= 0.
Agreement with the registry: AGREE / DISAGREE / UNDECIDED.

Reads kics_disclosure.json and the registry at AUDIT_REV. Imports nothing from scripts/ or src/.
Output: c2_per_security_xtest_<rev>.csv / .txt
"""
import csv
import json
import sys
from collections import defaultdict

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

QS = ["%d.%dQ" % (y, n) for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]
QI = {q: i for i, q in enumerate(QS)}
QEND = {"1": "03", "2": "06", "3": "09", "4": "12"}


def num(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if s in ("", "-", "—", "–", "nan", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def q_of(date):
    if date.startswith("2026.2Q"):
        return "2026.2Q"
    y, m, _ = date.split("-")
    return "%s.%dQ" % (y, (int(m) - 1) // 3 + 1)


kd = json.load(open(ROOT + "/kics_disclosure.json", encoding="utf-8"))
assert audit_io.worktree_equals_head("kics_disclosure.json"), "master differs from HEAD"
S = defaultdict(dict)
names = {}
for r in kd:
    if r["항목번호"] in (6, 13, 14, 49, 53):
        S[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = num(r.get("값"))
        names[r["원보험사코드"]] = r["원수사명"]
reg = audit_io.load_json("data/bonds/capital_tier_registry.json")["companies"]
SUF = "_" + audit_io.resolved_rev()


def g(code, item, q):
    return S.get((code, item), {}).get(q)


def series(code):
    out = {}
    last_l = None
    for q in QS:
        i13, i49, l, i6, i14 = g(code, 13, q), g(code, 49, q), g(code, 53, q), g(code, 6, q), g(code, 14, q)
        if l is None:
            l = last_l
        else:
            last_l = l
        out[q] = {"X": None if (i13 is None or i49 is None) else i13 - i49, "L": l, "I6": i6, "cap": None if i14 is None else 0.10 * i14}
    return out


def issued_by(s, q):
    d = s.get("issue_date")
    if not d or len(d) != 10:
        return d == "2026.2Q" and q == "2026.2Q"
    return d[:7] <= "%s-%s" % (q[:4], QEND[q[5]])


rows, txt = [], ["PIN rev=%s registry=%s" % (audit_io.resolved_rev(), audit_io.sha12("data/bonds/capital_tier_registry.json"))]
for code in sorted(reg):
    secs = reg[code]["securities"]
    eff = {id(x): x["type"] for x in secs}          # effective type used in pool computations; updated by decisive data verdicts
    blocks = defaultdict(list)
    for s in secs:
        d = s.get("issue_date")
        if d and ((len(d) == 10 and d >= "2023-01-01") or d == "2026.2Q"):
            blocks[q_of(d)].append(s)
    if not blocks:
        continue
    ser = series(code)
    ev = set(blocks.keys())
    for i in range(1, len(QS)):
        a, b = ser[QS[i - 1]], ser[QS[i]]
        for k in ("L", "I6"):
            if a[k] is not None and b[k] is not None and abs(b[k] - a[k]) > 5:
                ev.add(QS[i])
    dxl = {}
    for i in range(1, len(QS)):
        q = QS[i]
        a, b = ser[QS[i - 1]], ser[q]
        if q in ev or a["X"] is None or b["X"] is None:
            continue
        dxl[q] = (b["X"] - (b["L"] or 0.0)) - (a["X"] - (a["L"] or 0.0))

    def local_scale(q):
        qi = QI[q]
        before = [abs(dxl[QS[j]]) for j in range(qi - 1, 0, -1) if QS[j] in dxl][:2]
        after = [abs(dxl[QS[j]]) for j in range(qi + 1, len(QS)) if QS[j] in dxl][:2]
        v = before + after
        return max(v) if v else 50.0

    def pool_at(q, extra_t2=0.0):
        t2_out = sum(s["amount_eok"] for s in secs if eff[id(s)] == "tier2" and issued_by(s, q)) + extra_t2
        return max(0.0, (ser[q]["I6"] or 0.0) - (ser[q]["L"] or 0.0) - t2_out)

    txt.append("== %s %s" % (code, names.get(code)))
    ident = " ".join("%s:%s" % (q, "." if ser[q]["X"] is None or ser[q]["I6"] is None else "%.1f" % (ser[q]["X"] - ser[q]["I6"])) for q in QS)
    txt.append("   X - item6 by quarter: " + ident)
    for q, blk in sorted(blocks.items(), key=lambda kv: QI[kv[0]]):
        A1 = sum(s["amount_eok"] for s in blk if s["type"] == "tier1")
        A2 = sum(s["amount_eok"] for s in blk if s["type"] == "tier2")
        types = "/".join(sorted({s["type"] for s in blk}))
        qi = QI[q]
        cur = ser[q]
        prev = ser[QS[qi - 1]] if qi > 0 else None
        later = [ser[t] for t in QS[qi:] if ser[t]["X"] is not None and ser[t]["I6"]]
        ident_max = max((abs(x["X"] - x["I6"]) / max(x["I6"], 1.0) for x in later), default=None)
        row = {"code": code, "name": names.get(code), "issue_quarter": q, "registry_types": types, "block_tier1_amount": round(A1, 2), "block_tier2_amount": round(A2, 2),
               "securities": " | ".join("%s %s %s" % (s.get("issue_date"), s["amount_eok"], s["type"]) for s in blk),
               "identity_max_rel_gap_after_issue": None if ident_max is None else round(ident_max, 4)}
        A = A1 + A2
        if prev is None or prev["X"] is None or cur["X"] is None:
            # ---------------- level test (no flow observable)
            tot_t2_other = sum(x["amount_eok"] for x in secs if eff[id(x)] == "tier2" and x not in blk)
            tot_t2_h2 = tot_t2_other + A            # hypothesis: the whole block is tier2-type
            sl2_in, sl2_out, oth1 = [], [], []
            for t in QS[qi:]:
                x = ser[t]["X"]
                if x is None:
                    continue
                l_ = ser[t]["L"] or 0.0
                sl2_in.append(x - l_ - tot_t2_h2)
                sl2_out.append(x - tot_t2_h2)
                pool_t = max(0.0, (ser[t]["I6"] or 0.0) - l_ - sum(x2["amount_eok"] for x2 in secs if eff[id(x2)] == "tier2" and x2 not in blk and issued_by(x2, t)))
                oth1.append(x - max(0.0, pool_t - ser[t]["cap"]))      # block inside the tier1 pool: overflow-only model
            tol = max(0.05 * A, 20.0)
            row.update({"test": "level_only", "min_slack_tier2_L_in_X": round(min(sl2_in), 1), "min_slack_tier2_L_out_X": round(min(sl2_out), 1),
                        "min_other_overflow_only": round(min(oth1), 1), "tolerance_t": round(tol, 1)})
            t2_feasible = min(sl2_out) >= -tol
            t1_feasible = min(oth1) >= -tol
            if t2_feasible and not t1_feasible:
                data_verdict, reason = "T2", "overflow-only (tier1) model infeasible (min other %.1f) while whole-block-in-X is feasible (min slack %.1f)" % (min(oth1), min(sl2_out))
            elif t1_feasible and not t2_feasible:
                data_verdict, reason = "T1", "overflow-only model feasible (min other %.1f) while whole-block-in-X infeasible (min slack %.1f)" % (min(oth1), min(sl2_out))
            else:
                data_verdict, reason = "INDETERMINATE", "first master quarter = issue quarter, no flow; tier2 slack %.1f / tier1 other %.1f do not separate the hypotheses" % (min(sl2_out), min(oth1))
            basis = "level"
        else:
            dX = cur["X"] - prev["X"]
            dL = (cur["L"] or 0.0) - (prev["L"] or 0.0)
            d6 = (cur["I6"] or 0.0) - (prev["I6"] or 0.0)
            ov_prev = max(0.0, pool_at(QS[qi - 1]) - (prev["cap"] or cur["cap"]))
            # registry mixture: tier1-typed part sits in the tier1 pool (already included in pool_at(q)), tier2-typed part is subtracted there
            ov_reg = max(0.0, pool_at(q) - cur["cap"]) - ov_prev
            e_reg = [dL + A2 + ov_reg, A2 + ov_reg]
            # pure H2: the tier1-typed part would also be tier2-type -> removed from the pool
            ov_h2 = max(0.0, pool_at(q, extra_t2=A1) - cur["cap"]) - ov_prev
            e_h2 = [dL + A + ov_h2, A + ov_h2]
            # pure H1: the tier2-typed part would be tier1-type -> added to the pool
            ov_h1 = max(0.0, pool_at(q, extra_t2=-A2) - cur["cap"]) - ov_prev
            e_h1 = [dL + ov_h1, ov_h1]
            scale = local_scale(q)
            t = max(scale, 0.05 * A, 20.0)
            best = lambda e: min((dX - x for x in e), key=abs)
            r_reg, r_h2, r_h1 = best(e_reg), best(e_h2), best(e_h1)
            ok_reg, ok_h2, ok_h1 = abs(r_reg) <= t, abs(r_h2) <= t, abs(r_h1) <= t
            if ok_h2 and not ok_h1 and not (A1 > 0 and ok_reg and abs(r_reg) < abs(r_h2) / 3):
                data_verdict = "T2"
            elif ok_h1 and not ok_h2:
                data_verdict = "T1"
            elif ok_reg and not ok_h2 and not ok_h1:
                data_verdict = "MIXED"
            else:
                data_verdict = "INDETERMINATE"
            reason = "dX %.1f | residual registry %.1f, pure-T2 %.1f, pure-T1 %.1f | t %.1f" % (dX, r_reg, r_h2, r_h1, t)
            basis = "flow"
            # 2nd level: identity at issue
            def ident_ok(x):
                return x["X"] is not None and x["I6"] is not None and abs(x["X"] - x["I6"]) <= max(5.0, 0.01 * x["I6"])
            nxt = [ser[t_] for t_ in QS[qi + 1: qi + 4]]
            if data_verdict == "INDETERMINATE" and ident_ok(cur) and (ident_ok(prev) or all(ident_ok(x) for x in nxt if x["X"] is not None)):
                data_verdict, basis = "T2", "identity X=item6 at issue"
            elif data_verdict == "INDETERMINATE" and min(abs(r_h2), abs(r_h1)) * 3 <= max(abs(r_h2), abs(r_h1)) and min(abs(r_h2), abs(r_h1)) <= 2 * t:
                data_verdict = "LEANS_T2" if abs(r_h2) < abs(r_h1) else "LEANS_T1"
                basis = "ratio rule (>=3x, smaller within 2t)"
            row.update({"test": "flow", "dX": round(dX, 1), "dL53": round(dL, 1), "dItem6": round(d6, 1), "cap10_at_q": round(cur["cap"], 1), "local_scale": round(scale, 1),
                        "tolerance_t": round(t, 1), "res_registry": round(r_reg, 1), "res_pure_T2": round(r_h2, 1), "res_pure_T1": round(r_h1, 1)})
        # ---- agreement with the registry
        reg_all2 = A1 == 0 and A2 > 0
        reg_all1 = A2 == 0 and A1 > 0
        if data_verdict in ("T2", "LEANS_T2"):
            agree = "AGREE" if reg_all2 else ("DISAGREE" if reg_all1 else "DISAGREE(part)")
        elif data_verdict in ("T1", "LEANS_T1"):
            agree = "AGREE" if reg_all1 else ("DISAGREE" if reg_all2 else "DISAGREE(part)")
        elif data_verdict == "MIXED":
            agree = "AGREE" if (A1 > 0 and A2 > 0) else "DISAGREE"
        elif data_verdict == "T1_or_partial":
            agree = "DISAGREE" if reg_all2 else "AGREE"
        else:
            agree = "UNDECIDED"
        if data_verdict in ("T1", "T2"):
            for x in blk:
                eff[id(x)] = "tier1" if data_verdict == "T1" else "tier2"
        weak = data_verdict.startswith("LEANS")
        row.update({"data_verdict": data_verdict, "verdict_basis": basis, "agreement_with_registry": agree + (" (weak)" if weak and agree.startswith(("AGREE", "DISAGREE")) else ""), "reason": reason})
        rows.append(row)
        txt.append("  [%s] %s | registry %s | %s | data=%s [%s] -> %s%s" % (q, row["securities"], types, reason, data_verdict, basis, agree, " (weak)" if weak else ""))

cols = []
for r in rows:
    for k in r:
        if k not in cols:
            cols.append(k)
with open(HERE + "c2_per_security_xtest" + SUF + ".csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
txt.append("")
from collections import Counter
cnt = Counter(r["agreement_with_registry"] for r in rows)
txt.append("agreement summary over %d issue blocks: %s" % (len(rows), ", ".join("%s %d" % kv for kv in sorted(cnt.items()))))
open(HERE + "c2_per_security_xtest" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(txt) + "\n")
print("\n".join(l for l in txt if "X - item6" not in l))
