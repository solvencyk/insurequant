# -*- coding: utf-8 -*-
"""Independent check 3: public_exports/*.json vs HEAD copy and vs what the exporter algorithm yields from HEAD masters."""
import json
import os
import subprocess
import sys
from collections import Counter

REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
sys.path.insert(0, REPO + "/scripts")
sys.stdout.reconfigure(encoding="utf-8")


def git_bytes(rev, path):
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=REPO, capture_output=True, check=True).stdout


names = sorted(f for f in os.listdir(REPO + "/public_exports") if f.endswith(".json"))
changed = []
for f in names:
    p = "public_exports/" + f
    try:
        h = git_bytes("HEAD", p)
    except subprocess.CalledProcessError:
        print("NEW FILE not in HEAD:", f)
        changed.append(f)
        continue
    w = open(REPO + "/" + p, "rb").read()
    if h != w:
        changed.append(f)
print("changed public_exports files:", changed)
print("untracked/added files in public_exports:", subprocess.run(["git", "status", "--short", "public_exports"], cwd=REPO, capture_output=True, text=True).stdout.strip().replace("\n", " | "))

# manifest
mh = json.loads(git_bytes("HEAD", "public_exports/manifest.json").decode("utf-8"))
mw = json.load(open(REPO + "/public_exports/manifest.json", encoding="utf-8"))
print("manifest keys diff:", {k: (mh.get(k), mw.get(k)) for k in set(mh) | set(mw) if mh.get(k) != mw.get(k) and k != "sheets"})
print("manifest sheets identical to HEAD:", mh["sheets"] == mw["sheets"])
head_short = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
print("git rev-parse --short HEAD =", head_short, "| manifest build_id =", mw["build_id"], "| equal:", head_short == mw["build_id"])
print("manifest key order same as HEAD:", list(mh) == list(mw))
# manifest bytes format
raw = open(REPO + "/public_exports/manifest.json", "rb").read()
exp = json.dumps(mw, ensure_ascii=False, indent=2).encode("utf-8")
print("manifest bytes == json.dumps(indent=2, ensure_ascii=False):", raw == exp)

# rebuild the 3 changed sheets via the exporter's algorithm from HEAD masters (algorithm read from export_public_sheets.py)
from build_master_xlsx import FLATTEN  # noqa: E402
import export_public_sheets as ex  # noqa: E402  (import writes nothing; main() is guarded)

for f in changed:
    if f == "manifest.json":
        continue
    sheet = f[:-5]
    jn = next(j for j, s in ex.PUBLIC_MASTERS if s == sheet)
    rows = json.loads(git_bytes("HEAD", jn).decode("utf-8"))
    fl = FLATTEN.get(jn)
    if fl:
        rows = fl(rows)
    drop = ex.drop_cols(sheet)
    rows = [{k: v for k, v in r.items() if k not in drop} for r in rows]
    expb = json.dumps(rows, ensure_ascii=False).encode("utf-8")
    wb = open(REPO + "/public_exports/" + f, "rb").read()
    print(f"{sheet}: working file bytes == exporter-algorithm bytes from HEAD master: {wb == expb} (rows {len(rows)})")
    old = json.loads(git_bytes("HEAD", "public_exports/" + f).decode("utf-8"))
    new = json.loads(wb.decode("utf-8"))
    print(f"   row count old/new {len(old)}/{len(new)}; same row order & keys per row:", [list(r) for r in old] == [list(r) for r in new])
    ch = [(a, b) for a, b in zip(old, new) if a != b]
    print("   changed rows:", len(ch), Counter(b["원수사명"] for a, b in ch), Counter(b["공시분기"] for a, b in ch))
    cols = Counter()
    for a, b in ch:
        for k in b:
            if a.get(k) != b.get(k):
                cols[k] += 1
    print("   changed columns:", dict(cols))
# unchanged files = exporter output? (cheap check for all public sheets not changed)
bad = []
for jn, sheet in ex.PUBLIC_MASTERS:
    if sheet + ".json" in changed:
        continue
    rows = json.loads(git_bytes("HEAD", jn).decode("utf-8"))
    fl = FLATTEN.get(jn)
    if fl:
        rows = fl(rows)
    drop = ex.drop_cols(sheet)
    rows = [{k: v for k, v in r.items() if k not in drop} for r in rows]
    if json.dumps(rows, ensure_ascii=False).encode("utf-8") != open(REPO + "/public_exports/" + sheet + ".json", "rb").read():
        bad.append(sheet)
print("unchanged public sheets that differ from exporter output of HEAD masters:", bad)
