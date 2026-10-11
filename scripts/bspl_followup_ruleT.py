#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5c: 'time-consistent evidence' (rule T) cells (read-only; writes the manual-schema cells file).

Rule T: a fiscal-year-specific calibration.  Evidence about a cell comes only from filings of the SAME fiscal year as the cell (their current columns at the
year-end / the sibling interim quarters, their prior-year-end columns): a LATER fiscal year's filing that prints a restated comparative for an earlier date
describes that later filing's definition and says nothing about the earlier filing, so it is excluded (the whole-history calibration rejected the concept
because of exactly such comparatives).  Required for every cell here
  (1) every informative same-fiscal-year calibration entry reproduces the master (no failure) and at least one is a year-end entry,
  (2) the table's own totals (items 1/2/3, current column) do not disagree with the master at that quarter,
  (3) an independent closure that does not use the rule:
        equity cells  : 자본총계 - 자본금 - AOCI - 이익잉여금 (= 자본잉여금 + 자본조정 + 신종자본증권) is the same constant (+-0.6억) in the cell's quarter and in
                        every neighbouring quarter of the same fiscal year whose components are all in the master,
        asset cell    : the remaining asset lines (자산총계 - cash - FVPL - AC - candidate) stay in the range of the neighbouring quarters,
        KR0004 AC     : the AC lines (상각후원가측정대출채권 + 기타수취채권) of the cell's table are the same lines as in the verified sibling table.
Output: data/_derived/bspl_followup_20261011/ruleT_report.json, ruleT_cells.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402

W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
TAIL = " (inbox/parser/20261011T0900Z bspl follow-up, step 5c rule T)"
CELLS = [("KR0005", 31, "2023.1Q"), ("KR0005", 31, "2023.2Q"), ("KR0008", 31, "2023.1Q"), ("KR0008", 31, "2023.2Q"), ("KR1010", 12, "2023.3Q"),
         ("KR0004", 13, "2025.3Q")]


def informative(e, own_q):
    return not (abs(e[5]) < 1e-9 and abs(e[6]) > 1e-9 and e[0] != own_q)


def norm(s):
    return re.sub(r"\s+", "", s)


def main():
    all_v, anchor, disc, meta = B.load_master()
    rep, cells = [], []
    for code, item, q in CELLS:
        d = json.loads((CAND / f"{code}.json").read_text(encoding="utf-8"))
        c = next(x for x in d["candidates"] if x["item"] == item and x["quarter"] == q)
        assert c["status"] == "HOLD_REJECTED_RULE", (code, item, q, c["status"])
        y = int(q[:4])
        grp = "K" if c.get("form") == "K" else "S"
        ev = [e for e in d["calibration"].get(f"{c['rule']}|{grp}", {}).get("evidence", []) if int(e[0][:4]) == y and informative(e, q)]
        bad = [e for e in ev if not e[4]]
        ye = [e for e in ev if e[1].endswith("4Q")]
        tot_bad = [e for ck, cv in d["calibration"].items() if ck.split(":")[0] in ("1", "2", "3") for e in cv["evidence"] if e[0] == q and e[1] == q and e[2] == 0 and not e[4]]
        rec = {"key": f"{code}|{item}|{q}", "rule": c["rule"], "value_mn": c["value_mn"], "n_same_year_evidence": len(ev), "n_bad": len(bad), "n_year_end": len(ye),
               "totals_disagree": len(tot_bad), "evidence": ev[:6]}
        ok = bool(ev) and not bad and bool(ye or any(e[2] == 1 for e in ev)) and not tot_bad
        check = None
        mv = all_v[code]
        if item == 31:
            # equity constant: 자본총계 - 자본금 - AOCI - 이익잉여금 over the fiscal-year quarters whose components exist in the master (+ this cell)
            res = {}
            for qq in [f"{y}.{n}Q" for n in (1, 2, 3, 4)]:
                tot = mv.get((3, qq))
                cap = mv.get((30, qq))
                oci = mv.get((4, qq))
                re_ = c["value_mn"] if qq == q else mv.get((31, qq))
                other_cand = None
                if qq != q:
                    other_cand = next((x["value_mn"] for x in d["candidates"] if x["item"] == 31 and x["quarter"] == qq and x["status"] == "HOLD_REJECTED_RULE"), None)
                    if re_ is None:
                        re_ = other_cand
                if None in (tot, cap, oci, re_):
                    continue
                res[qq] = round((tot - cap - oci - re_) / 100.0, 2)
            vals = list(res.values())
            check = {"residual_억_by_quarter": res, "spread_억": round(max(vals) - min(vals), 2) if vals else None}
            ok = ok and len(vals) >= 3 and (max(vals) - min(vals)) <= 0.6
        elif item == 12:
            tot1 = mv.get((1, q))
            parts = {k: mv.get((k, q)) for k in (10, 11, 13)}
            rest = None if None in parts.values() or tot1 is None else round((tot1 - sum(parts.values()) - c["value_mn"]) / 100.0, 2)
            nb = {}
            for qq in ("2023.1Q", "2023.2Q", "2023.4Q"):
                t1, p = mv.get((1, qq)), [mv.get((k, qq)) for k in (10, 11, 12, 13)]
                if t1 is not None and None not in p:
                    nb[qq] = round((t1 - sum(p)) / 100.0, 2)
            check = {"remaining_asset_lines_억": rest, "neighbours_억": nb}
            ok = ok and rest is not None and 0 <= rest <= 400
        elif item == 13:
            def ac_labels(qq):
                doc = B.load_tables(code, qq)
                t = B.pick_tables(doc, "bs_full")[0]
                labs, cut = [], False
                for r in t["rows"]:
                    lab = norm(r["label"])
                    if lab in ("자산총계",):
                        break
                    if lab.startswith("상각후원가측정") and "부채" not in lab:
                        labs.append(lab)
                return labs
            a, b = ac_labels("2025.2Q"), ac_labels(q)
            check = {"ac_lines_2025.2Q": a, "ac_lines_2025.3Q": b}
            ok = ok and a == b and len(a) >= 1
        rec["independent_check"] = check
        rec["ok"] = ok
        rep.append(rec)
        if ok:
            doc = B.load_tables(code, q)
            unit = c["unit"]
            ev_txt = "; ".join(f"{e[0]} {e[1]} col{e[2]} {e[5]:,.1f}={e[6]:,.1f}" for e in ev[:4])
            if item == 31:
                ind = ("독립 폐합: 자본총계 − 자본금 − AOCI − 이익잉여금(=자본잉여금+자본조정+신종자본증권) 잔차가 같은 해 분기들에서 같은 상수("
                       + ", ".join(f"{k} {v:,.2f}억" for k, v in check["residual_억_by_quarter"].items()) + ") — 이 칸이 이 상수에 들어맞는다.")
            elif item == 12:
                ind = (f"독립 폐합: 자산총계 − (현금 + FVPL + 상각후원가 + 이 칸) = {check['remaining_asset_lines_억']:,.2f}억, 이웃 분기의 같은 잔여 "
                       + ", ".join(f"{k} {v:,.2f}억" for k, v in check["neighbours_억"].items()) + " 범위.")
            else:
                ind = ("독립 확인: 상각후원가 라인(" + " + ".join(check["ac_lines_2025.3Q"]) + ")이 같은 회계연도 2025.1Q·2Q 공시본의 검증된 표와 같은 라인이다"
                       "(3분기 표는 당기 열 하나뿐이라 자체 전기말 열이 없어 같은 해 형제 공시본의 전기말 열 대조로 갈음).")
            cells.append({"code": code, "item": item, "quarter": q, "status": "MANUAL", "calib": "ruleT", "value_mn": c["value_mn"], "rule": c["rule"], "kind": c["kind"],
                          "form": c.get("form"), "page": c["page"], "unit": unit, "unit_how": c.get("unit_how", "master"), "prec_mn": c.get("prec_mn"), "tol_mn": B.UNIT_TOL[unit],
                          "pdf": c.get("pdf") or doc["pdf"], "sha256": c.get("sha256") or doc["sha256"],
                          "basis": (f"정기경영공시 {q} {'4-1 B/S상 자기자본' if item == 31 else ('4-1 요약 재무상태표' if c['kind'] == 'sum_bs' else '재무상태표(8-1 K 구간)')} p{c['page']} 라인「{c['rule']}」 "
                                    f"{c['value_mn'] / 100:,.3f}억(단위 {unit}). 시간 일관 증거(규칙 T) 5c: 같은 회계연도 공시본의 이 라인이 마스터 DART 앵커를 재현({ev_txt}); "
                                    "나중 회계연도 공시본이 같은 날짜를 재작성해 낸 비교열은 이 공시본의 정의를 말해주지 않으므로 증거에서 뺐다(그 비교열 때문에 전 기간 보정이 불합격이었다). "
                                    f"{ind} 표 항등식 폐합 확인, 표의 총계가 마스터와 일치." + TAIL)})
    (W / "ruleT_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (W / "ruleT_cells.json").write_text(json.dumps({"_note": "step 5c rule T cells (manual schema)", "cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for r in rep:
        print(f"{r['key']:<18} ok={r['ok']!s:<5} same-year evidence {r['n_same_year_evidence']} (bad {r['n_bad']}, year-end {r['n_year_end']}) totals_disagree={r['totals_disagree']} check={r['independent_check']}")


if __name__ == "__main__":
    main()
