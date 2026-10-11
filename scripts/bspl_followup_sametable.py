#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5c: SAME-TABLE calibration of held BS cells.

A filing's balance sheet prints [current, prior year-end] with ONE definition per line.  When the prior-year-end column of THIS filing reproduces
the master's own anchor of that year-end (DART / audit value) for the same concept, the line of this filing has the master's definition, and so
has its current column -- no matter whether some LATER filing restated the same comparative (which is what rejected the concept globally in
Stage B).  Conversely, when the filing's own prior column disagrees with the anchor, the master's anchor is on another definition than the
filing's line (restatement / separate-account inclusion / aggregation): the cell stays held.
Candidates: every HOLD_REJECTED_RULE / HOLD_UNTESTED nonzero cell of kind bs_full.  The prior-year-end anchor must be a DART/owner cell (not from
the disclosure sidecar) and not 2022.4Q (IFRS4).  Also reported: how many held cells pass / fail / have no own-filing comparative.
Output: sametable_report.json, sametable_cells.json (manual schema).  Read-only.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402

W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
TAIL = " (inbox/parser/20261011T0900Z bspl follow-up, step 5c same-table calibration)"


def main():
    all_v, anchor, disc, meta = B.load_master()
    rep, cells = [], []
    for p in sorted(CAND.glob("KR*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        code = d["code"]
        for c in d["candidates"]:
            if c["status"] not in ("HOLD_REJECTED_RULE", "HOLD_UNTESTED") or abs(c.get("value_mn") or 0.0) < 1e-9:
                continue
            q, item = c["quarter"], c["item"]
            rec = {"key": f"{code}|{item}|{q}", "status_before": c["status"], "rule": c["rule"], "kind": c["kind"], "form": c.get("form"), "value_mn": c["value_mn"]}
            if c["kind"] != "bs_full":
                rec.update(verdict="SKIP", reason="not an 8-1 statement line (supervisory summary / equity table: no prior-year-end column)")
                rep.append(rec)
                continue
            grp = c.get("form") or "K"
            ckey = f"{c['rule']}|{grp}"
            ev = d["calibration"].get(ckey, {}).get("evidence", [])
            own_c1 = [e for e in ev if e[0] == q and e[2] == 1]
            own_c0 = [e for e in ev if e[0] == q and e[2] == 0]
            # the table must be on the master's basis as a whole: its own totals (items 1/2/3, current column) may not disagree with the master
            tot_bad = [e for ck_, cv_ in d["calibration"].items() if ck_.split(":")[0] in ("1", "2", "3") for e in cv_["evidence"]
                       if e[0] == q and e[1] == q and e[2] == 0 and not e[4]]
            if tot_bad:
                rec.update(verdict="TABLE_TOTALS_DISAGREE", reason="the table's own totals disagree with the master at this quarter (another basis): " +
                           "; ".join(f"{e[5]:,.0f} vs {e[6]:,.0f}" for e in tot_bad[:3]))
            elif not own_c1:
                rec.update(verdict="NO_OWN_COMPARATIVE", reason="the filing's own prior-year-end column has no DART/audit anchor to compare (2022.4Q is IFRS4 / no anchor)")
            elif all(e[4] for e in own_c1) and all(e[4] for e in own_c0):
                # identity of the table: Stage B only emits observations of tables whose identity closes; the unit tie is the master
                if c["status"] == "HOLD_UNTESTED":
                    rec.update(verdict="NO_ANCHOR", reason="untested")
                else:
                    rec.update(verdict="PASS", reason=f"own prior-year-end column reproduces the master anchor ({len(own_c1)} comparison(s): " + "; ".join(f"{e[1]} {e[5]:,.1f} = {e[6]:,.1f}" for e in own_c1[:2]) + ")")
                    doc = B.load_tables(code, q)
                    unit = c["unit"]
                    cells.append({"code": code, "item": item, "quarter": q, "status": "MANUAL", "calib": "sametable", "value_mn": c["value_mn"], "rule": c["rule"], "kind": c["kind"],
                                  "form": c.get("form"), "page": c["page"], "unit": unit, "unit_how": "master", "prec_mn": c.get("prec_mn"), "tol_mn": B.UNIT_TOL[unit],
                                  "pdf": c.get("pdf") or doc["pdf"], "sha256": c.get("sha256") or doc["sha256"],
                                  "basis": (f"정기경영공시 {q} 재무상태표(8-1 {grp} 구간) p{c['page']} 라인「{c['rule']}」 {c['value_mn'] / 100:,.3f}억(단위 {unit}). 같은 표 보정 5c: 이 공시본 표의 전기말 열이 "
                                            f"마스터의 DART 앵커를 재현({'; '.join(f'{e[1]} {e[5]:,.2f} = {e[6]:,.2f}' for e in own_c1[:2])}) -- 한 표의 두 열은 한 정의이므로 당기 열도 마스터 정의다"
                                            "(다른 해 공시본의 재작성 전기열 때문에 전 기간 보정이 불합격이어도 이 공시본 자체의 열에는 영향이 없다). "
                                            "표 항등식(자산 = 부채 + 자본) 폐합 확인, 표의 자산·부채·자본 총계가 마스터와 일치." + TAIL)})
            else:
                bad = [e for e in own_c1 + own_c0 if not e[4]]
                rec.update(verdict="FAIL", reason="own-filing column disagrees with the master anchor: " + "; ".join(f"{e[1]}(col{e[2]}) {e[5]:,.1f} vs {e[6]:,.1f}" for e in bad[:2]))
            rep.append(rec)
    (W / "sametable_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (W / "sametable_cells.json").write_text(json.dumps({"_note": "step 5c same-table calibrated cells (manual schema)", "cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(dict(Counter(r["verdict"] for r in rep)))
    for r in rep:
        if r["verdict"] == "PASS":
            print(" PASS", r["key"], r["rule"], round(r["value_mn"], 1), "|", r["reason"][:120])


if __name__ == "__main__":
    main()
