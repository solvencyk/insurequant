# -*- coding: utf-8 -*-
"""
P3 (ticket 20261010T0945Z lic_load_stage1): KR0009 현대해상 insurance_liability_portfolio.json 2-4,
2025.1Q / 2025.2Q / 2025.3Q.

Finding (경영공시 PDF page rendered at 130 dpi, 2-4 합계 row, every value read off the image):
  2025.1Q p9   일반모형 174,678 / 19,400 / 91,648 ; 변동수수료접근법 blank ; 보험료배분접근법 35,579 (일반 9,927 + 자동차 25,652)
  2025.2Q p10  일반모형 166,622 / 19,410 / 94,227 ; 변동수수료접근법 blank ; 보험료배분접근법 34,878 (일반 9,924 + 자동차 24,954)
  2025.3Q p9   일반모형 162,868 / 19,292 / 96,703 ; 변동수수료접근법 blank ; 보험료배분접근법 34,991 (일반 10,190 + 자동차 24,800)
  (2025.4Q p33 has the same layout and is already mapped correctly: items 4-6 = 0, item 7 = 34,772.)
The master had the PAA total in item 4 (변동수수료접근법_최선추정부채), item 7 = 0, and the PAGE NUMBER
of the PDF page ("- 9 -", "- 10 -", "- 9 -") in item 6 (변동수수료접근법_보험계약마진 = 9 / 10 / 9); item 8 (sum of 1..7)
therefore carried that page number too.  The independent DART check agrees with the corrected item 8:
  LRC total from the DART 보험계약부채 변동표 (별도, 부채 기준): 321,304.90 / 315,137.17 / 313,853.79 억원.

Cell-level fix with an OLD-VALUE GUARD: every cell is changed only if it still holds the value found on
2026-10-10; any other value aborts without writing.  Backup first, byte-exact round trip required,
the file is rewritten in its own format (CRLF, indent 2), every other row is left untouched.

Usage:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20261010_ilp_kr0009_paa_column.py [--write]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ILP = REPO / "insurance_liability_portfolio.json"
BACKUP = REPO / "data" / "_derived" / "ilp_backup_20261010_pre_kr0009.json"

CODE = "KR0009"
# (quarter, item) -> (old value, new value), all 억원
FIX = {
    ("2025.1Q", 4): (35579.0, 0.0), ("2025.1Q", 6): (9.0, 0.0), ("2025.1Q", 7): (0.0, 35579.0), ("2025.1Q", 8): (321314.0, 321305.0),
    ("2025.2Q", 4): (34878.0, 0.0), ("2025.2Q", 6): (10.0, 0.0), ("2025.2Q", 7): (0.0, 34878.0), ("2025.2Q", 8): (315147.0, 315137.0),
    ("2025.3Q", 4): (34991.0, 0.0), ("2025.3Q", 6): (9.0, 0.0), ("2025.3Q", 7): (0.0, 34991.0), ("2025.3Q", 8): (313863.0, 313854.0),
}


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
    idx = {}
    for i, r in enumerate(rows):
        if r["원보험사코드"] == CODE:
            idx[(r["공시분기"], r["항목번호"])] = i
    plan = []
    for key, (old, new) in sorted(FIX.items()):
        if key not in idx:
            raise SystemExit(f"abort: {CODE} {key} not found")
        cur = rows[idx[key]]["값"]
        if cur == new and old != new:
            print(f"already fixed: {CODE} {key} = {cur}")
            continue
        if float(cur) != old:
            raise SystemExit(f"abort (old-value guard): {CODE} {key} holds {cur}, expected {old}")
        plan.append((key, old, new))
    # identity check after the fix: item 8 == sum(items 1..7) for the three quarters
    for q in ("2025.1Q", "2025.2Q", "2025.3Q"):
        vals = {n: rows[idx[(q, n)]]["값"] for n in range(1, 9)}
        for (qq, n), (old, new) in FIX.items():
            if qq == q:
                vals[n] = new
        s7 = sum(vals[n] for n in range(1, 8))
        assert abs(s7 - vals[8]) < 1e-9, (q, s7, vals[8])
    print(f"{len(plan)} cell(s) to change:")
    for (q, n), old, new in plan:
        print(f"  {CODE} {q} item {n}: {old} -> {new}")
    if not args.write or not plan:
        print("dry run" if not args.write else "nothing to do")
        return 0
    if BACKUP.exists():
        raise SystemExit(f"abort: backup {BACKUP.name} already exists")
    shutil.copyfile(ILP, BACKUP)
    if hashlib.sha256(BACKUP.read_bytes()).hexdigest() != hashlib.sha256(raw0).hexdigest():
        raise SystemExit("abort: backup mismatch")
    new_rows = json.loads(txt)
    for (q, n), old, new in plan:
        new_rows[idx[(q, n)]]["값"] = new
    if ILP.read_bytes() != raw0:
        raise SystemExit("abort: file changed while preparing the fix")
    tmp = ILP.with_name(ILP.name + ".tmp")
    tmp.write_bytes(dump(new_rows).encode("utf-8"))
    os.replace(tmp, ILP)
    after = json.loads(ILP.read_text(encoding="utf-8"))
    changed = [(i, a, b) for i, (a, b) in enumerate(zip(rows, after)) if a != b]
    assert len(after) == len(rows) and len(changed) == len(plan), (len(changed), len(plan))
    print(f"wrote {ILP.name}; backup {BACKUP.name}; {len(changed)} rows changed, all others identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
