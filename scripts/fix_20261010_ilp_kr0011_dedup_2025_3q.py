# -*- coding: utf-8 -*-
"""
P2 (ticket 20261010T1330Z ilp_ibk_fix_dups_and_kr0004_pl_holes): KR0011 DB손해보험 2025.3Q of
insurance_liability_portfolio.json has items 1-9 twice (9 duplicate keys, every pair identical in all ten fields).
The duplication is already in `ilp_backup_20261010_pre_merge.json` and in the 8f5e3b8 1,863-row version.

Remove exactly the SECOND copy of each of those nine pairs (keep the first), and only if the two rows are identical
in every field.  Any other duplicate key in the master, a pair that differs, or a different set of keys than the nine
expected ones aborts without writing.  Backup first, byte-exact round trip, file rewritten in its own format.

Usage:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20261010_ilp_kr0011_dedup_2025_3q.py [--write]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ILP = REPO / "insurance_liability_portfolio.json"
BACKUP = REPO / "data" / "_derived" / "ilp_backup_20261010_pre_dedup.json"
EXPECTED = {("KR0011", item, "2025.3Q") for item in range(1, 10)}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    raw0 = ILP.read_bytes()
    txt = raw0.decode("utf-8")
    crlf = "\r\n" in txt
    rows = json.loads(txt)
    dump = lambda r: (json.dumps(r, indent=2, ensure_ascii=False).replace("\n", "\r\n") if crlf else json.dumps(r, indent=2, ensure_ascii=False))
    if dump(rows) != txt:
        raise SystemExit("abort: file does not round-trip byte-for-byte")
    groups = collections.defaultdict(list)
    for i, r in enumerate(rows):
        groups[(r["원보험사코드"], r["항목번호"], r["공시분기"])].append(i)
    dups = {k: ix for k, ix in groups.items() if len(ix) > 1}
    if not dups:
        print("no duplicate keys: nothing to do")
        return 0
    if set(dups) != EXPECTED:
        raise SystemExit(f"abort: duplicate key set differs from the expected nine: {sorted(dups)}")
    drop = []
    for k, ix in sorted(dups.items()):
        if len(ix) != 2:
            raise SystemExit(f"abort: {k} appears {len(ix)} times")
        if rows[ix[0]] != rows[ix[1]]:
            raise SystemExit(f"abort: {k} rows differ: {rows[ix[0]]} vs {rows[ix[1]]}")
        drop.append(ix[1])
        print(f"  {k}: rows {ix[0]} / {ix[1]} identical (value {rows[ix[0]]['값']}) -> drop row {ix[1]}")
    print(f"{len(drop)} duplicate row(s) to remove (master {len(rows)} -> {len(rows) - len(drop)} rows)")
    if not args.write:
        print("dry run")
        return 0
    if BACKUP.exists():
        raise SystemExit(f"abort: backup {BACKUP.name} already exists")
    shutil.copyfile(ILP, BACKUP)
    if hashlib.sha256(BACKUP.read_bytes()).hexdigest() != hashlib.sha256(raw0).hexdigest():
        raise SystemExit("abort: backup mismatch")
    drop_set = set(drop)
    new_rows = [r for i, r in enumerate(json.loads(txt)) if i not in drop_set]
    if ILP.read_bytes() != raw0:
        raise SystemExit("abort: file changed while preparing the fix")
    tmp = ILP.with_name(ILP.name + ".tmp")
    tmp.write_bytes(dump(new_rows).encode("utf-8"))
    os.replace(tmp, ILP)
    after = json.loads(ILP.read_text(encoding="utf-8"))
    kept = [r for i, r in enumerate(rows) if i not in drop_set]
    assert after == kept, "remaining rows differ from the expected sequence"
    cnt = collections.Counter((r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in after)
    assert max(cnt.values()) == 1, "duplicate keys remain"
    print(f"wrote {ILP.name}; backup {BACKUP.name}; {len(rows)} -> {len(after)} rows, duplicate keys 0, all other rows identical and in the same order")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
