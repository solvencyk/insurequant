"""apply_master.py [--plans a,b,...] [--apply] [--revert] -- the ONLY script of this run that writes kics_disclosure.json.

Cell-level, guarded, single writer:
  - the live master bytes must round-trip through json.loads/dumps(indent=2, CRLF) unchanged (so only the planned cells can differ)
  - every plan must carry base_sha == sha256(live master): a master another session changed since the plans were built is refused
  - every edit: the current value must equal `old` (guard); --revert swaps old/new (guard = new)
  - BEFORE writing: (1) rows keep membership and relative order (no insert/delete), (2) the cells that differ from the live master are exactly the
    planned cells, (3) the same against git HEAD (live master must equal HEAD first, so nothing else is mixed in), (4) rows of untouched
    companies are identical
  - backup of the pre-change master (new file name, never overwritten) -> temp file in the same folder -> os.replace (retries on Windows
    PermissionError: another agent may be reading the file) -> sha re-check
Without --apply: full verification, nothing written.
"""
import copy
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
apply = "--apply" in sys.argv
revert = "--revert" in sys.argv
names = sys.argv[sys.argv.index("--plans") + 1].split(",") if "--plans" in sys.argv else APPLIED

raw = MASTER.read_bytes()
live_sha = sha_bytes(raw)
assert not raw.startswith(b"\xef\xbb\xbf"), "BOM in live master"
old_rows = json.loads(raw.decode("utf-8"))
assert dump_master_bytes(old_rows) == raw, "round-trip failure: live master is not in the canonical byte format"
print(f"live master sha {live_sha[:12]} | rows {len(old_rows)} | round-trip identical: True")
plans = [load_plan(n) for n in names]
if not revert:
    for p in plans:
        assert p["base_sha"] == live_sha, f"plan {p['name']} was built against {p['base_sha'][:12]}, live master is {live_sha[:12]} -> rebuild plans (d1_build_plans.py)"
mp = merge_plans(names)
edits = mp["edits"]
if revert:
    edits = [{**e, "old": e["new"], "new": e["old"]} for e in edits]
head = head_rows()
if not revert:
    assert old_rows == head, "live master differs from git HEAD before the change - something else is mixed in; refusing"
    print("live master == git HEAD before the change: True (list equality incl. order)")

new_rows = copy.deepcopy(old_rows)
ne = apply_to_rows(new_rows, edits)
print(f"planned: {ne} cell edits in {len(names)} blocks ({'REVERT' if revert else 'apply'})")
planned = {(e["code"], e["q"], e["item"], e["field"]): (e["old"], e["new"]) for e in edits}
assert len(planned) == ne

# (1) membership + order
assert [key(r) for r in new_rows] == [key(r) for r in old_rows], "membership / order changed"
# (2) differing cells vs live == planned
diff = {}
for a, b in zip(old_rows, new_rows):
    for f in set(a) | set(b):
        if a.get(f, "<nokey>") != b.get(f, "<nokey>"):
            diff[(*key(a), f)] = (a.get(f, "<nokey>"), b.get(f, "<nokey>"))
assert diff == planned, f"cell diffs differ from the plan: {set(diff) ^ set(planned)}"
print(f"verified vs live master: changed cells {len(diff)} == planned {len(planned)} exactly (no row added/removed, order unchanged)")
# (3) vs HEAD
if not revert:
    hk = {key(r): r for r in head}
    nk = {key(r): r for r in new_rows}
    assert set(hk) == set(nk) and len(hk) == len(head)
    hd = {}
    for k, hr in hk.items():
        nr = nk[k]
        for f in set(hr) | set(nr):
            if hr.get(f, "<nokey>") != nr.get(f, "<nokey>"):
                hd[(*k, f)] = (hr.get(f, "<nokey>"), nr.get(f, "<nokey>"))
    assert hd == planned, "HEAD-vs-new cell diffs != planned"
    print(f"verified vs git HEAD: changed cells {len(hd)} == planned (no deletions, no other cells)")
# (4) untouched companies identical
touched = {e["code"] for e in edits}
assert [r for r in new_rows if r["원보험사코드"] not in touched] == [r for r in old_rows if r["원보험사코드"] not in touched]
print(f"rows of all companies outside {sorted(touched)}: identical (list equality incl. order)")
new_bytes = dump_master_bytes(new_rows)
assert not new_bytes.startswith(b"\xef\xbb\xbf")
print(f"new master bytes sha {sha_bytes(new_bytes)[:12]} | rows {len(new_rows)}")
if not apply:
    print("dry run: nothing written")
    sys.exit(0)
BACKUP.mkdir(parents=True, exist_ok=True)
bk = BACKUP / f"kics_disclosure_before_{live_sha[:12]}.json"
if bk.exists():
    assert sha_file(bk) == live_sha, "backup file exists with different content"
else:
    bk.write_bytes(raw)
print("backup:", bk)
tmp = MASTER.with_name(MASTER.name + ".latestprior.tmp")
tmp.write_bytes(new_bytes)
if sha_file(MASTER) != live_sha:
    tmp.unlink()
    raise SystemExit("master changed while preparing the write; aborted (nothing written)")
att = atomic_replace(tmp, MASTER)
assert sha_file(MASTER) == sha_bytes(new_bytes)
print(f"APPLIED{' (REVERT)' if revert else ''}: {ne} cells in {len(names)} blocks, rows {len(new_rows)}, sha {sha_file(MASTER)} (replace attempt {att})")
