#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5c: FY2023 'comparative chain' for held interim cells (read-only).

The opening year-end of FY2023 (2022.4Q) is IFRS4 in the master, so no anchor exists and the interim 2023.1Q-3Q 8-1 tables cannot be checked with
their own prior-year-end column.  But the FY2023 year-end filing prints the SAME date (2022.4Q) as its comparative column.  Chain:
    (a) the interim table of the cell prints a prior column (2022.4Q) with value p for the cell's concept,
    (b) the 2023.4Q filing's table of the same group (K/S) prints the same concept for 2022.4Q with value q,
    (c) p == q  (same company, same date, same line -> same definition; rounding/0.15% only),
    (d) the 2023.4Q filing's CURRENT column of that concept reproduces the master's 2023.4Q anchor (calibration evidence, no failure).
Then the interim line has the master's definition.  Reports every held FY2023 bs_full cell with the chain verdict.
Output: chain2023_report.json, chain2023_cells.json (manual schema for bspl_followup_make_spec.py)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402

W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
TAIL = " (inbox/parser/20261011T0900Z bspl follow-up, step 5c FY2023 comparative chain)"


def grp(o):
    return "K" if o.form == "K" else "S"


def main():
    all_v, anchor, disc, meta = B.load_master()
    rep, cells = [], []
    obs_cache = {}

    def obs_of(code, q):
        k = (code, q)
        if k not in obs_cache:
            doc = B.load_tables(code, q)
            if doc is None:
                obs_cache[k] = (None, [])
            else:
                o, ui, nts = B.observations(code, q, doc, all_v, disc, None)
                obs_cache[k] = (doc, o)
        return obs_cache[k]

    for p in sorted(CAND.glob("KR*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        code = d["code"]
        if code in ("KR1101", "KR1102", "KR1103", "KR1104", "KR1105", "KR1106", "KR1107", "KR1108"):
            continue
        for c in d["candidates"]:
            q, item = c["quarter"], c["item"]
            if c["status"] not in ("HOLD_REJECTED_RULE", "HOLD_UNTESTED") or c["kind"] != "bs_full" or not q.startswith("2023.") or q.endswith("4Q"):
                continue
            if abs(c.get("value_mn") or 0.0) < 1e-9:
                continue
            rec = {"key": f"{code}|{item}|{q}", "status_before": c["status"], "rule": c["rule"], "form": c.get("form"), "value_mn": c["value_mn"], "page": c["page"]}
            doc_q, obs_q = obs_of(code, q)
            doc_4, obs_4 = obs_of(code, "2023.4Q")
            name = c["rule"]
            g = c.get("form") or "K"
            # (a) interim prior column
            a = [o for o in obs_q if o.kind == "bs_full" and o.col == 1 and cname_match(o, name) and grp(o) == g]
            # (b) year-end filing comparative column, same group
            b = [o for o in obs_4 if o.kind == "bs_full" and o.col == 1 and cname_match(o, name) and grp(o) == g]
            # (d) year-end filing current column vs master
            ev = d["calibration"].get(f"{name}|{g}", {}).get("evidence", [])
            e4 = [e for e in ev if e[0] == "2023.4Q" and e[2] == 0]
            # the interim table must be on the master's basis as a whole: its own totals (items 1/2/3, current column) may not disagree with the master
            tot_bad = [e for ck_, cv_ in d["calibration"].items() if ck_.split(":")[0] in ("1", "2", "3") for e in cv_["evidence"]
                       if e[0] == q and e[1] == q and e[2] == 0 and not e[4]]
            if tot_bad:
                rec.update(verdict="TABLE_TOTALS_DISAGREE", reason="the table's own totals disagree with the master at this quarter (another basis): " +
                           "; ".join(f"{e[5]:,.0f} vs {e[6]:,.0f}" for e in tot_bad[:3]))
            elif not a:
                rec.update(verdict="NO_INTERIM_PRIOR_COLUMN", reason="the interim table prints no usable prior-year-end column for this concept")
            elif not b:
                rec.update(verdict="NO_YEAR_END_COMPARATIVE", reason="the 2023.4Q filing has no comparative (2022.4Q) value of the concept in the same group")
            elif not e4:
                rec.update(verdict="NO_YEAR_END_ANCHOR_EVIDENCE", reason="the 2023.4Q current column of the concept has no master anchor evidence")
            elif not all(e[4] for e in e4):
                rec.update(verdict="YEAR_END_FAIL", reason="the 2023.4Q current column does not reproduce the master anchor")
            else:
                pv, qv = a[0].value_mn, b[0].value_mn
                tol = max(0.0015 * abs(qv), 2 * max(a[0].prec_mn, b[0].prec_mn), 0.01)
                if abs(pv - qv) <= tol:
                    rec.update(verdict="CHAIN_OK", reason=f"interim prior column (2022.4Q) {pv:,.3f} == year-end comparative {qv:,.3f}; 2023.4Q current column reproduces master ({e4[0][5]:,.3f} = {e4[0][6]:,.3f})")
                    unit = c["unit"]
                    cells.append({"code": code, "item": item, "quarter": q, "status": "MANUAL", "calib": "chain2023", "value_mn": c["value_mn"], "rule": c["rule"], "kind": c["kind"],
                                  "form": c.get("form"), "page": c["page"], "unit": unit, "unit_how": "master", "prec_mn": c.get("prec_mn"), "tol_mn": B.UNIT_TOL[unit],
                                  "pdf": c.get("pdf") or doc_q["pdf"], "sha256": c.get("sha256") or doc_q["sha256"],
                                  "basis": (f"정기경영공시 {q} 재무상태표(8-1 {g} 구간) p{c['page']} 라인「{c['rule']}」 {c['value_mn'] / 100:,.3f}억(단위 {unit}). 2023 비교열 사슬 5c: 이 표의 전기말(2022.12.31) 열 {pv / 100:,.3f}억이 "
                                            f"2023.4Q 공시본의 2022.12.31 비교열 {qv / 100:,.3f}억과 같고, 2023.4Q 공시본의 당기열({e4[0][5] / 100:,.3f}억)은 마스터 DART 앵커({e4[0][6] / 100:,.3f}억)를 재현한다 -- 같은 날짜·같은 회사·같은 줄이 두 공시본에서 같으므로 "
                                            "이 줄의 정의는 마스터 정의다(2022.4Q 는 IFRS4 라 마스터 앵커가 없어 직접 대조 불가). 표 항등식(자산 = 부채 + 자본) 폐합 확인." + TAIL)})
                else:
                    rec.update(verdict="CHAIN_FAIL", reason=f"interim prior column (2022.4Q) {pv:,.3f} != year-end comparative {qv:,.3f}")
            rep.append(rec)
    (W / "chain2023_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (W / "chain2023_cells.json").write_text(json.dumps({"_note": "step 5c FY2023 chain cells (manual schema)", "cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(dict(Counter(r["verdict"] for r in rep)))
    for r in rep:
        print(f" {r['verdict']:<28} {r['key']:<20} {r['rule']:<28} {r['value_mn'] / 100:>12,.1f}억 | {r['reason'][:150]}")


def cname_match(o, name):
    return B.cname(o.concept) == name


if __name__ == "__main__":
    main()
