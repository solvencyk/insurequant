# -*- coding: utf-8 -*-
"""pass2 s08 (read-only): for candidate gold cells print the builder source value (data/dart/viz/pl_breakdown_master.json), the live master value and the existing gold value -> masked-gold check (a gold value equal to the source needs a ledger pin).
usage: s08_src_check.py"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
src = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{ROOT}/data/dart/viz/pl_breakdown_master.json", encoding="utf-8"))}
live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
gold = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))["set"]}
CELLS = []
for q in ("2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q"):
    for i in (5, 7, 9, 10, 12):
        CELLS.append(("KR0070", i, q))
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    for i in (11, 12):
        CELLS.append(("KR0070", i, q))
for q in ("2024.2Q", "2024.3Q"):
    for i in (5, 6, 7):
        CELLS.append(("KR0087", i, q))
for q in ("2023.1Q", "2023.2Q"):
    for i in (5, 9, 10):
        CELLS.append(("KR0009", i, q))
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    for i in (5, 6, 7, 9, 10, 11, 12):
        CELLS.append(("KR0068", i, q))
for q in ("2024.3Q", "2024.4Q"):
    CELLS.append(("KR0005", 16, q))
for code in ("KR0032",):
    for i in range(25, 33):
        CELLS.append((code, i, "2023.1Q"))
for code in ("KR0082",):
    for q in ("2023.1Q", "2023.2Q"):
        for i in range(25, 33):
            CELLS.append((code, i, q))
print("code item quarter | source | live | gold")
for k in CELLS:
    s, l, g = src.get(k), live.get(k), gold.get(k)
    print(f"{k[0]} {k[1]:>2} {k[2]} | src={'ROW_ABSENT' if s is None else s.get('값')} | live={'ROW_ABSENT' if l is None else l.get('값')} | gold={None if g is None else g['값']}")
