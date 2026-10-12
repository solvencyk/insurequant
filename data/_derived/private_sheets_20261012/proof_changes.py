# -*- coding: utf-8 -*-
"""Proof of the 2026-10-12 privacy + capsec-column + Munich resync changes: compares working-tree public_exports/ and the
master xlsx K-ICS sheet against git HEAD. Read-only."""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PE = REPO / "public_exports"
out = []


def head_bytes(rel):
    r = subprocess.run(["git", "-c", "core.quotePath=false", "show", f"HEAD:{rel}"], cwd=REPO, capture_output=True)
    return r.stdout if r.returncode == 0 else None


head_files = subprocess.run(["git", "-c", "core.quotePath=false", "ls-tree", "--name-only", "HEAD", "public_exports/"],
                            cwd=REPO, capture_output=True, text=True, encoding="utf-8").stdout.split()
work_files = sorted("public_exports/" + p.name for p in PE.glob("*.json"))
out.append(f"HEAD files={len(head_files)} work files={len(work_files)}")
out.append("removed in work: " + ", ".join(sorted(set(head_files) - set(work_files))))
out.append("added in work: " + ", ".join(sorted(set(work_files) - set(head_files))))
for rel in work_files:
    h = head_bytes(rel)
    w = (REPO / rel).read_bytes()
    if h is None:
        continue
    if h == w:
        continue
    if rel.endswith("manifest.json"):
        hm, wm = json.loads(h), json.loads(w)
        diff = {k: (hm["sheets"].get(k), wm["sheets"].get(k)) for k in set(hm["sheets"]) | set(wm["sheets"])
                if hm["sheets"].get(k) != wm["sheets"].get(k)}
        top = {k: (hm[k], wm[k]) for k in hm if k != "sheets" and hm.get(k) != wm.get(k)}
        out.append(f"CHANGED {rel}: sheet entries {diff}; top-level changes {top}")
        continue
    hr, wr = json.loads(h), json.loads(w)
    hcols = {k for r in hr for k in r}
    wcols = {k for r in wr for k in r}
    if len(hr) == len(wr) and hcols != wcols:
        dropped = sorted(hcols - wcols)
        kept_same = all({k: v for k, v in a.items() if k in wcols} == b for a, b in zip(hr, wr))
        out.append(f"CHANGED {rel}: rows {len(hr)} -> {len(wr)}; dropped columns {dropped}; added columns {sorted(wcols - hcols)}; "
                   f"remaining cells identical={kept_same}")
    else:
        hs = {json.dumps(r, sort_keys=True, ensure_ascii=False) for r in hr}
        ws = {json.dumps(r, sort_keys=True, ensure_ascii=False) for r in wr}
        out.append(f"CHANGED {rel}: rows {len(hr)} -> {len(wr)}; added rows {len(ws - hs)}; removed/changed rows {len(hs - ws)}")
        for s in sorted(ws - hs)[:5]:
            out.append("   + " + s[:200])
text = "\n".join(out)
print(text)
(REPO / "data/_derived/private_sheets_20261012/proof_changes.txt").write_text(text + "\n", encoding="utf-8")
