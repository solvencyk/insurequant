import json, csv, os, subprocess, collections
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
out = open(here + "/k2_gold2.txt", "w", encoding="utf-8")
def git(rev, path): return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:{path}"]).decode("utf-8"))
def flat(d, pre=""):
    r = {}
    if isinstance(d, dict):
        for k, v in d.items(): r.update(flat(v, pre + "/" + str(k)))
    elif isinstance(d, list):
        for i, v in enumerate(d): r.update(flat(v, pre + f"[{i}]"))
    else: r[pre] = d
    return r
for f in ("data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json"):
    a = flat(git("b8c37fff^", f)); b = flat(git("b8c37fff", f))
    chg = [k for k in a if k in b and a[k] != b[k]]; rem = [k for k in a if k not in b]
    out.write(f"{f}: old leaves {len(a)}, new leaves {len(b)}; pre-existing leaves changed={len(chg)} removed={len(rem)}; added={len(set(b)-set(a))}\n")
    for k in chg[:5]: out.write(f"    changed {k}: {a[k]!r} -> {b[k]!r}\n")
    # what is the top-level structure
    d = git("b8c37fff", f); out.write(f"    top keys {list(d.keys())}\n")
held = list(csv.DictReader(open(src + "held_blocks.csv", encoding="utf-8-sig")))
applied = list(csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")))
gold = [r for r in held if "gold" in (r["dryrun_verdict"] + r["reason"] + r["decision"]).lower() or "owner" in r["dryrun_verdict"].lower()]
out.write(f"held rows mentioning gold/owner conflict: {len(gold)}\n")
gk = set((r["master"], r["code"], r["quarter"]) for r in gold)
ak = set((r["master"], r["code"], r["quarter"]) for r in applied)
out.write(f"gold-conflict blocks {len(gk)}; applied blocks {len(ak)}; intersection {sorted(gk & ak)}\n")
# verdict wording counts
c = collections.Counter(r["dryrun_verdict"] for r in held); out.write(str(c) + "\n")
