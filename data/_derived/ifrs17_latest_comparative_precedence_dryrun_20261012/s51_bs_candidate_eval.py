"""Read-only dry run, IFRS17_BS domain (year-end main items) : current master vs LATEST comparative column (next annual report's prior-year-end column).

Inputs   bs_4q_scan.csv (s18)
Unit     block = (company, year-end quarter): items 1 자산총계, 2 부채총계, 3 자본총계, 4 AOCI, 14 재보험계약자산, 20 보험계약부채,
         21 재보험계약부채, 30 자본금, 31 이익잉여금 are replaced together (only the cells the later column prints; others keep the master value).
Closure  B1  1 자산총계 = 2 부채총계 + 3 자본총계       tol max(0.01% x |1|, 200백만)      (balance sheet identity)
         B2  20 <= 2 and 21 <= 2 and 14 <= 1 (component never exceeds its total; sign/scale sanity)
         The equity statement / reserve / K-ICS cross-checks (data_contract 17BS<->K-ICS) are not re-run per candidate (see summary: rule blind spots).
Overlay  a candidate cell that is also a cell of data/dart/viz/bs_manual_overrides.json (disclosure fills, owner fixes) -> 'overlay 충돌'.
Output   bs_block_verdicts.csv
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lib_dryrun as D  # noqa: E402

ROOT = D.ROOT
rows = list(csv.DictReader(open(HERE / "bs_4q_scan.csv", encoding="utf-8-sig")))
bs = D.load_json("IFRS17_BS.json")
M = defaultdict(dict)
NAMES = {}
for r in bs:
    M[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]
    NAMES[r["원보험사코드"]] = r["원수사명"]
overlay = D.load_json("data/dart/viz/bs_manual_overrides.json")["cells"]
restated_reg = D.load_json("data/_gold/bs_restated_cells.json")["cells"]


def f(x):
    try:
        return float(x)
    except Exception:
        return None


def ident(v):
    out = {}
    a, l, e = v.get(1), v.get(2), v.get(3)
    out["B1_A=L+E"] = None if None in (a, l, e) else abs(a - (l + e)) <= max(1e-4 * abs(a), 200.0)
    ok = True
    for sub, tot in ((20, 2), (21, 2), (14, 1)):
        if v.get(sub) is not None and v.get(tot) is not None and v[sub] > v[tot] + 1e-6 and v[tot] > 0 and v[sub] > 0:
            ok = False
    out["B2_component<=total"] = ok
    return out


blocks = defaultdict(dict)
for r in rows:
    blocks[(r["kr"], r["quarter"])][int(r["item"])] = r

out = []
cnt = Counter()
cells = Counter()
for (kr, q), items in sorted(blocks.items()):
    stale = {it: r for it, r in items.items() if r["cls"] == "RESTATED_STALE"}
    adopted = {it for it, r in items.items() if r["cls"] == "RESTATED_ADOPTED"}
    neq = {it for it, r in items.items() if r["cls"] == "MASTER_NEQ_ORIG"}
    if not (stale or adopted or neq):
        continue
    cur = {it: M[(kr, q)].get(it) for it in (1, 2, 3, 4, 14, 20, 21, 30, 31)}
    lat = dict(cur)
    for it, r in stale.items():
        lv = f(r["later"])
        if lv is not None:
            lat[it] = lv
    row = {"domain": "IFRS17_BS(year-end)", "kr": kr, "name": NAMES.get(kr, ""), "quarter": q, "later_filing_q": f"{int(q[:4])+1}.4Q",
           "n_stale_cells": len(stale), "stale_items": ",".join(map(str, sorted(stale))),
           "n_already_latest": len(adopted), "n_master_neq_orig": len(neq)}
    for it in (1, 2, 3, 20):
        if it in stale:
            row[f"item{it}_current"] = stale[it]["master"]
            row[f"item{it}_latest"] = stale[it]["later"]
    ic, il = ident(cur), ident(lat)
    row["identities_current"] = json.dumps(ic, ensure_ascii=False)
    row["identities_latest"] = json.dumps(il, ensure_ascii=False)
    closed_cur = all(v is not False for v in ic.values())
    closed_lat = all(v is not False for v in il.values())
    hit = [it for it in stale if f"{kr}|{it}|{q}" in overlay]
    row["overlay_cells"] = ",".join(map(str, hit))
    if hit:
        row["verdict"] = "overlay 충돌"
    elif stale:
        if closed_lat and closed_cur:
            row["verdict"] = "최신 채택(진짜 재작성 †)"
        elif closed_lat and not closed_cur:
            row["verdict"] = "최신 채택(예외 해소)"
        elif (not closed_lat) and closed_cur:
            row["verdict"] = "현행 유지"
        else:
            row["verdict"] = "둘 다 불가"
    elif adopted:
        row["verdict"] = "이미 최신(이전 라운드 채택)"
    else:
        row["verdict"] = "마스터가 원본·최신 둘 다와 다름(오버라이드)"
    out.append(row)
    cnt[row["verdict"]] += 1
    cells[row["verdict"]] += len(stale)

cols = ["domain", "kr", "name", "quarter", "later_filing_q", "n_stale_cells", "stale_items", "n_already_latest", "n_master_neq_orig",
        "item1_current", "item1_latest", "item2_current", "item2_latest", "item3_current", "item3_latest", "item20_current", "item20_latest",
        "identities_current", "identities_latest", "overlay_cells", "verdict"]
with open(HERE / "bs_block_verdicts.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(out)
print("BS year-end blocks:", len(out), dict(cnt))
print("stale cells by verdict:", dict(cells))
print("blocks scanned (company x year-end with a later annual):", len(blocks))
