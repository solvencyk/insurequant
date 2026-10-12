"""proof_vs_head.py -- READ-ONLY independent proof of the live kics_disclosure.json vs git HEAD after the apply.
 (1) every HEAD row is still present, same relative order, no new keys
 (2) the cells that differ from HEAD == exactly the 65 planned cells (value-level old -> new)
 (3) rows of every company outside the touched set equal HEAD (list equality incl. order)
 (4) the master bytes are still the canonical format (CRLF, indent 2, no BOM) and `git diff --numstat` is small
Also proves: the planned old values == the backup (pre-change) master cell by cell, and the live cells == planned new values."""
import subprocess
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
mp = merge_plans(APPLIED)
planned = {(e["code"], e["q"], e["item"], e["field"]): (e["old"], e["new"]) for e in mp["edits"]}
raw = MASTER.read_bytes()
live, head = json.loads(raw.decode("utf-8")), head_rows()
assert not raw.startswith(b"\xef\xbb\xbf") and dump_master_bytes(live) == raw
print(f"live sha {sha_bytes(raw)[:12]} rows {len(live)} | HEAD rows {len(head)} | canonical bytes (CRLF, indent 2, no BOM): True")
lk, hk = {key(r): r for r in live}, {key(r): r for r in head}
assert len(lk) == len(live) and len(hk) == len(head), "duplicate keys"
assert set(lk) == set(hk), "key sets differ"
pos = {key(r): i for i, r in enumerate(live)}
assert [pos[key(r)] for r in head] == sorted(pos[key(r)] for r in head)
print(f"(1) all {len(head)} HEAD keys present, same relative order, no new keys: True")
diff = {}
for k, hr in hk.items():
    lr = lk[k]
    for f in set(hr) | set(lr):
        if hr.get(f, "<nokey>") != lr.get(f, "<nokey>"):
            diff[(*k, f)] = (hr.get(f, "<nokey>"), lr.get(f, "<nokey>"))
assert diff == planned, f"differs from the plan: {set(diff) ^ set(planned)}"
print(f"(2) cells changed vs HEAD: {len(diff)} == planned {len(planned)} exactly (old -> new equal to the plan)")
bk = json.loads((BACKUP / "kics_disclosure_before_bede3bcc0bc6.json").read_text(encoding="utf-8"))
assert bk == head, "backup != HEAD"
touched = {k[0] for k in planned}
assert [r for r in live if r["원보험사코드"] not in touched] == [r for r in head if r["원보험사코드"] not in touched]
print(f"(3) rows of all companies outside {sorted(touched)}: identical to HEAD (list equality incl. order)")
by_kind = {}
for e in mp["edits"]:
    by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
print("   cells by kind:", by_kind, "| blocks:", len(APPLIED))
ns = subprocess.run(["git", "diff", "--numstat", "--", "kics_disclosure.json"], cwd=REPO, capture_output=True, text=True).stdout.strip()
print("(4) git diff --numstat kics_disclosure.json:", ns)
