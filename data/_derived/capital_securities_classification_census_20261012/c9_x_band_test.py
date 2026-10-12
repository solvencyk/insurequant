"""c9_x_band_test.py (parser-kics, ticket 20261012T1230Z) -- READ ONLY on every repo file; writes only next to this script.

Quantified version of the "시계열 X 검정" that the registry's test_method describes (and that c5 only eyeballed).  For every company with hybrids issued on
or after 2023-01-01 the issuer's own K-ICS table is read as

    X_t     = item13_t - item49_t         (보완자본으로 재분류하는 항목, 해약환급금 초과분 제외; 경과조치 적용 전 표)
    L_t     = item53_t                    (기발행 신종 = 시행일 전 발행분; 적용 전 표에서는 전액 X 에 들어 있음)
    cap_t   = 0.10 * item14_t             (기본자본 인정 신종 한도 = 총요구자본의 10%)

Hypothesis for each issue block (hybrids of the same quarter are one block, because the table cannot split them):
    T2 = the block is 보완자본형: its whole book amount sits in X from the issue quarter on
    T1 = the block is 기본자본형: only the part of the pooled T1 amount above cap_t sits in X
Predicted hybrid part P_t(h) = sum(T2 blocks) + max(0, sum(T1 blocks) - cap_t).   other_t(h) = X_t - L_t - P_t(h)   (non-hybrid reclassifications).

Two readings of the same numbers (both printed):
  (1) band score   : other_t(h) should stay inside the company's OWN pre-issue band [min, max of X_t - L_t before the first new-type issue] (needs >= 3 quarters,
                     else only other_t >= -tol).  score(h) = sum over scored quarters of the distance outside the band beyond tol.  Scored quarters are all
                     quarters from the first issue on EXCEPT those in which item 53 changes (a legacy hybrid replaced in the same quarter confounds the reading).
  (2) event study  : change of other_t from the quarter before to the issue quarter of a block, with the block assumed T1 vs T2 (other blocks as in the best
                     assignment).  The true reading should show a change as small as the quarter-to-quarter changes of X - L before any issue ("typical", max).
tol = max(10, 1% of the pooled new-type amount) (book vs face rounding).
Output: census_x_band_test.csv / .txt -- per company the scores of all-T2, all-T1, the census assignment and the best assignment, the event study, the band.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/c9_x_band_test.py
"""
from __future__ import annotations

import csv
import io
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
inv = json.loads((HERE / "census_inventory.json").read_text(encoding="utf-8"))["rows"]
kd = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
sec = list(csv.DictReader(open(HERE / "census_securities.csv", encoding="utf-8-sig")))

QUARTERS = [f"{y}.{n}Q" for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]
QI = {q: i for i, q in enumerate(QUARTERS)}
S = defaultdict(dict)  # (code, item) -> {quarter: value}
for r in kd:
    if r["항목번호"] in (6, 13, 14, 49, 53):
        try:
            S[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = float(str(r.get("값")).replace(",", ""))
        except (TypeError, ValueError):
            pass


def q_of(date):
    y, m, _ = date.split("-")
    return f"{y}.{(int(m) - 1) // 3 + 1}Q"


def get(code, item, q):
    return S.get((code, item), {}).get(q)


def x_t(code, q):
    a, b = get(code, 13, q), get(code, 49, q)
    return None if a is None or b is None else a - b


def l_t(code, q):
    return get(code, 53, q) or 0.0


# census assignment of the new-type hybrids (from census_securities.csv): tier1 / tier2 / unknown
census_type = {}
for r in sec:
    if r["tier"] == "hybrid" and r["issue_date"] >= "2023-01-01":
        census_type[(r["code"], r["issue_date"], float(r["face_eok"]))] = r["census_type"]

blocks = defaultdict(lambda: defaultdict(list))  # code -> issue quarter -> [(date, face, census_type)]
for r in inv:
    if r["tier"] == "hybrid" and (r["issue_date"] or "") >= "2023-01-01":
        blocks[r["code"]][q_of(r["issue_date"])].append((r["issue_date"], float(r["face_eok"]), census_type.get((r["code"], r["issue_date"], float(r["face_eok"])), "?")))
# the hybrid that the registry knows but the bond file lacks (Hana non-life, 2026.2Q, +999)
blocks["KR0050"]["2026.2Q"].append(("2026-06-30", 999.0, "tier2"))

rows, lines = [], []
for code in sorted(blocks):
    qs = sorted(blocks[code], key=QI.get)
    amt = {}
    for q in qs:  # book amount of the block = item-6 increment in the issue quarter when it is close to the faces, else the faces
        faces = sum(f for _, f, _ in blocks[code][q])
        i = QI[q]
        d6 = None
        if i > 0 and get(code, 6, q) is not None and get(code, 6, QUARTERS[i - 1]) is not None:
            d6 = get(code, 6, q) - get(code, 6, QUARTERS[i - 1])
        amt[q] = d6 if d6 is not None and abs(d6 - faces) <= 0.10 * faces else faces
    tol = max(10.0, 0.01 * sum(amt.values()))
    first = QI[qs[0]]
    pre_q = [q for q in QUARTERS[:first] if x_t(code, q) is not None]
    pre = [x_t(code, q) - l_t(code, q) for q in pre_q]
    band = (min(pre), max(pre)) if len(pre) >= 3 else None
    pre_d = [abs(pre[k] - pre[k - 1]) for k in range(1, len(pre))]  # quarter-to-quarter changes of X - L before any new-type issue
    typical = (max(pre_d), sorted(pre_d)[len(pre_d) // 2]) if len(pre_d) >= 2 else None
    post_q = [q for q in QUARTERS[first:] if x_t(code, q) is not None and get(code, 14, q) is not None]
    scored = [q for q in post_q if QI[q] == 0 or abs(l_t(code, q) - l_t(code, QUARTERS[QI[q] - 1])) <= 1.0]

    def other(assign, q):
        t = QI[q]
        t2 = sum(amt[b] for b in qs if QI[b] <= t and assign[b] == "T2")
        t1 = sum(amt[b] for b in qs if QI[b] <= t and assign[b] == "T1")
        return x_t(code, q) - l_t(code, q) - t2 - max(0.0, t1 - 0.10 * get(code, 14, q))

    def score(assign):
        tot = 0.0
        for q in scored:
            o = other(assign, q)
            ex = (max(0.0, band[0] - o) + max(0.0, o - band[1])) if band else max(0.0, -o)
            tot += max(0.0, ex - tol)
        return tot

    allc = [dict(zip(qs, c)) for c in itertools.product(("T1", "T2"), repeat=len(qs))]
    ranked = sorted(((score(a), a) for a in allc), key=lambda z: z[0])
    all_t2, all_t1 = score({b: "T2" for b in qs}), score({b: "T1" for b in qs})
    cen = {}
    for b in qs:
        ts = {t for _, _, t in blocks[code][b]}
        cen[b] = "T2" if ts == {"tier2"} else ("T1" if ts == {"tier1"} else "?")
    cen_score = score(cen) if "?" not in cen.values() else None
    best_s, best_a = ranked[0]
    second = next((z for z in ranked[1:] if z[1] != best_a), None)
    width = (band[1] - band[0]) if band else None
    # event study, blocks in chronological order: block b is tried as T1 and as T2 with the EARLIER blocks fixed at their own sequentially chosen type
    # (the smaller change of "other" wins); later blocks do not matter at the issue quarter of b
    ev, seq, chosen = {}, {}, {}
    for b in qs:
        i = QI[b]
        prev = QUARTERS[i - 1] if i > 0 else None
        if prev is None or x_t(code, b) is None or x_t(code, prev) is None or get(code, 14, b) is None or get(code, 14, prev) is None:
            ev[b] = None
            chosen[b] = best_a[b]
            continue
        if abs(l_t(code, b) - l_t(code, prev)) > 1.0:
            ev[b] = "confounded(item 53 changes in the issue quarter)"
            chosen[b] = best_a[b]
            continue
        d = {}
        for hyp in ("T1", "T2"):
            a = dict(chosen)
            a[b] = hyp
            for later in qs:
                a.setdefault(later, "T1")
            d[hyp] = other(a, b) - other(a, prev)
        pick = "T1" if abs(d["T1"]) < abs(d["T2"]) else "T2"
        chosen[b] = pick
        rej = "T2" if pick == "T1" else "T1"
        ev[b] = d
        beyond = (abs(d[rej]) > typical[0]) if typical else (abs(d[rej]) >= 0.5 * amt[b])
        seq[b] = f"{pick} (rejected {rej}: |d|={abs(d[rej]):.0f} vs chosen |d|={abs(d[pick]):.0f}; rejected beyond " + ("typical max" if typical else "50% of block") + f": {'YES' if beyond else 'no'})"
    row = {
        "code": code, "blocks": ";".join(f"{b}:{amt[b]:.0f}" for b in qs), "band_pre_issue": "none(<3 quarters)" if not band else f"{band[0]:.0f}~{band[1]:.0f}",
        "band_width": None if width is None else round(width),
        "typical_dX_max_median": "" if typical is None else f"{typical[0]:.0f}/{typical[1]:.0f}", "tol": round(tol), "scored_quarters": len(scored),
        "score_all_T2": round(all_t2), "score_all_T1": round(all_t1),
        "census_assignment": ",".join(f"{b}={cen[b]}" for b in qs), "score_census": None if cen_score is None else round(cen_score),
        "best_assignment": ",".join(f"{b}={best_a[b]}" for b in qs), "score_best": round(best_s),
        "second_best": "" if second is None else ",".join(f"{b}={second[1][b]}" for b in qs), "score_second": "" if second is None else round(second[0]),
        "event_study": " | ".join(
            f"{b}: " + ("n/a" if e is None else (e if isinstance(e, str) else f"dOther if T1 {e['T1']:+.0f} / if T2 {e['T2']:+.0f}")) for b, e in ev.items()),
        "event_study_pick": " | ".join(f"{b}: {v}" for b, v in seq.items()),
    }
    rows.append(row)
    lines.append(f"{code}  blocks[{row['blocks']}]  pre-issue band {row['band_pre_issue']} (width {row['band_width']}); typical |d(X-L)| max/median {row['typical_dX_max_median'] or 'n/a'}; "
                 f"tol {row['tol']}; scored quarters {row['scored_quarters']}")
    lines.append(f"    score all-T2={row['score_all_T2']}  all-T1={row['score_all_T1']}  census[{row['census_assignment']}]={row['score_census']}")
    lines.append(f"    best[{row['best_assignment']}]={row['score_best']}  second[{row['second_best']}]={row['score_second']}")
    lines.append(f"    event study: {row['event_study']}")
    lines.append(f"    event study pick: {row['event_study_pick'] or 'n/a'}")
    for tag, a in (("census", cen if "?" not in cen.values() else None), ("best", best_a)):
        if a is None:
            continue
        lines.append(f"    other_t under {tag}: " + " ".join(f"{q[2:]}:{other(a, q):.0f}" for q in post_q))

with open(HERE / "census_x_band_test.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
text = "\n".join(lines) + "\n"
(HERE / "census_x_band_test.txt").write_text(text, encoding="utf-8", newline="\n")
print(text)
