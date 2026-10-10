# -*- coding: utf-8 -*-
"""Note-only patch of the already loaded reinsurer rows in CSM_sensitivity.json (KR1101~KR1108 rows only).

The first load (load_reinsurer_csm_masters_20261011.py) wrote the 비고 text built before the issuer-identity flag existed.
build_reinsurer_csm_rows_20261011.py now adds "발행사 표 항등식 잔차 ..." to rows whose printed table does not close.
This script brings the loaded rows' 비고 to the re-staged text and touches NOTHING else:
  - a loaded row is updated only when it differs from the staged row in 비고 alone, and every ';'-segment of the old note is
    still in the new note (the new note only ADDS segments);
  - any other difference (value, key, a missing staged row) aborts without writing;
  - rows of other companies are never looked at for update; the file must round-trip byte-exactly before the write;
  - backup first, proof afterwards (all other rows identical, targets differ in 비고 only).

  default  dry run        --apply  write

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/patch_reinsurer_sens_notes_20261011.py [--apply]
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
MASTER = ROOT / "CSM_sensitivity.json"
sys.stdout.reconfigure(encoding="utf-8")
CODES = {f"KR11{n:02d}" for n in range(1, 9)}


def dump(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


def key(r):
    return (r["원보험사코드"], r["공시분기"], r["순번"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    raw = MASTER.read_bytes()
    rows = json.loads(raw.decode("utf-8"))
    if dump(rows) != raw:
        raise SystemExit("CSM_sensitivity.json does not round-trip byte-exactly -- refusing to write")
    staged = {key(r): r for r in json.loads((STAGE / "rows_sensitivity.json").read_text(encoding="utf-8"))}
    updates = {}
    for r in rows:
        if r["원보험사코드"] not in CODES:
            continue
        s = staged.get(key(r))
        if s is None:
            raise SystemExit(f"loaded reinsurer row without staged counterpart: {key(r)}")
        if s == r:
            continue
        diff = [k for k in set(r) | set(s) if r.get(k) != s.get(k)]
        if diff != ["비고"]:
            raise SystemExit(f"{key(r)}: differs in {diff}, not only 비고 -- refusing")
        old_seg, new_seg = r["비고"].split("; "), s["비고"].split("; ")
        if not set(old_seg) <= set(new_seg):
            raise SystemExit(f"{key(r)}: new note drops old segments {set(old_seg) - set(new_seg)} -- refusing")
        updates[key(r)] = s
    print(f"loaded reinsurer rows {sum(1 for r in rows if r['원보험사코드'] in CODES)} | staged {len(staged)} | rows to update (비고 only) {len(updates)}")
    for k, s in sorted(updates.items()):
        added = [x for x in s["비고"].split("; ") if x not in rows[[key(r) for r in rows].index(k)]["비고"].split("; ")]
        print("  ", k, "adds:", added)
    if not a.apply:
        print("(dry run -- nothing written; add --apply)")
        return 0
    if not updates:
        print("nothing to do")
        return 0
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MASTER, BACKUP / "CSM_sensitivity.json.pre_notepatch")
    (BACKUP / "CSM_sensitivity.json.pre_notepatch.sha256").write_text(hashlib.sha256(raw).hexdigest() + "\n", encoding="utf-8")
    new_rows = [updates.get(key(r), r) if r["원보험사코드"] in CODES else r for r in rows]
    if MASTER.read_bytes() != raw:
        raise SystemExit("master changed while patching -- nothing written, re-run")
    tmp = MASTER.with_suffix(".json.tmp_reinsurer")
    tmp.write_bytes(dump(new_rows))
    tmp.replace(MASTER)
    # proof
    raw2 = MASTER.read_bytes()
    rows2 = json.loads(raw2.decode("utf-8"))
    assert dump(rows2) == raw2
    assert len(rows2) == len(rows)
    changed = [i for i, (x, y) in enumerate(zip(rows, rows2)) if x != y]
    assert len(changed) == len(updates), (len(changed), len(updates))
    for i in changed:
        d = [k for k in set(rows[i]) | set(rows2[i]) if rows[i].get(k) != rows2[i].get(k)]
        assert d == ["비고"], d
        assert rows2[i]["원보험사코드"] in CODES
    print(f"written: {len(changed)} rows changed (비고 only); all other {len(rows) - len(changed)} rows identical; backup {BACKUP.name}/CSM_sensitivity.json.pre_notepatch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
