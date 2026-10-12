# -*- coding: utf-8 -*-
"""Read-only: key-level comparison PL_breakdown.json working tree vs git HEAD (rows keyed (code, item, quarter))."""
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
head = json.loads(subprocess.run(["git", "-C", R, "show", "HEAD:PL_breakdown.json"], capture_output=True).stdout.decode("utf-8"))
now = json.loads(open(R + "PL_breakdown.json", "rb").read().decode("utf-8"))
def idx(rows):
    return {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
a, b = idx(head), idx(now)
removed = sorted(set(a) - set(b)); added = sorted(set(b) - set(a))
changed = [k for k in a if k in b and a[k] != b[k]]
print("HEAD rows", len(head), "now rows", len(now), "| removed", len(removed), "| added", len(added), "| changed", len(changed))
for k in added: print("  added  ", k, b[k]["값"], b[k]["값_당분기"])
for k in changed: print("  changed", k, {f: (a[k].get(f), b[k].get(f)) for f in set(a[k]) | set(b[k]) if a[k].get(f) != b[k].get(f)})
for k in removed: print("  REMOVED", k)
