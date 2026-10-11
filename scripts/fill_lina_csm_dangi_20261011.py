# -*- coding: utf-8 -*-
"""Fill the 값_당분기 field of the existing Lina (KR0074) CSM_waterfall.json cells that are None although the previous quarter is now in the master.

Owner (2026-10-11): Lina fully filled.  Only the field 값_당분기 changes, only where it is currently None, only for the cells that
data/_derived/csm_backfill_lina_20261011/proposed_derived_dangi_existing.json lists (2023.4Q, 2024.4Q, 2025.3Q, 2025.4Q, items 1-5 = 20 cells).
Nothing else in any row changes; no row is added or removed; the order of rows and keys is kept.

Convention (measured on every company of the master by data/_derived/csm_backfill_lina_20261011/s99_dangi_convention_check.py: 2,320 of 2,340
cells follow it, the 20 exceptions are exactly these cells) = build_root_masters.build_csm():
  item 6 (closing)  : 값_당분기 = 값                          (already filled, not touched)
  item 1 (opening)  : Q1 -> 값 ; otherwise the previous quarter's item-6 값
  items 2..5        : Q1 -> 값 ; otherwise 값(q) - 값(previous quarter), rounded to 6 decimals
The derived values are recomputed from the master at run time and must equal the values the extraction proposed (else abort).

  default      dry run: prints the 20 cells (old None -> new value), writes nothing
  --apply      write (backup first: data/_derived/csm_backfill_backup_20261011/CSM_waterfall.json.pre_dangi + sha256; byte round-trip guard)
  --revert     put exactly those cells back to None (only cells whose current value equals the derived one)
  --candidate PATH   write the filled bytes to PATH instead of the master (for gate what-if runs through gate_overlay_csm.py); the master is untouched
  --verify     prove against git HEAD: only the 값_당분기 field of exactly the 20 cells differs (None -> value), nothing else
  --master PATH      operate on another file (tests on a copy); default = the repo's CSM_waterfall.json

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fill_lina_csm_dangi_20261011.py [--apply | --revert | --candidate PATH | --verify]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0074"
PROPOSED = ROOT / "data" / "_derived" / "csm_backfill_lina_20261011" / "proposed_derived_dangi_existing.json"
BACKUP = ROOT / "data" / "_derived" / "csm_backfill_backup_20261011"
MASTER = ROOT / "CSM_waterfall.json"
QUARTERS = {"2023.4Q", "2024.4Q", "2025.3Q", "2025.4Q"}
FIELD = "값_당분기"


def dump(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


def read_guarded(path: Path):
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if dump(obj) != raw:
        raise SystemExit(f"{path.name}: bytes do not round-trip through json.dumps(indent=2)+CRLF -- refusing to write")
    return raw, obj


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def derive_targets(rows, only_none=True):
    """{(quarter, item): value} for the KR0074 rows derivable by the build_csm convention.
    only_none=True: only rows whose stored 값_당분기 is None (what is still to fill); False: every KR0074 row (independent recomputation)."""
    import build_root_masters as BR

    ytd = {no: {} for no in range(1, 7)}
    for r in rows:
        if r["원보험사코드"] == CODE and r["값"] is not None:
            ytd[r["항목번호"]][r["공시분기"]] = r["값"]
    out = {}
    for r in rows:
        if r["원보험사코드"] != CODE or (only_none and r[FIELD] is not None) or r["값"] is None:
            continue
        no, q, v = r["항목번호"], r["공시분기"], r["값"]
        if no == BR.CSM_CLOSE:
            d = v
        elif no == BR.CSM_OPEN:
            p = BR._prev_q(q)
            d = v if p is None else ytd[BR.CSM_CLOSE].get(p)
        else:
            d = BR._flow_dangi(ytd[no], q)
        if d is not None:
            out[(q, no)] = round(d, 6)
    return out


def proposed_cells():
    doc = json.loads(PROPOSED.read_text(encoding="utf-8"))
    return {(c["공시분기"], c["항목번호"]): c["build_csm_규칙_도출값"] for c in doc["cells"]}


def plan(rows):
    """The 20 proposed cells, each re-derived from the master (independent of the stored value) and required to equal the proposal;
    any OTHER KR0074 cell that is None but derivable aborts the run (it would silently stay unfilled)."""
    prop = proposed_cells()
    allv = derive_targets(rows, only_none=False)
    bad = [(k, allv.get(k), prop[k]) for k in prop if k not in allv or abs(allv[k] - prop[k]) > 1e-9]
    still_none = derive_targets(rows, only_none=True)
    extra = sorted(set(still_none) - set(prop))
    if bad or extra:
        raise SystemExit(f"derived cells != proposed cells: value/missing diffs {bad[:5]} | derivable but not proposed {extra[:5]} -- aborting")
    if not {q for q, _ in prop} <= QUARTERS or len(prop) != 20 or any(no == 6 for _, no in prop):
        raise SystemExit(f"unexpected target set: {sorted(prop)}")
    return prop


def apply_to(rows, targets):
    """-> (new rows list sharing nothing with the old, list of changed (quarter, item, old, new)). Old-value guard: only None -> value."""
    changed = []
    new_rows = []
    for r in rows:
        k = (r["공시분기"], r["항목번호"])
        if r["원보험사코드"] == CODE and k in targets:
            cur = r[FIELD]
            if cur is None:
                nr = dict(r)
                nr[FIELD] = targets[k]
                new_rows.append(nr)
                changed.append((k[0], k[1], None, targets[k]))
                continue
            if abs(cur - targets[k]) > 1e-9:
                raise SystemExit(f"collision: {k} already holds {cur}, derived {targets[k]} -- never overwritten")
        new_rows.append(r)
    return new_rows, changed


def head_rows():
    raw = subprocess.run(["git", "show", "HEAD:CSM_waterfall.json"], cwd=ROOT, check=True, capture_output=True).stdout
    return json.loads(raw.decode("utf-8"))


def verify(rows_now, rows_base, targets, label_base):
    """Only the 값_당분기 field of exactly the target cells differs from the base (None -> value); same length, same order, nothing else."""
    ok = len(rows_now) == len(rows_base)
    diff_cells, other_changes = [], []
    for a, b in zip(rows_base, rows_now):
        if a == b:
            continue
        keys = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
        ident = (a["원보험사코드"], a["공시분기"], a["항목번호"])
        if keys == {FIELD} and a["원보험사코드"] == CODE and (a["공시분기"], a["항목번호"]) in targets and a[FIELD] is None \
                and abs(b[FIELD] - targets[(a["공시분기"], a["항목번호"])]) < 1e-9:
            diff_cells.append(ident)
        else:
            other_changes.append((ident, sorted(keys)))
    ok &= len(diff_cells) == len(targets) and not other_changes
    print(f"verify vs {label_base}: rows {len(rows_base)} -> {len(rows_now)} | cells whose ONLY change is 값_당분기 None -> derived value: {len(diff_cells)} (expected {len(targets)})"
          f" | any other change: {len(other_changes)} {other_changes[:3]}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--candidate")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--master", default=str(MASTER))
    a = ap.parse_args()
    path = Path(a.master)
    raw, rows = read_guarded(path)

    if a.verify:
        targets = proposed_cells()
        ok = verify(rows, head_rows(), targets, "git HEAD")
        print("VERIFY OK" if ok else "!! VERIFY FAILED")
        return 0 if ok else 1

    if a.revert:
        targets = proposed_cells()
        new_rows, n = [], 0
        for r in rows:
            k = (r["공시분기"], r["항목번호"])
            if r["원보험사코드"] == CODE and k in targets and r[FIELD] is not None:
                if abs(r[FIELD] - targets[k]) > 1e-9:
                    raise SystemExit(f"revert guard: {k} holds {r[FIELD]}, not the derived {targets[k]} -- leaving it")
                nr = dict(r)
                nr[FIELD] = None
                new_rows.append(nr)
                n += 1
            else:
                new_rows.append(r)
        print(f"revert: {n} cells put back to None")
        if a.apply:
            BACKUP.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, BACKUP / (path.name + ".pre_dangi_revert"))
            tmp = path.with_suffix(path.suffix + ".tmp_dangi")
            tmp.write_bytes(dump(new_rows))
            tmp.replace(path)
            print("reverted (written)")
        else:
            print("(dry run -- nothing written; add --apply)")
        return 0

    targets = plan(rows)
    new_rows, changed = apply_to(rows, targets)
    print(f"{len(changed)} cells to fill ({FIELD} None -> convention value), {len(targets) - len(changed)} already filled")
    for q, no, old, new in sorted(changed, key=lambda c: (c[0], c[1])):
        print(f"  {CODE} {q} item {no}: {old} -> {new}")
    if not changed:
        print("nothing to do (idempotent)")
        return 0
    data = dump(new_rows)
    ok = verify(new_rows, rows, targets, f"the file as read ({path.name})")
    if not ok:
        raise SystemExit("self-verify failed")
    if a.candidate:
        Path(a.candidate).write_bytes(data)
        print(f"candidate bytes written to {a.candidate} (sha256 {sha(data)[:12]}); the master is untouched")
        return 0
    if not a.apply:
        print("(dry run -- nothing written; add --apply or --candidate PATH)")
        return 0
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, BACKUP / (path.name + ".pre_dangi"))
    (BACKUP / (path.name + ".pre_dangi.sha256")).write_text(sha(raw) + "\n", encoding="utf-8", newline="\n")
    if sha(path.read_bytes()) != sha(raw):
        raise SystemExit("master changed while planning -- nothing written")
    tmp = path.with_suffix(path.suffix + ".tmp_dangi")
    tmp.write_bytes(data)
    tmp.replace(path)
    raw2, rows2 = read_guarded(path)
    if not verify(rows2, rows, targets, "the file before the write"):
        raise SystemExit("post-write verification failed -- restore from the backup")
    print(f"written: {len(changed)} cells filled; backup {BACKUP.name}/{path.name}.pre_dangi sha256 {sha(raw)[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
