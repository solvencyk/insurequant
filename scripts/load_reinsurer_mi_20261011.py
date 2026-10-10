# -*- coding: utf-8 -*-
"""Load the staged reinsurer rows (KR1101~KR1108) into management_indicators.json  (ADDITIVE, guarded).

Ticket: inbox/parser/20261011T0430Z__orchestrator__KR1101-KR1108_2024.4Q-2026.2Q__reinsurer_csm_masters.md (item 4)
Runlog: data/disclosure/_meta/reinsurer_ifrs17_csm_runlog.md

Rows come from data/_derived/reinsurer_ifrs17_csm_20261011/mi_rows.json (extract_reinsurer_mi_20261011.py ->
build_reinsurer_mi_rows_20261011.py), already sorted by (code, quarter, item). The master is sorted the same way and
KR11xx sorts after KR1098, so appending keeps the file sorted. Guards (same as load_reinsurer_csm_masters_20261011.py):
  - the master is re-read right before the write and must round-trip byte-exactly through json.dumps(indent=2)+CRLF
    (no trailing newline) -- otherwise nothing is written;
  - a staged key (code, item, quarter) that already exists is never overwritten (collision with a different value aborts);
  - backup to data/_derived/reinsurer_csm_backup_20261011/ (+ sha256) first;
  - afterwards: the old rows are a list prefix of the new file and the appended rows equal the staged rows.

  default   dry run        --apply   write        --revert [--apply]   remove exactly the staged rows again

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_reinsurer_mi_20261011.py [--apply]
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
MASTER = ROOT / "management_indicators.json"
sys.stdout.reconfigure(encoding="utf-8")
CODES = {f"KR11{n:02d}" for n in range(1, 9)}


def dump(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()
    staged = json.loads((STAGE / "mi_rows.json").read_text(encoding="utf-8"))
    assert all(r["원보험사코드"] in CODES for r in staged)
    sk = lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"])
    assert all(sk(x) < sk(y) for x, y in zip(staged, staged[1:])), "staged rows must be strictly sorted by (code, quarter, item)"
    for attempt in range(3):
        raw = MASTER.read_bytes()
        rows = json.loads(raw.decode("utf-8"))
        if dump(rows) != raw:
            raise SystemExit("management_indicators.json does not round-trip byte-exactly -- refusing to write")
        if a.revert:
            st = {key(r): r for r in staged}
            keep = [r for r in rows if not (key(r) in st and st[key(r)] == r)]
            print(f"revert would remove {len(rows) - len(keep)} of {len(staged)} staged rows")
            if not a.apply:
                print("(dry run -- nothing written)")
                return 0
            BACKUP.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(MASTER, BACKUP / "management_indicators.json.pre_revert")
            if MASTER.read_bytes() != raw:
                continue
            tmp = MASTER.with_suffix(".json.tmp_reinsurer")
            tmp.write_bytes(dump(keep))
            tmp.replace(MASTER)
            print(f"reverted: {len(rows)} -> {len(keep)} rows")
            return 0
        ex = {key(r): r for r in rows}
        new, same, collide = [], 0, []
        for r in staged:
            k = key(r)
            if k not in ex:
                new.append(r)
            elif ex[k] == r:
                same += 1
            else:
                collide.append(k)
        print(f"management_indicators.json: existing {len(rows)} rows | staged {len(staged)} | new {len(new)} | already present (equal) {same} | collisions {len(collide)}")
        if collide:
            raise SystemExit(f"collisions with different values (never overwritten): {collide[:10]}")
        if not a.apply:
            print("(dry run -- nothing written; add --apply)")
            return 0
        if not new:
            print("nothing to add")
            return 0
        BACKUP.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(MASTER, BACKUP / "management_indicators.json.pre_load")
        (BACKUP / "management_indicators.json.pre_load.sha256").write_text(sha(raw) + "\n", encoding="utf-8")
        data = dump(rows + new)
        if MASTER.read_bytes() != raw:
            print(f"master changed during planning, retry {attempt + 1}")
            continue
        tmp = MASTER.with_suffix(".json.tmp_reinsurer")
        tmp.write_bytes(data)
        tmp.replace(MASTER)
        raw2 = MASTER.read_bytes()
        rows2 = json.loads(raw2.decode("utf-8"))
        assert dump(rows2) == raw2
        assert rows2[: len(rows)] == rows, "existing rows changed"
        assert rows2[len(rows):] == new, "appended rows differ from staged rows"
        assert all(r["원보험사코드"] in CODES for r in rows2[len(rows):])
        print(f"written: {len(rows)} -> {len(rows2)} rows; existing rows identical; backup {BACKUP.name}/management_indicators.json.pre_load sha256 {sha(raw)[:12]}")
        return 0
    raise SystemExit("master kept changing -- gave up without writing")


if __name__ == "__main__":
    raise SystemExit(main())
