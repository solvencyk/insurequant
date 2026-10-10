# -*- coding: utf-8 -*-
"""Load the staged reinsurer rows (KR1101~KR1107) into CSM_amortization.json / CSM_sensitivity.json / CSM_waterfall.json.

Ticket: inbox/parser/20261011T0430Z__orchestrator__KR1101-KR1108_2024.4Q-2026.2Q__reinsurer_csm_masters.md
Runlog: data/disclosure/_meta/reinsurer_ifrs17_csm_runlog.md

Rows come from data/_derived/reinsurer_ifrs17_csm_20261011/rows_{amortization,sensitivity,waterfall}.json (built by
build_reinsurer_csm_rows_20261011.py). The load is ADDITIVE and guarded:
  - the master is re-read right before the write; its bytes must round-trip through json.dumps(indent=2)+CRLF (so no
    byte of any existing row changes), otherwise nothing is written;
  - a staged key that already exists in the master is never overwritten (reported as a collision, nothing written);
  - the new rows are appended after the existing ones (codes KR11xx sort after KR1098);
  - a backup of the master is copied to data/_derived/reinsurer_csm_backup_20261011/ first (+ sha256);
  - afterwards the file is re-read and the old rows are proven identical (same list prefix) and the appended rows equal
    the staged rows.
The CSM_waterfall load also appends one provenance cell per (company, quarter) to CSM_waterfall_provenance.json
(source_id DISCLOSURE: the audit reports live under data/disclosure/).

  default            dry run (prints the plan, writes nothing)
  --apply            write
  --revert           remove exactly the staged rows again (rows that are still equal to the staged ones), leave everything else
  --only amort,sens,wf   subset (default: all three)

build_csm_sensitivity.py and build_tidy_exports.py (--only amort) REGENERATE their master from the viz panels and would
drop these rows: re-run this script with --apply after such a rebuild (it is idempotent: existing keys are skipped only
when equal, collisions with different values abort).

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_reinsurer_csm_masters_20261011.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "data" / "_derived" / "reinsurer_ifrs17_csm_20261011"
BACKUP = ROOT / "data" / "_derived" / "reinsurer_csm_backup_20261011"
sys.stdout.reconfigure(encoding="utf-8")

CODES = {f"KR11{n:02d}" for n in range(1, 9)}
MASTERS = {
    "amort": ("CSM_amortization.json", "rows_amortization.json", lambda r: (r["원보험사코드"], r["공시분기"], r["경과차년"])),
    "sens": ("CSM_sensitivity.json", "rows_sensitivity.json", lambda r: (r["원보험사코드"], r["공시분기"], r["순번"])),
    "wf": ("CSM_waterfall.json", "rows_waterfall.json", lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"])),
}
SIDECAR = "CSM_waterfall_provenance.json"


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


def plan_rows(name, staged, existing, key):
    ex = {key(r): r for r in existing}
    new, same, collide = [], [], []
    for r in staged:
        k = key(r)
        if k not in ex:
            new.append(r)
        elif ex[k] == r:
            same.append(k)
        else:
            collide.append(k)
    return new, same, collide


def write_atomic(path: Path, data: bytes):
    tmp = path.with_suffix(path.suffix + ".tmp_reinsurer")
    tmp.write_bytes(data)
    tmp.replace(path)


def sidecar_cells(staged_wf, audit_prov):
    """one provenance cell per (company, quarter) of the waterfall rows"""
    pdf = {(p["code"], p["quarter"]): p for p in audit_prov}
    cells, seen = [], set()
    for r in staged_wf:
        k = (r["원보험사코드"], r["공시분기"])
        if k in seen:
            continue
        seen.add(k)
        p = pdf[k]
        cells.append({"company_code": k[0], "quarter": k[1], "item_block": "csm_waterfall", "source_id": "DISCLOSURE",
                      "source_file": p["pdf"], "as_of_date": f"{k[1][:4]}-12-31"})
    return cells


def process(which, apply, revert, report):
    fname, sname, key = MASTERS[which]
    staged = json.loads((STAGE / sname).read_text(encoding="utf-8"))
    for r in staged:
        assert r["원보험사코드"] in CODES, r
    path = ROOT / fname
    for attempt in range(3):
        raw, rows = read_guarded(path)
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
            write_atomic(path, dump(keep))
            report[which] = {"reverted": removed}
            return
        new, same, collide = plan_rows(which, staged, rows, key)
        print(f"[{which}] {fname}: existing {len(rows)} rows | staged {len(staged)} | new {len(new)} | already present (equal) {len(same)} | collisions {len(collide)}")
        if collide:
            raise SystemExit(f"[{which}] collisions with different values (never overwritten): {collide[:10]}")
        before = {}
        for r in rows:
            before.setdefault(r["원보험사코드"], []).append(r)
        if not apply:
            report[which] = {"new": len(new), "existing": len(rows), "same": len(same)}
            return
        BACKUP.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, BACKUP / f"{fname}.pre_load")
        (BACKUP / f"{fname}.pre_load.sha256").write_text(sha(raw) + "\n", encoding="utf-8")
        out = rows + new
        data = dump(out)
        if sha(path.read_bytes()) != sha(raw):                    # someone wrote in between: start over
            print(f"[{which}] master changed during planning, retry {attempt + 1}")
            continue
        write_atomic(path, data)
        # ---- proof: old rows untouched, appended rows == staged rows
        raw2, rows2 = read_guarded(path)
        assert rows2[: len(rows)] == rows, "existing rows changed"
        assert rows2[len(rows):] == new, "appended rows differ from staged rows"
        assert all(r["원보험사코드"] in CODES for r in rows2[len(rows):])
        old_codes = sorted(before)
        same_after = all([r for r in rows2 if r["원보험사코드"] == c] == before[c] for c in old_codes if c not in CODES)
        print(f"[{which}] written: {len(rows)} -> {len(rows2)} rows; existing-company rows identical: {same_after}; "
              f"backup {BACKUP.name}/{fname}.pre_load sha256 {sha(raw)[:12]}")
        report[which] = {"before": len(rows), "after": len(rows2), "added": len(new), "existing_identical": same_after}
        if which == "wf":
            side = ROOT / SIDECAR
            sraw, sobj = read_guarded(side)
            shutil.copyfile(side, BACKUP / f"{SIDECAR}.pre_load")
            have = {(c["company_code"], c["quarter"], c["item_block"]) for c in sobj["cells"]}
            audit_prov = json.loads((STAGE / "build_report.json").read_text(encoding="utf-8"))["wf_provenance"]
            add = [c for c in sidecar_cells(staged, audit_prov) if (c["company_code"], c["quarter"], c["item_block"]) not in have]
            sobj["cells"] = sobj["cells"] + add
            if sha(side.read_bytes()) == sha(sraw):
                write_atomic(side, dump(sobj))
            sraw2, sobj2 = read_guarded(side)
            assert sobj2["cells"][: len(sobj["cells"]) - len(add)] == json.loads(sraw.decode("utf-8"))["cells"]
            print(f"[wf] provenance sidecar: +{len(add)} cells ({len(sobj2['cells'])} total)")
            report["wf_sidecar"] = {"added": len(add)}
        return
    raise SystemExit(f"[{which}] master kept changing -- gave up without writing")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--only", default="amort,sens,wf")
    a = ap.parse_args()
    report = {}
    for which in a.only.split(","):
        process(which.strip(), a.apply, a.revert, report)
    print(json.dumps(report, ensure_ascii=False))
    if not a.apply:
        print("(dry run -- nothing written; add --apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
