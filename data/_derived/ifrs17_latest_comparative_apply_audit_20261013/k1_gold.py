import json, csv, os, subprocess, collections
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
out = open(here + "/k1_gold.txt", "w", encoding="utf-8")
def git(rev, path): return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:{path}"]).decode("utf-8"))
for f in ("data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json", "data/dart/viz/bs_manual_overrides.json"):
    a = git("b8c37fff^", f); b = git("b8c37fff", f)
    def keyed(d):
        if isinstance(d, dict):
            for k in ("cells", "entries", "overrides"):
                if k in d and isinstance(d[k], (list, dict)): d = d[k]; break
        return d
    ka, kb = keyed(a), keyed(b)
    out.write(f"{f}: type {type(ka).__name__} old={len(ka)} new={len(kb)}\n")
    if isinstance(ka, dict):
        changed = [k for k in ka if k in kb and ka[k] != kb[k]]; removed = [k for k in ka if k not in kb]
        out.write(f"   pre-existing keys changed={len(changed)} removed={len(removed)} added={len(set(kb)-set(ka))}\n")
    else:
        sa = [json.dumps(x, sort_keys=True, ensure_ascii=False) for x in ka]; sb = [json.dumps(x, sort_keys=True, ensure_ascii=False) for x in kb]
        out.write(f"   pre-existing entries preserved={all(x in sb for x in sa)} removed={len([x for x in sa if x not in sb])} added={len([x for x in sb if x not in sa])}\n")
# held blocks of class gold conflict
held = list(csv.DictReader(open(src + "held_blocks.csv", encoding="utf-8-sig")))
out.write(f"held cols {list(held[0].keys())}\n")
cats = collections.Counter(r.get("verdict") or r.get("section") or r.get("category") for r in held)
out.write(f"held categories {cats}\n")
