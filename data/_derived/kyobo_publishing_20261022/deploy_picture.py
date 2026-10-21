# -*- coding: utf-8 -*-
"""Read-only: which files on origin/main differ from the branch tip (HEAD) and from the working tree."""
import subprocess, re, sys, json
def git(*a):
    r = subprocess.run(["git", "-c", "core.quotePath=false", *a], capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip()
JP = "jp-f9027362"
_, tree = git("ls-tree", "-r", "--name-only", "origin/main")
files = [f for f in tree.splitlines() if f]
rows = []
for f in files:
    if f == ".gitignore": continue
    src = "jp/" + f[len(JP) + 1:] if f.startswith(JP + "/") else f
    _, a = git("rev-parse", f"origin/main:{f}")
    rc, b = git("rev-parse", f"HEAD:{src}")
    if rc != 0: continue
    wt = subprocess.run(["git", "hash-object", src], capture_output=True)
    w = wt.stdout.decode().strip() if wt.returncode == 0 else None
    if a != b or (w and w != a):
        rows.append((f, a != b, bool(w and w != b)))
for f, d_head, d_wt in rows:
    print(("HEAD-diff " if d_head else "          ") + ("WT-modified-vs-HEAD " if d_wt else "") + f)
print("total differing:", len(rows))
