# -*- coding: utf-8 -*-
"""Read-only: which of the changed cells (HEAD~1 -> HEAD masters, plus NB / panels) does the site actually show?
Rules copied from the HTML (read, not edited):
 IFRS17.html CSM waterfall / NB / combo: year mode = latest + up to 3 prior year-ends (4Q) [WF_WINDOW=4]; quarter mode = last 5 quarters [WF_Q_WINDOW=5], field 값_당분기.
 IFRS17.html Panel 3 (PL_breakdown): year mode = field 값 at every 4Q + latest; quarter mode = 값_당분기 for the last 5 quarters.
 compare.html: the last non-null value per company/metric (panel_compare.json) -- earlier quarters are not shown.
"""
import json
import subprocess
from collections import Counter, defaultdict

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"


def show(ref, path):
    return json.loads(subprocess.check_output(["git", "-C", ROOT, "show", f"{ref}:{path}"]).decode("utf-8"))


def qk(q):
    return (int(q[:4]), int(q[5]))


def windows(quarters, kind):
    qs = sorted(quarters, key=qk)
    latest = qs[-1]
    ly = int(latest[:4])
    if kind == "wf":   # CSM waterfall / combo / NB: latest + prior 3 year-ends that exist
        year = {latest} | {f"{ly - k}.4Q" for k in range(1, 4) if f"{ly - k}.4Q" in set(qs)}
    else:              # PL panel 3
        year = {q for q in qs if q.endswith("4Q")} | {latest}
    return year, set(qs[-5:]), latest


def scan(path, kind, new_rows=None, old_rows=None):
    old = old_rows if old_rows is not None else show("d5077c7b", path)
    new = new_rows if new_rows is not None else json.load(open(f"{ROOT}/{path}", encoding="utf-8"))
    nbm = path.startswith("NB_")
    key = (lambda r: (r["원보험사코드"], r["공시분기"])) if nbm else (lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"]))
    o = {key(r): r for r in old}
    quarters = defaultdict(set)
    for r in new:
        quarters[r["원보험사코드"]].add(r["공시분기"])
    tot = Counter()
    shown = []
    for r in new:
        k = key(r)
        p = o.get(k)
        if p is None:
            continue
        code, q = k[0], k[-1]
        year, last5, latest = windows(quarters[code], kind)
        for f in sorted(set(p) | set(r)):
            if f in ("원보험사코드", "원수사명", "티커", "생손보여부", "항목번호", "항목명", "공시분기"):
                continue
            if p.get(f) == r.get(f):
                continue
            ytd = f in ("값", "신계약CSM_연누계", "월납월초보험료_연누계", "신계약CSM배수_연누계")
            vis = (q in year) if ytd else (q in last5)
            tot[(f, vis)] += 1
            if vis:
                shown.append((code, r["원수사명"], q, k[1] if not nbm else "", f, p.get(f), r.get(f), latest))
    return tot, shown


for path, kind in (("CSM_waterfall.json", "wf"), ("PL_breakdown.json", "pl"), ("NB_CSM_multiple.json", "wf")):
    if path == "NB_CSM_multiple.json":
        # old = HEAD, new = disk (this round's cell edits)
        old_rows = show("HEAD", path)
        tot, shown = scan(path, kind, old_rows=old_rows)
    else:
        tot, shown = scan(path, kind)
    print(f"== {path}: changed cells by (field, shown_in_IFRS17_table): {dict(tot)}")
    by = Counter((s[0], s[1], s[2]) for s in shown)
    for (code, name, q), n in sorted(by.items()):
        print(f"   shown: {code} {name} {q}: {n} cells")

# compare.html: last non-null per company/metric
a = json.load(open(f"{ROOT}/data/_derived/remaining_20261022/e24_publishing_four/before/panel_compare.json", encoding="utf-8"))
b = json.load(open(f"{ROOT}/data/compare/panel_compare.json", encoding="utf-8"))
qs = b["meta"]["quarters"]
n_tot = n_shown = 0
for ma, mb in zip(a["metrics"], b["metrics"]):
    for code in sorted(set(ma["v"]) | set(mb["v"])):
        va, vb = ma["v"].get(code) or [], mb["v"].get(code) or []
        lastnn = next((i for i in range(len(vb) - 1, -1, -1) if vb[i] is not None), None)
        for i, (x, y) in enumerate(zip(va, vb)):
            if x != y:
                n_tot += 1
                if i == lastnn:
                    n_shown += 1
                    print("   compare.html shown:", mb["id"], code, qs[i], x, "->", y)
print(f"== panel_compare.json: changed company values {n_tot}, shown on compare.html (= last non-null for that metric): {n_shown}")
