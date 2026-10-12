"""apply_plan.py (parser-kics, ticket 20261012T1030Z) -- the ONLY script here that writes the repo master (kics_disclosure.json).
Cell-level, guarded, single-writer:
  - the live master bytes must round-trip through json.loads/dumps(indent=2, CRLF) unchanged (so only the planned cells can differ)
  - every plan must carry base_sha == sha256(live master): a master another session changed since the plan was built is refused
  - edits: current value must equal `old` (guard); inserts: key must not exist, anchor row must exist
  - BEFORE writing: (1) every pre-existing row unchanged except the planned cells, same relative order, (2) inserted keys == planned keys,
    (3) vs git HEAD: every HEAD row present, unchanged except planned cells, same relative order; keys new vs HEAD == planned inserts;
    cells different from HEAD == planned edit cells exactly   (4) the live master equals HEAD before the change (so nothing else is mixed in)
  - backup of the pre-change master (new file name, never overwritten) -> temp file -> os.replace (retry on Windows PermissionError) -> sha re-check
usage: apply_plan.py --plans a,b [--apply]        (without --apply: full verification, nothing written)
"""
import copy
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_followups_20261012")
from lib import *  # noqa: F401,F403,E402

utf8_stdout()


def main():
    apply = "--apply" in sys.argv
    names = [x for x in sys.argv[sys.argv.index("--plans") + 1].split(",") if x]
    raw = MASTER.read_bytes()
    live_sha = sha_bytes(raw)
    assert not raw.startswith(b"\xef\xbb\xbf"), "BOM in live master"
    old_rows = json.loads(raw.decode("utf-8"))
    assert dump_master_bytes(old_rows) == raw, "round-trip failure: live master is not in the canonical byte format"
    print(f"live master sha {live_sha[:12]} | rows {len(old_rows)} | round-trip identical: True")

    plans = [load_plan(n) for n in names]
    for p in plans:
        assert p["base_sha"] == live_sha, f"plan {p['name']} was built against {p['base_sha'][:12]}, live master is {live_sha[:12]} -> rebuild plans (make_plans.py)"
    mp = merge_plans(names)
    head = head_rows()
    assert old_rows == head, "live master differs from git HEAD before the change - something else is mixed in; refusing"
    print("live master == git HEAD before the change: True (list equality incl. order)")

    new_rows = copy.deepcopy(old_rows)
    ne, ni = apply_to_rows(new_rows, mp)
    print(f"planned: edits={ne} cells, inserts={ni} rows")

    ins_keys = [key(i["row"]) for i in mp["inserts"]]
    edit_cells = {(e["code"], e["q"], e["item"], e["field"]): e for e in mp["edits"]}
    # (1) pre-existing rows vs live master
    old_idx = {key(r): r for r in old_rows}
    surv = [r for r in new_rows if key(r) not in set(ins_keys)]
    assert [key(r) for r in surv] == [key(r) for r in old_rows], "relative order / membership of surviving rows changed"
    chk = 0
    for r in surv:
        o = old_idx[key(r)]
        fields = set(o) | set(r)
        for f in fields:
            ec = edit_cells.get((*key(r), f))
            if ec is not None:
                assert o.get(f, "<nokey>") == ec["old"] and r.get(f) == ec["new"], (key(r), f)
                chk += 1
            else:
                assert o.get(f, "<nokey>") == r.get(f, "<nokey>"), f"unplanned change {key(r)} {f}"
    assert chk == ne, (chk, ne)
    # (2) inserted keys
    assert {key(r) for r in new_rows} - set(old_idx) == set(ins_keys) and len(ins_keys) == len(set(ins_keys)) == ni, "inserted keys differ from the plan"
    assert len(new_rows) == len(old_rows) + ni
    # (3) vs HEAD (list-level)
    hk = {key(r): r for r in head}
    nk = {key(r): r for r in new_rows}
    assert all(k in nk for k in hk), "a HEAD row is missing"
    diff_cells = []
    for k, hr in hk.items():
        nr = nk[k]
        for f in set(hr) | set(nr):
            if hr.get(f, "<nokey>") != nr.get(f, "<nokey>"):
                diff_cells.append((*k, f))
    assert set(diff_cells) == set(edit_cells), f"HEAD-vs-new cell diffs != planned edit cells: {sorted(set(diff_cells) ^ set(edit_cells))[:10]}"
    pos = {key(r): i for i, r in enumerate(new_rows)}
    hp = [pos[key(r)] for r in head]
    assert hp == sorted(hp), "relative order of HEAD rows changed"
    print(f"verified vs HEAD: all {len(head)} HEAD rows present, same relative order, changed cells == planned {len(edit_cells)} edit cells exactly, "
          f"new keys == planned {len(ins_keys)} inserts exactly (no deletions, no other cells)")
    # per-company untouched proof
    touched_codes = {e["code"] for e in mp["edits"]} | {k[0] for k in ins_keys}
    assert [r for r in new_rows if r["원보험사코드"] not in touched_codes] == [r for r in head if r["원보험사코드"] not in touched_codes]
    print(f"rows of all companies outside {sorted(touched_codes)}: identical to HEAD (list equality incl. order): True")
    new_bytes = dump_master_bytes(new_rows)
    assert not new_bytes.startswith(b"\xef\xbb\xbf")
    print(f"new master bytes sha {sha_bytes(new_bytes)[:12]} | rows {len(new_rows)}")
    if not apply:
        print("dry run: nothing written")
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    bk = BACKUP / f"kics_disclosure_before_{live_sha[:12]}.json"
    if bk.exists():
        assert sha_file(bk) == live_sha, "backup file exists with different content"
    else:
        bk.write_bytes(raw)
    print("backup:", bk)
    tmp = MASTER.with_name(MASTER.name + ".followups.tmp")
    tmp.write_bytes(new_bytes)
    if sha_file(MASTER) != live_sha:
        tmp.unlink()
        raise SystemExit("master changed while preparing the write; aborted (nothing written)")
    for attempt in range(1, 13):
        try:
            os.replace(tmp, MASTER)
            break
        except PermissionError as exc:
            print(f"  os.replace attempt {attempt} failed ({exc.__class__.__name__}); retry in 3s", flush=True)
            time.sleep(3)
    else:
        raise SystemExit("os.replace kept failing; master NOT written (tmp left in place)")
    assert sha_file(MASTER) == sha_bytes(new_bytes)
    log = {"plans": names, "base_sha": live_sha, "sha_after": sha_bytes(new_bytes), "rows_after": len(new_rows),
           "edits": mp["edits"], "inserts": mp["inserts"]}
    write_json_lf(EVID / f"applied_{'+'.join(names)}.json", log)
    print(f"APPLIED {names}: edits={ne} inserts={ni} rows_total={len(new_rows)} sha={sha_bytes(new_bytes)}")


if __name__ == "__main__":
    main()
