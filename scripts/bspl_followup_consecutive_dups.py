#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 3: consecutive-quarter duplicate scan of IFRS17_BS.json and PL_breakdown.json.

For every (company, item) the quarters are sorted; two CONSECUTIVE calendar quarters with the exact same value (0 and missing excluded;
BS items 5-8 are excluded because validation R_RSV_1 already covers them) form a duplicate; runs of 3+ are merged into one record.
PL: the cumulative 값 (YTD) AND the 값_당분기 are scanned (a YTD value that repeats is a copy unless the item had no activity; a Q4 -> next
Q1 repeat is always a copy because a 12-month and a 3-month figure cannot coincide).

The record carries provenance flags (sidecar / overlay / PL provenance / FS-API cache availability) and an item-nature class:
  CONSTANT_LINE   a line that legitimately stays put (자본금 30, 차입부채 23, 투자계약부채 22 when 0-ish) -> still listed, needs a source reason
  MOVING_BALANCE  a balance that moves every quarter (totals, 현금, 금융자산, 부채, 이익잉여금, AOCI ...) -> suspect
  PL_FLOW         a PL YTD / 당분기 flow
Output: data/_derived/bspl_granularity_20261011/consecutive_duplicates_20261011.json  (the path the ticket names; also a copy in
bspl_followup_20261011/).  Read-only on the masters.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

OUT_TICKET = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "consecutive_duplicates_20261011.json"
OUT_COPY = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "consecutive_duplicates_20261011.json"
BS_SKIP = {5, 6, 7, 8}
CONSTANT_BS = {30: "자본금", 23: "차입부채", 22: "투자계약부채"}


def qidx(q: str) -> int:
    y, n = q.split(".")
    return int(y) * 4 + int(n[0]) - 1


def runs(series):
    """series: {quarter: value} -> list of runs [(q_start..q_end, value)] of consecutive calendar quarters with equal non-zero value"""
    qs = sorted(series, key=qidx)
    out, cur = [], None
    for q in qs:
        v = series[q]
        if v is None or v == 0:
            cur = None
            continue
        if cur and qidx(q) == qidx(cur["qs"][-1]) + 1 and v == cur["v"]:
            cur["qs"].append(q)
        else:
            if cur and len(cur["qs"]) >= 2:
                out.append(cur)
            cur = {"qs": [q], "v": v}
    if cur and len(cur["qs"]) >= 2:
        out.append(cur)
    return out


def main():
    before = "--before" in sys.argv        # scan the pre-follow-up baseline copies (data/_derived/bspl_followup_backup_20261011/baseline)
    base = ROOT / "data" / "_derived" / "bspl_followup_backup_20261011" / "baseline" if before else ROOT
    bs = json.loads((base / "IFRS17_BS.json").read_text(encoding="utf-8"))
    pl = json.loads((base / "PL_breakdown.json").read_text(encoding="utf-8"))
    side = json.loads((ROOT / "data" / "_derived" / "bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
    ov = json.loads((ROOT / "data" / "dart" / "viz" / "bs_manual_overrides.json").read_text(encoding="utf-8"))["cells"]
    carry = json.loads((ROOT / "data" / "_derived" / "bs_carry_forward_cells.json").read_text(encoding="utf-8"))
    plprov = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
    res = []
    # ---- BS ----
    g = defaultdict(dict)
    meta = {}
    for r in bs:
        if r["항목번호"] in BS_SKIP:
            continue
        g[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
        meta[r["원보험사코드"]] = r["원수사명"]
        meta[(r["원보험사코드"], r["항목번호"])] = r["항목명"]
    for (code, item), series in sorted(g.items()):
        for run in runs(series):
            qs = run["qs"]
            res.append({"master": "BS", "code": code, "name": meta[code], "item": item, "item_name": meta[(code, item)],
                        "field": "값", "quarters": qs, "value": run["v"], "run_length": len(qs),
                        "class": "CONSTANT_LINE" if item in CONSTANT_BS else "MOVING_BALANCE",
                        "sidecar_quarters": [q for q in qs if f"{code}|{item}|{q}" in side],
                        "overlay_quarters": [q for q in qs if f"{code}|{item}|{q}" in ov],
                        "carry_forward_flag": bool([q for q in qs if q in (carry.get("companies", {}).get(code) or [])])})
    # ---- PL ----
    gp = defaultdict(lambda: defaultdict(dict))
    for r in pl:
        k = (r["원보험사코드"], r["항목번호"])
        gp[k]["값"][r["공시분기"]] = r.get("값")
        gp[k]["값_당분기"][r["공시분기"]] = r.get("값_당분기")
        meta[r["원보험사코드"]] = r["원수사명"]
        meta[("PL", r["항목번호"])] = r["항목명"]
    for (code, item), fields in sorted(gp.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
        for fld, series in fields.items():
            for run in runs(series):
                qs = run["qs"]
                cross_fy = any(qs[i].endswith("4Q") for i in range(len(qs) - 1))        # Q4 -> next Q1 repeat
                res.append({"master": "PL", "code": code, "name": meta[code], "item": item, "item_name": meta[("PL", item)],
                            "field": fld, "quarters": qs, "value": run["v"], "run_length": len(qs), "class": "PL_FLOW",
                            "q4_to_q1_repeat": cross_fy})
    res.sort(key=lambda r: (r["master"], r["code"], str(r["item"]), r["field"], qidx(r["quarters"][0])))
    payload = {"_what": "consecutive-calendar-quarter exact-equal non-zero values (BS items 5-8 excluded: R_RSV_1); runs of 3+ merged",
               "counts": {"BS": sum(1 for r in res if r["master"] == "BS"), "PL": sum(1 for r in res if r["master"] == "PL")},
               "records": res}
    outs = (OUT_COPY.with_name("consecutive_duplicates_before_20261011.json"),) if before else (OUT_TICKET, OUT_COPY)
    for p in outs:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("records", payload["counts"])
    bsr = [r for r in res if r["master"] == "BS"]
    by_item = defaultdict(int)
    for r in bsr:
        by_item[r["item"]] += 1
    print("BS by item:", dict(sorted(by_item.items())))
    plr = [r for r in res if r["master"] == "PL"]
    by_pi = defaultdict(int)
    for r in plr:
        by_pi[(r["item"], r["field"])] += 1
    print("PL by (item, field):", dict(sorted(by_pi.items(), key=lambda kv: (str(kv[0][0]), kv[0][1]))))


if __name__ == "__main__":
    main()
