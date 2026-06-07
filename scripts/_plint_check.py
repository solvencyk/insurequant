# -*- coding: utf-8 -*-
"""Scratch integration check for the PL Tier-2 sweep (read-only on the master JSON).

(B) 12-new-company self-check table: code | item4 5 6 9 10 11 | item1(stored) |
    reconstructed | %gap | PASS/FAIL.  Reconstruction = item2 + item13 + item14
    + item15 - item16  (the identity every probe validated).  For companies whose
    own-company 보험손익 excludes 기타사업비용 (note 총 == 보험손익) item16 is netted
    to 0 inside the note; we read item16 from the master (assemble's value).
(C) spot-check item1 for golds + the already-OK life companies.
(D) before/after item1 for the 4 Tier-1-fixed codes.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
M = json.loads(Path("data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))
Q = "2025.4Q"

vals = {}
names = {}
for r in M:
    if r["공시분기"] != Q:
        continue
    vals.setdefault(r["원보험사코드"], {})[r["항목번호"]] = r["값"]
    names[r["원보험사코드"]] = r["원수사명"]


def g(code, n):
    return vals.get(code, {}).get(n)


def fmt(x):
    return "None" if x is None else f"{x:,.0f}"


# ---- (B) 12-new-company self-check ---------------------------------------- #
NEW = ["KR0010", "KR0009", "KR0002", "KR0011", "KR0032", "KR0003", "KR1000",
       "KR0073", "KR0082", "KR0087", "KR0094", "KR0104", "KR0071", "KR0072",
       "KR0079", "KR0083"]
# item16 the own-company 보험손익 line nets (probe-established). Where the 보험손익 line
# EXCLUDES 기타사업비용 (note 총 == 보험손익) item16=0 in the identity; else the note/IS
# 기타사업비용. None => use master item16.
ITEM16_RECON = {
    "KR0010": 0.0,        # KB: note 총 보험서비스결과 == 보험손익 (기타사업비용 outside)
    "KR0009": 0.0,        # 현대: LOB summary 합계 == 보험손익
    "KR0002": 128958.0,   # 한화손해: 보험손익 includes 기타사업비용 deduction (note 천원)
    "KR0011": 211736.0,   # DB
    "KR0003": 38023.0,    # 롯데: compact IS omits 기타사업비용 (from note)
    "KR1000": 94514.0,    # 코리안리
}
print("=" * 110)
print("(B) NEW-COMPANY SELF-CHECK  (recon = item2+13+14+15-16  vs stored item1)")
print("=" * 110)
hdr = (f"{'code':<8}{'item4':>12}{'item5':>11}{'item6':>11}{'item9':>10}"
       f"{'item10':>10}{'item11':>10}{'item1(st)':>12}{'recon':>12}{'%gap':>8}  verdict")
print(hdr)
for code in NEW:
    i1 = g(code, 1)
    i2 = g(code, 2)
    i13 = g(code, 13) or 0
    i14 = g(code, 14) or 0
    i15 = g(code, 15) or 0
    i16 = ITEM16_RECON.get(code, g(code, 16) or 0)
    recon = None
    if i2 is not None:
        recon = i2 + i13 + i14 + i15 - i16
    gap = None
    if recon is not None and i1:
        gap = (recon - i1) / abs(i1) * 100
    verdict = "n/a"
    if gap is not None:
        verdict = "PASS" if abs(gap) <= 1.0 else "FAIL"
    gaps = "None" if gap is None else f"{gap:.3f}"
    print(f"{code:<8}{fmt(g(code,4)):>12}{fmt(g(code,5)):>11}{fmt(g(code,6)):>11}"
          f"{fmt(g(code,9)):>10}{fmt(g(code,10)):>10}{fmt(g(code,11)):>10}"
          f"{fmt(i1):>12}{fmt(recon):>12}{gaps:>8}  {verdict}")

# populated-items check (items 4,5,9,10 must be present for all; 6/11 where applicable)
print("\nPopulated-items check (4,5,9,10 required; 6/11 N/A: NH=6/11, 미래에셋=6/11):")
for code in NEW:
    miss = [n for n in (4, 5, 9, 10) if g(code, n) is None]
    note = ""
    if code == "KR0032":
        note = " (NH: item6/11 N/A by design)"
    if code == "KR0079":
        note = " (미래에셋: item6/11 N/A by design)"
    print(f"  {code}: missing core {miss}{note}")

# ---- (C) spot-check (must be unchanged) ----------------------------------- #
print("\n" + "=" * 70)
print("(C) SPOT-CHECK item1 (golds + already-OK life — should be UNCHANGED)")
print("=" * 70)
SPOT = {
    "KR0008": 1483034.088528, "KR0001": 1426994.645423,
    "KR0069": 981030.0, "KR0068": 344419.0,
    "KR0082": 125973.153048, "KR0072": -12715.584004, "KR0071": 102102.65244,
    "KR0104": 389177.046593, "KR0087": 113771.0, "KR0094": 704153.0,
}
for code, base in SPOT.items():
    cur = g(code, 1)
    same = (cur is not None and abs(cur - base) < 0.5)
    print(f"  {code} {names.get(code,''):<8}  before={fmt(base):>14}  after={fmt(cur):>14}"
          f"  {'UNCHANGED' if same else 'CHANGED <--'}")

# ---- (D) before/after for the 4 Tier-1-fixed codes ------------------------ #
print("\n" + "=" * 70)
print("(D) BEFORE/AFTER item1 for the 4 Tier-1-fixed codes")
print("=" * 70)
FIX = {
    "KR0009": (809045.654167, 396111.0),
    "KR0002": (206.270457, 206270.0),
    "KR1000": (226495.640541, 223754.0),
    "KR0073": (371583.485213, 391590.0),
}
for code, (before, target) in FIX.items():
    cur = g(code, 1)
    ok = (cur is not None and abs(cur - target) <= max(1.0, 0.005 * abs(target)))
    print(f"  {code} {names.get(code,''):<8}  before={fmt(before):>14}  "
          f"after={fmt(cur):>14}  target={fmt(target):>12}  {'OK' if ok else 'BAD <--'}")
