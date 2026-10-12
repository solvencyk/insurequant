import json, csv, os, subprocess
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
def git(rev, path): return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:{path}"]).decode("utf-8"))
out = open(here + "/k5_gold5.txt", "w", encoding="utf-8")
applied = list(csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")))
bsov = (git("b8c37fff^", "data/dart/viz/bs_manual_overrides.json"), git("b8c37fff", "data/dart/viz/bs_manual_overrides.json"))
tot = {"PL_breakdown": 0, "CSM_waterfall": 0}
for master, f in (("PL_breakdown", "data/_gold/user_pl_cells.json"), ("CSM_waterfall", "data/_gold/user_csm_cells.json")):
    old = git("b8c37fff^", f)["set"]; new = git("b8c37fff", f)["set"]
    okey = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in old}
    nkey = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in new}
    out.write(f"{master}: old gold entries {len(old)}, new {len(new)}; duplicated keys in new: {len(new)-len(nkey)}\n")
    pre_changed = [k for k, e in okey.items() if nkey.get(k) != e]
    out.write(f"   pre-existing gold entries changed/removed: {len(pre_changed)}\n")
    ap = [a for a in applied if a["master"] == master]
    bad = 0
    for a in ap:
        k = (a["code"], int(a["item"]), a["quarter"])
        if k in okey: bad += 1; out.write(f"   OVERLAP with pre-existing owner entry: {k} old gold {okey[k].get('값')} new {a['new']}\n")
        e = nkey.get(k)
        if e is None or abs(float(e["값"]) - float(a["new"])) > 1e-6: bad += 1; out.write(f"   gold line missing/mismatch for {k}: {e and e['값']} vs {a['new']}\n")
    out.write(f"   applied cells {len(ap)}; problems {bad}\n")
    out.write(f"   new gold lines not in applied list: {len(set(nkey)-set(okey)) - len(ap)}\n")
# BS overrides: 65 added keys vs applied
a_old, a_new = bsov
def keys(d):
    if isinstance(d, dict):
        for k in ("overrides", "cells", "set"):
            if k in d: d = d[k]; break
    return d
ko, kn = keys(a_old), keys(a_new)
out.write(f"bs_manual_overrides old {len(ko)} new {len(kn)} type {type(kn).__name__}\n")
if isinstance(kn, dict):
    added = [k for k in kn if k not in ko]; chg = [k for k in ko if kn.get(k) != ko[k]]
    out.write(f"   added {len(added)} changed-existing {len(chg)}; sample {added[:3]} -> {[kn[k] for k in added[:2]]}\n")
