# -*- coding: utf-8 -*-
"""pv3 check 2: panel_compare.json / panel_csm_combo.json vs git HEAD copy (leaf diff) + own recompute of
ins_profit/inv_profit/net_income/roe (+ roe group medians) from HEAD masters (and from HEAD~1 masters for the old panel)."""
import json
import statistics
import subprocess
import sys
from collections import Counter

REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
sys.stdout.reconfigure(encoding="utf-8")


def gj(rev, path):
    out = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=REPO, capture_output=True, check=True).stdout
    return json.loads(out.decode("utf-8"))


def wj(path):
    with open(REPO + "/" + path, encoding="utf-8") as f:
        return json.load(f)


def leaves(o, p=()):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from leaves(v, p + (str(k),))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from leaves(v, p + (i,))
    else:
        yield p, o


def leafdiff(a, b):
    da, db = dict(leaves(a)), dict(leaves(b))
    return sorted(((k, da.get(k, "<absent>"), db.get(k, "<absent>")) for k in set(da) | set(db) if da.get(k, "<absent>") != db.get(k, "<absent>")), key=lambda t: str(t[0]))


SEVEN = {"KR0005", "KR0032", "KR0070", "KR0082", "KR0083", "KR0087", "KR0104"}

# ---- combo: unchanged?
P = "data/csm_combo/panel_csm_combo.json"
subprocess.run(["git", "diff", "--quiet", "HEAD", "--", P], cwd=REPO)
print("panel_csm_combo.json differs from HEAD (git diff --quiet exit; 0 = identical):", subprocess.run(["git", "diff", "--quiet", "HEAD", "--", P], cwd=REPO).returncode)

# ---- compare
P2 = "data/compare/panel_compare.json"
old, new = gj("HEAD", P2), wj(P2)
d = leafdiff(old, new)
ids = [m["id"] for m in new["metrics"]]
print("compare leaf diffs HEAD -> working:", len(d))
print("top-level keys same order:", list(old) == list(new), "| meta equal:", old["meta"] == new["meta"], "| companies equal:", old["companies"] == new["companies"], "| loss_curve equal:", old["loss_curve"] == new["loss_curve"])
by_metric = Counter()
other = []
for k, x, y in d:
    if k[0] != "metrics":
        other.append(k)
        continue
    by_metric[ids[k[1]]] += 1
print("changed leaves by metric id:", dict(by_metric), "| non-metrics leaves changed:", other)
qs = new["meta"]["quarters"]
comp_chg = Counter()
med_chg = []
struct = []
for k, x, y in d:
    mid = ids[k[1]]
    if k[2] == "v":
        comp_chg[(mid, k[3])] += 1
    elif k[2] in ("med", "med_n", "med_pre", "med_n_pre"):
        med_chg.append((mid, k[2], k[3], qs[k[4]], x, y))
    else:
        struct.append(k)
print("company-value leaf changes by (metric, code):", dict(comp_chg))
print("company codes outside the 7:", sorted({c for (_, c) in comp_chg if c not in SEVEN}))
print("median leaf changes:", med_chg)
print("other-field leaf changes:", struct)
print("metric keys identical per metric:", all(list(a) == list(b) for a, b in zip(old["metrics"], new["metrics"])))

# ---- recompute from masters
pl_new = gj("HEAD", "PL_breakdown.json")
pl_old = gj("HEAD~1", "PL_breakdown.json")
bs = gj("HEAD", "IFRS17_BS.json")
bs_old = gj("HEAD~1", "IFRS17_BS.json")
print("IFRS17_BS.json unchanged HEAD~1->HEAD:", bs == bs_old)
codes = [c["code"] for c in new["companies"]]
ctype = {c["code"]: c["type"] for c in new["companies"]}
cseg = json.load(open(REPO + "/data/company_segment.json", encoding="utf-8"))["by_code"]
pool_ok = {c: (ctype[c] != "재보·보증") for c in codes}


def fl(v):
    return None if v in (None, "") else float(str(v).replace(",", ""))


def recompute(pl):
    ytd = {}
    for r in pl:
        if r["원보험사코드"] in ctype and str(r["항목번호"]).isdigit() and int(r["항목번호"]) in (1, 17, 24):
            ytd[(int(r["항목번호"]), r["원보험사코드"], r["공시분기"])] = fl(r["값"])
    eq = {(r["원보험사코드"], r["공시분기"]): fl(r["값"]) for r in bs if r["항목번호"] == 3}
    out = {}
    for mid, it in (("ins_profit", 1), ("net_income", 24), ("inv_profit", 17)):
        out[mid] = {c: [None if ytd.get((it, c, q)) is None else int(round(ytd[(it, c, q)] / 100.0, 0)) for q in qs] for c in codes}
    roe = {}
    for c in codes:
        arr = []
        for q in qs:
            y, n = int(q[:4]), int(q[5])
            ni, e1, e0 = ytd.get((24, c, q)), eq.get((c, q)), eq.get((c, f"{y-1}.4Q"))
            if (y, n) < (2024, 1) or ni is None or e1 is None or e0 is None or e1 <= 0 or e0 <= 0:
                arr.append(None)
            else:
                arr.append(round(ni * 4.0 / n / ((e0 + e1) / 2.0) * 100.0, 1))
        roe[c] = arr
    out["roe"] = roe
    med = {}
    for t in ("생보", "손보", "재보·보증"):
        pool = [c for c in codes if ctype[c] == t and pool_ok[c]]
        row = []
        for i in range(len(qs)):
            xs = [roe[c][i] for c in pool if roe[c][i] is not None]
            row.append(None if len(xs) < 5 else round(statistics.median(xs), 1))
        med[t] = row
    out["roe_med"] = med
    return out


def compare_panel(panel, rc, label):
    m = {x["id"]: x for x in panel["metrics"]}
    bad = 0
    for mid in ("ins_profit", "net_income", "inv_profit", "roe"):
        for c in codes:
            a, b = m[mid]["v"][c], rc[mid][c]
            for i, (x, y) in enumerate(zip(a, b)):
                ok = (x is None and y is None) or (x is not None and y is not None and abs(x - y) < 1e-9)
                if not ok:
                    bad += 1
                    if bad <= 10:
                        print("   MISMATCH", label, mid, c, qs[i], "panel", x, "recompute", y)
    medbad = 0
    for t, row in rc["roe_med"].items():
        pm = m["roe"]["med"].get(t)
        if pm is None:
            if any(v is not None for v in row):
                medbad += 1
            continue
        for i, (x, y) in enumerate(zip(pm, row)):
            ok = (x is None and y is None) or (x is not None and y is not None and abs(x - y) < 1e-9)
            if not ok:
                medbad += 1
                print("   MEDMISMATCH", label, t, qs[i], x, y)
    print(f"{label}: value mismatches (4 metrics x {len(codes)} cos x {len(qs)} q) = {bad}; roe median mismatches = {medbad}")


rc_new, rc_old = recompute(pl_new), recompute(pl_old)
compare_panel(new, rc_new, "WORKING panel vs recompute(HEAD master)")
compare_panel(old, rc_old, "HEAD panel vs recompute(HEAD~1 master) [sanity of my code]")

# every recompute change old->new must equal panel leaf changes
exp = set()
for mid in ("ins_profit", "net_income", "inv_profit", "roe"):
    for c in codes:
        for i in range(len(qs)):
            if rc_old[mid][c][i] != rc_new[mid][c][i]:
                exp.add((mid, c, i))
got = {(ids[k[1]], k[3], k[4]) for k, x, y in d if k[2] == "v"}
print("own-recompute expected value changes:", len(exp), "| panel value changes:", len(got), "| equal:", exp == got)
print("expected changes by metric:", dict(Counter(m for m, _, _ in exp)), "| companies:", sorted({c for _, c, _ in exp}))
expmed = {(t, i) for t in rc_new["roe_med"] for i in range(len(qs)) if rc_old["roe_med"][t][i] != rc_new["roe_med"][t][i]}
gotmed = {(k[3], k[4]) for k, x, y in d if k[2] == "med" and ids[k[1]] == "roe"}
print("expected roe median changes:", sorted(expmed), "| panel roe median changes:", sorted(gotmed), "| equal:", expmed == gotmed)
