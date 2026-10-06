"""Repo-wide scan for the KR0032 slot-shift signature in kics_disclosure.json.

Signature A: item7 (이익잉여금) == 0 while item8 (자본조정) != 0
             -> retained earnings almost certainly landed in the 자본조정 slot.
Signature B: item9 (AOCI) == 0 while item10 (비지배지분) != 0
             -> AOCI almost certainly landed in the 비지배지분 slot.
Signature C: item7 == 0 on its own (retained earnings genuinely zero is rare).

Also replays the current extractor for every (company, quarter) hit so we can see
whether today's code already produces the right answer (= stale master row).
"""
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from solvency.parser.kics_baseline_match import match_baseline_value_or_zero  # noqa: E402
from solvency.parser.kics_disclosure_parser import (  # noqa: E402
    build_label_lookups,
    extract_kics_detail_rows,
)

with open(REPO / "kics_disclosure.json", encoding="utf-8") as f:
    kics = json.load(f)


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


cell = {}
name = {}
for r in kics:
    try:
        it = int(r["항목번호"])
    except (TypeError, ValueError, KeyError):
        continue
    key = (r.get("원보험사코드"), r.get("공시분기"))
    cell.setdefault(key, {})[it] = num(r.get("값"))
    name[(r.get("원보험사코드"))] = r.get("원수사명")

sigA, sigB, sigC = [], [], []
for key in sorted(cell):
    d = cell[key]
    i7, i8, i9, i10 = d.get(7), d.get(8), d.get(9), d.get(10)
    if i7 is not None and abs(i7) < 1 and i8 is not None and abs(i8) >= 1:
        sigA.append(key)
    if i9 is not None and abs(i9) < 1 and i10 is not None and abs(i10) >= 1:
        sigB.append(key)
    if i7 is not None and abs(i7) < 1:
        sigC.append(key)

print("=" * 90)
print(f"Signature A  item7==0 & item8!=0   : {len(sigA)} buckets")
for k in sigA:
    d = cell[k]
    print(f"   {k[0]} {name.get(k[0],''):<16} {k[1]}  item7={d.get(7)} item8={d.get(8)} "
          f"item9={d.get(9)} item10={d.get(10)} item11={d.get(11)}")
print()
print(f"Signature B  item9==0 & item10!=0  : {len(sigB)} buckets")
for k in sigB:
    d = cell[k]
    print(f"   {k[0]} {name.get(k[0],''):<16} {k[1]}  item7={d.get(7)} item8={d.get(8)} "
          f"item9={d.get(9)} item10={d.get(10)} item11={d.get(11)}")
print()
print(f"Signature C  item7==0 (any)        : {len(sigC)} buckets")
byco = defaultdict(list)
for k in sigC:
    byco[k[0]].append(k[1])
for co, qs in sorted(byco.items()):
    print(f"   {co} {name.get(co,''):<18} n={len(qs):>2}  {sorted(qs)}")

# ---- replay today's extractor on the union of hits --------------------------
PERIOD = {}
for p in sorted((REPO / "md_inbox").glob("FY*_Q?")):
    y, q = p.name[2:6], p.name[-1]
    PERIOD[f"{y}.{q}Q"] = p

BASE = [(4, "Ⅰ. 건전성감독기준 재무상태표 상의 순자산"), (5, "1. 보통주"),
        (6, "2. 자본항목 중 보통주 이외의 자본증권"), (7, "3. 이익잉여금"),
        (8, "4. 자본조정"), (9, "5. 기타포괄손익누계액"),
        (10, "6. 비지배지분"), (11, "7. 조정준비금")]

print()
print("=" * 90)
print("Replay of TODAY's extractor on every Signature-A/B bucket")
for k in sorted(set(sigA) | set(sigB)):
    code, q = k
    pdir = PERIOD.get(q)
    if pdir is None:
        print(f"   {code} {q}: no md_inbox period dir")
        continue
    mds = sorted(pdir.glob(f"{code}_*.md"))
    if not mds:
        print(f"   {code} {q}: no MD file")
        continue
    table = extract_kics_detail_rows(mds[0].read_text(encoding="utf-8"), q)
    lookup, core = build_label_lookups(table)
    got = {it: match_baseline_value_or_zero(nm, lookup, core, table) for it, nm in BASE}
    d = cell[k]
    print(f"   {code} {name.get(code,''):<16} {q}  md={mds[0].name}  pairs={len(table)}")
    for it, _nm in BASE:
        master = d.get(it)
        fresh = got[it]
        flag = ""
        if fresh is not None and master is not None and abs(num(fresh) - master) >= 1:
            flag = "   <== MASTER DISAGREES WITH TODAY'S EXTRACTOR"
        print(f"        item{it:>3}  master={str(master):>10}  today={str(fresh):>10}{flag}")
