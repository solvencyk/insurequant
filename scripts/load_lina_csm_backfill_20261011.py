# -*- coding: utf-8 -*-
"""Load the staged Lina (KR0074) quarterly CSM rows into CSM_waterfall.json / CSM_amortization.json / CSM_waterfall_provenance.json.

Ticket : inbox/parser/20261011T1700Z__orchestrator__MULTI_2023.1Q-2026.2Q__csm_backfill_annual_filers_from_disclosure.md
Runlog : data/disclosure/_meta/csm_backfill_annual_filers_runlog_20261011.md
Staged by scripts/extract_lina_csm_rows_20261011.py -> data/_derived/csm_backfill_lina_20261011/{rows_waterfall,rows_amortization,sidecar_cells}.json

The load is ADDITIVE and guarded (same protocol as load_reinsurer_csm_masters_20261011.py):
  - the master is re-read right before the write; its bytes must round-trip through json.dumps(indent=2)+CRLF (so no byte of any
    existing row can change), otherwise nothing is written;
  - old-value guard: a staged key that already exists is never overwritten (equal -> skipped, different -> abort, nothing written);
  - the new rows are appended after the existing ones (the masters are append-ordered: KR0003/KR0079/KR0075 already have late blocks);
  - a backup of each master is copied to data/_derived/csm_backfill_backup_20261011/ first (+ sha256);
  - afterwards the file is re-read: the old rows are proven identical (same list prefix) and the appended rows equal the staged rows.

  default      dry run (prints the plan, writes nothing)
  --apply      write
  --revert     remove exactly the staged rows again (rows that are still equal to the staged ones), leave everything else
  --only wf,amort,side   subset.  DEFAULT = wf,side: since the extension to all quarters the staging also holds amortisation rows that are
                         NOT to be loaded until the orchestrator says so (another agent is correcting CSM_amortization.json), so the
                         amortisation master is only touched with an explicit --only amort[,...]
  --amort-quarters Q,Q   which staged schedule quarters to load (default all three = 30 rows; the ticket text names only the
                         2026.2Q p96 schedule -- the 2026.1Q p71 and 2025.3Q p66 schedules are the same table type from the same
                         filings and pass the same identities; use --amort-quarters 2026.2Q for the literal 10-row scope)

build_root_masters.py / build_csm_waterfall_master.py / build_csm_sensitivity.py / build_tidy_exports.py (--only amort) REGENERATE
masters from other inputs and would drop these rows: re-run this script with --apply after such a rebuild (idempotent).

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_lina_csm_backfill_20261011.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "data" / "_derived" / "csm_backfill_lina_20261011"
BACKUP = ROOT / "data" / "_derived" / "csm_backfill_backup_20261011"
sys.stdout.reconfigure(encoding="utf-8")

CODE = "KR0074"
# which -> (master file, staged file, key function, rows accessor/mutator)
TARGETS = {
    "wf": ("CSM_waterfall.json", "rows_waterfall.json", lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]), None),
    "amort": ("CSM_amortization.json", "rows_amortization.json", lambda r: (r["원보험사코드"], r["공시분기"], r["경과차년"]), None),
    "side": ("CSM_waterfall_provenance.json", "sidecar_cells.json", lambda r: (r["company_code"], r["quarter"], r["item_block"]), "cells"),
}


def dump(obj) -> bytes:
    """the exact serialisation of the masters: json.dumps(indent=2, ensure_ascii=False), CRLF, no trailing newline"""
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


def read_guarded(path: Path):
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if dump(obj) != raw:
        raise SystemExit(f"{path.name}: bytes do not round-trip through json.dumps(indent=2)+CRLF -- refusing to write")
    return raw, obj


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_atomic(path: Path, data: bytes):
    tmp = path.with_suffix(path.suffix + ".tmp_lina")
    tmp.write_bytes(data)
    tmp.replace(path)


def rows_of(obj, field):
    return obj if field is None else obj[field]


def with_rows(obj, field, rows):
    if field is None:
        return rows
    new = dict(obj)
    new[field] = rows
    return new


def plan(staged, existing, key):
    ex = {key(r): r for r in existing}
    new, same, collide = [], [], []
    for r in staged:
        k = key(r)
        if k not in ex:
            new.append(r)
        elif ex[k] == r:
            same.append(k)
        else:
            collide.append((k, ex[k], r))
    return new, same, collide


AMORT_QUARTERS = None          # None = every staged schedule quarter (set by --amort-quarters)
QUARTERS = None                # None = every staged quarter of the waterfall / sidecar (set by --quarters)


def process(which, apply, revert, report):
    fname, sname, key, field = TARGETS[which]
    staged = json.loads((STAGE / sname).read_text(encoding="utf-8"))
    if which == "amort" and AMORT_QUARTERS is not None:
        staged = [r for r in staged if r["공시분기"] in AMORT_QUARTERS]
    if which in ("wf", "side") and QUARTERS is not None:
        staged = [r for r in staged if (r.get("공시분기") or r.get("quarter")) in QUARTERS]
    for r in staged:
        code = r.get("원보험사코드") or r.get("company_code")
        assert code == CODE, r                                   # this loader only ever adds Lina rows
    path = ROOT / fname
    for attempt in range(3):
        raw, obj = read_guarded(path)
        rows = rows_of(obj, field)
        if revert:
            keys = {key(r): r for r in staged}
            keep = [r for r in rows if not (key(r) in keys and keys[key(r)] == r)]
            removed = len(rows) - len(keep)
            print(f"[{which}] {fname}: revert would remove {removed} of {len(staged)} staged rows")
            if not apply:
                report[which] = {"revert_removed": removed}
                return
            BACKUP.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, BACKUP / f"{fname}.pre_revert")
            if sha(path.read_bytes()) != sha(raw):
                continue
            write_atomic(path, dump(with_rows(obj, field, keep)))
            report[which] = {"reverted": removed}
            return
        new, same, collide = plan(staged, rows, key)
        print(f"[{which}] {fname}: existing {len(rows)} | staged {len(staged)} | new {len(new)} | already present (equal) {len(same)} | collisions {len(collide)}")
        if collide:
            raise SystemExit(f"[{which}] collisions with different values (never overwritten): {collide[:5]}")
        if not apply:
            report[which] = {"new": len(new), "existing": len(rows), "same": len(same), "new_keys": [list(key(r)) for r in new]}
            return
        BACKUP.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, BACKUP / f"{fname}.pre_load")
        (BACKUP / f"{fname}.pre_load.sha256").write_text(sha(raw) + "\n", encoding="utf-8", newline="\n")
        data = dump(with_rows(obj, field, rows + new))
        if sha(path.read_bytes()) != sha(raw):                   # someone wrote in between: start over
            print(f"[{which}] master changed during planning, retry {attempt + 1}")
            continue
        write_atomic(path, data)
        # ---- proof: old rows untouched (list prefix), appended rows == staged rows
        raw2, obj2 = read_guarded(path)
        rows2 = rows_of(obj2, field)
        assert rows2[: len(rows)] == rows, "existing rows changed"
        assert rows2[len(rows):] == new, "appended rows differ from staged rows"
        if field is not None:
            assert {k: v for k, v in obj2.items() if k != field} == {k: v for k, v in obj.items() if k != field}, "sidecar header changed"
        print(f"[{which}] written: {len(rows)} -> {len(rows2)} rows; existing rows identical (prefix proof); backup {BACKUP.name}/{fname}.pre_load sha256 {sha(raw)[:12]}")
        report[which] = {"before": len(rows), "after": len(rows2), "added": len(new), "existing_identical": True}
        return
    raise SystemExit(f"[{which}] master kept changing -- gave up without writing")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--only", default="wf,side")
    ap.add_argument("--quarters", default="all",
                    help="comma list of waterfall/sidecar quarters to load or revert (default all staged); e.g. revert only the extension: "
                         "--revert --apply --only wf,side --quarters 2023.3Q,2024.1Q,2024.2Q,2024.3Q,2025.1Q,2025.2Q")
    ap.add_argument("--amort-quarters", default="all",
                    help="comma list of schedule quarters to load, e.g. 2026.2Q (the ticket names only the 2026.2Q p96 schedule); default all staged")
    a = ap.parse_args()
    global AMORT_QUARTERS, QUARTERS
    AMORT_QUARTERS = None if a.amort_quarters == "all" else {q.strip() for q in a.amort_quarters.split(",")}
    QUARTERS = None if a.quarters == "all" else {q.strip() for q in a.quarters.split(",")}
    report = {}
    for which in [w.strip() for w in a.only.split(",")]:
        process(which, a.apply, a.revert, report)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "new_keys"} for k, v in report.items()}, ensure_ascii=False))
    if not a.apply:
        print("(dry run -- nothing written; add --apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
