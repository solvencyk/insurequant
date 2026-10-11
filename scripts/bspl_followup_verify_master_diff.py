#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent cell-level diff of a master JSON against a reference copy (git HEAD or a backup file).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_verify_master_diff.py bs  [--ref baseline|HEAD|<path>]
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_followup_verify_master_diff.py pl  [--ref ...]

Reports added / removed / changed cells (key = code|item|quarter) with old -> new values and any other field difference of a row,
and prints a one-line verdict.  Read-only.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
BASE = ROOT / "data" / "_derived" / "bspl_followup_backup_20261011" / "baseline"
FILES = {"bs": "IFRS17_BS.json", "pl": "PL_breakdown.json"}


def load_ref(name: str, ref: str):
    if ref == "baseline":
        return json.loads((BASE / name).read_text(encoding="utf-8"))
    if Path(ref).exists():
        return json.loads(Path(ref).read_text(encoding="utf-8"))
    raw = subprocess.run(["git", "show", f"{ref}:{name}"], cwd=ROOT, capture_output=True, check=True).stdout      # HEAD / commit-ish
    return json.loads(raw.decode("utf-8"))


def key(r):
    return f"{r['원보험사코드']}|{r['항목번호']}|{r['공시분기']}"


def main():
    which = sys.argv[1]
    ref = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "baseline"
    name = FILES[which]
    old = {key(r): r for r in load_ref(name, ref)}
    new_rows = json.loads((ROOT / name).read_text(encoding="utf-8"))
    new = {key(r): r for r in new_rows}
    if len(new) != len(new_rows):
        print("DUPLICATE KEYS in current master:", len(new_rows) - len(new))
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed, other = [], []
    for k in sorted(set(old) & set(new)):
        a, b = old[k], new[k]
        if a == b:
            continue
        if a.get("값") != b.get("값") or a.get("값_당분기") != b.get("값_당분기"):
            changed.append((k, a.get("값"), b.get("값"), a.get("값_당분기"), b.get("값_당분기")))
        else:
            other.append(k)
    print(f"{name} vs {ref}: rows {len(old)} -> {len(new)}; added {len(added)}, removed {len(removed)}, value-changed {len(changed)}, other-field-changed {len(other)}")
    for k in added[:60]:
        print("  ADD   ", k, new[k].get("값"))
    for k in removed[:60]:
        print("  REMOVE", k)
    for c in changed[:80]:
        print("  CHANGE", c[0], c[1], "->", c[2], "" if c[3] == c[4] else f"(당분기 {c[3]} -> {c[4]})")
    for k in other[:20]:
        print("  OTHER ", k)
    print("VERDICT:", "only additions" if not removed and not changed and not other else "CHANGES PRESENT")


if __name__ == "__main__":
    main()
