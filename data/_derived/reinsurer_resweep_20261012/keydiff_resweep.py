"""Key-level diff of PL_breakdown.json / IFRS17_BS.json (live) against git HEAD and against the pre-apply backup."""
import json, subprocess, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
BK = "data/_derived/reinsurer_resweep_backup_20261012/"


def head(path):
    raw = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, check=True).stdout
    return json.loads(raw.decode("utf-8"))


def key_pl(r):
    return (r["원보험사코드"], str(r["항목번호"]), r["공시분기"])


out = {}
for name, path in (("PL", "PL_breakdown.json"), ("BS", "IFRS17_BS.json")):
    live = json.load(open(path, encoding="utf-8"))
    for ref_name, ref in (("HEAD", head(path)), ("backup", json.load(open(BK + path, encoding="utf-8")))):
        a = {key_pl(r): json.dumps(r, ensure_ascii=False, sort_keys=True) for r in ref}
        b = {key_pl(r): json.dumps(r, ensure_ascii=False, sort_keys=True) for r in live}
        added = [k for k in b if k not in a]
        deleted = [k for k in a if k not in b]
        changed = [k for k in a if k in b and a[k] != b[k]]
        print(f"{name} vs {ref_name}: rows {len(ref)} -> {len(live)} | added {len(added)} deleted {len(deleted)} changed {len(changed)} | added by item {dict(sorted(Counter(k[1] for k in added).items(), key=lambda kv: int(kv[0])))} | by company {dict(sorted(Counter(k[0] for k in added).items()))}")
        out[f"{name}_{ref_name}"] = {"added": len(added), "deleted": len(deleted), "changed": len(changed)}
json.dump(out, open("data/_derived/reinsurer_resweep_20261012/keydiff_result.json", "w", encoding="utf-8"), indent=1)
