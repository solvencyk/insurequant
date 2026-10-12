# -*- coding: utf-8 -*-
"""c2b: REVERSE per-security X test for the registry's tier1 (기본자본형) securities of DB손해보험 (KR0011), the only company with
large new tier1-type issues in the master window.  Same model as c2 (X = item13 - item49, 값 column, 억원).

Hypotheses for each issue block:
   H1 (registry: 기본자본형)  X moves only by the change of the cap overflow  max(0, tier1-type pool - 10% x SCR)
   H2 (보완자본형)            X rises by the whole book amount of the block
Noise: quarter-to-quarter change of X in the quiet quarters (no issue), robust sigma = 1.4826 x MAD, and the 2-quarter aggregate
sigma = sqrt(2) x sigma.
Reads kics_disclosure.json and the registry. Imports nothing from scripts/ or src/.
Output: c2b_dbnonlife_reverse_test.txt / .csv
"""
import csv
import json
import statistics
from collections import defaultdict

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
QS = ["%d.%dQ" % (y, n) for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]
CODE = "KR0011"


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


kd = json.load(open(ROOT + "/kics_disclosure.json", encoding="utf-8"))
S = defaultdict(dict)
for r in kd:
    if r["원보험사코드"] == CODE and r["항목번호"] in (6, 13, 14, 49):
        S[r["항목번호"]][r["공시분기"]] = num(r.get("값"))
X = {q: S[13][q] - S[49][q] for q in QS if S[13].get(q) is not None and S[49].get(q) is not None}
I6 = {q: S[6].get(q) for q in QS}
CAP = {q: 0.10 * S[14][q] for q in QS}
events = {"2025.3Q": 8650.0, "2026.1Q": None, "2026.2Q": None}   # block book amounts = change of item 6
for q in ("2026.1Q", "2026.2Q"):
    i = QS.index(q)
    events[q] = I6[q] - I6[QS[i - 1]]
events["2025.3Q"] = I6["2025.3Q"] - I6["2025.2Q"]

quiet = []
for i in range(1, len(QS)):
    q = QS[i]
    if q in events or q not in X or QS[i - 1] not in X:
        continue
    # keep quarters where item 6 did not move
    if abs((I6[q] or 0) - (I6[QS[i - 1]] or 0)) > 5:
        continue
    quiet.append((q, X[q] - X[QS[i - 1]]))
diffs = [d for _, d in quiet]
med = statistics.median(diffs)
mad = statistics.median([abs(d - med) for d in diffs])
sigma = 1.4826 * mad
L = []
L.append("DB손해보험 KR0011  quiet-quarter changes of X: %s" % ", ".join("%s %+.0f" % (q, d) for q, d in quiet))
L.append("robust sigma (1.4826 MAD) = %.0f ; plain stdev = %.0f" % (sigma, statistics.pstdev(diffs)))
rows = []
pool_before = 0.0
tot_obs = tot_h1 = tot_h2 = 0.0
for q in ("2025.3Q", "2026.1Q", "2026.2Q"):
    i = QS.index(q)
    prev = QS[i - 1]
    A = events[q]
    dX = X[q] - X[prev]
    pool_after = pool_before + A
    ov_before = max(0.0, pool_before - CAP[prev])
    ov_after = max(0.0, pool_after - CAP[q])
    e1 = ov_after - ov_before
    e2 = A
    r1, r2 = dX - e1, dX - e2
    L.append("[%s] A(item6 change)=%.1f dX=%+.1f | H1 (tier1-type, cap %.1f, pool %.1f->%.1f) expected %+.1f residual %+.1f (%.1f sigma) | H2 (tier2-type) expected %+.1f residual %+.1f (%.1f sigma)" % (
        q, A, dX, CAP[q], pool_before, pool_after, e1, r1, abs(r1) / sigma, e2, r2, abs(r2) / sigma))
    rows.append({"quarter": q, "A_item6_change": round(A, 1), "dX": round(dX, 1), "H1_expected": round(e1, 1), "H1_res": round(r1, 1),
                 "H2_expected": round(e2, 1), "H2_res": round(r2, 1), "sigma": round(sigma, 0)})
    pool_before = pool_after
    if q in ("2026.1Q", "2026.2Q"):
        tot_obs += dX
        tot_h1 += e1
        tot_h2 += e2
# aggregate of the two 2026 quarters
agg_sigma = sigma * (2 ** 0.5)
L.append("[2026.1Q+2026.2Q aggregate] dX=%+.1f | H1 expected %+.1f residual %+.1f (%.1f sigma_agg) | H2 expected %+.1f residual %+.1f (%.1f sigma_agg)" % (
    tot_obs, tot_h1, tot_obs - tot_h1, abs(tot_obs - tot_h1) / agg_sigma, tot_h2, tot_obs - tot_h2, abs(tot_obs - tot_h2) / agg_sigma))
L.append("implied overflow if 'other' stayed at its 2025.4Q level (%.1f): 2026.1Q %.1f (H1 model %.1f, H2 model %.1f); 2026.2Q %.1f (H1 model %.1f, H2 model %.1f)" % (
    X["2025.4Q"], X["2026.1Q"] - X["2025.4Q"], max(0.0, 8650 + events["2026.1Q"] - CAP["2026.1Q"]), events["2026.1Q"],
    X["2026.2Q"] - X["2025.4Q"], max(0.0, 8650 + events["2026.1Q"] + events["2026.2Q"] - CAP["2026.2Q"]), events["2026.1Q"] + events["2026.2Q"]))
open(HERE + "c2b_dbnonlife_reverse_test.txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
with open(HERE + "c2b_dbnonlife_reverse_test.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("\n".join(L))
