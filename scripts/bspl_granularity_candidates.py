#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B CLI: calibrate mapping concepts per company and build BS cell candidates (no master writes).

Output: data/_derived/bspl_granularity_20261011/candidates/<KR>.json  (+ _population.json)
Run:    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_candidates.py --company KR0050
        ... --company all        (15 unlisted + 8 reinsurer branches)
Never pipe a script into the interpreter via stdin; always pass a file path.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.views import view_all, cur  # noqa: E402

TIER2 = ["KR0004", "KR0029", "KR0049", "KR0050", "KR0051", "KR0074", "KR0075", "KR0076", "KR0080",
         "KR0095", "KR0097", "KR0100", "KR1010", "KR1011", "KR1098"]
REINS = ["KR1101", "KR1102", "KR1103", "KR1104", "KR1105", "KR1106", "KR1107", "KR1108"]
LISTED = ["KR0001", "KR0002", "KR0003", "KR0005", "KR0008", "KR0009", "KR0010", "KR0011", "KR0032", "KR0068",
          "KR0069", "KR0070", "KR0071", "KR0072", "KR0073", "KR0079", "KR0082", "KR0083", "KR0087", "KR0094",
          "KR0099", "KR0104", "KR0150", "KR1000"]      # DART-sourced companies (2023.1Q/2Q holes etc.)
QUARTERS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
OUT = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
OUT_BRACKET = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates_bracket"
BRACKET = False         # --bracket: opt-in year-end bracket acceptance (status CAND_BRACKET), written to OUT_BRACKET only
LIFE_ONLY_ITEMS = {5, 8}
# (company, quarter) whose master column is on another basis than the disclosure (never fill, never anchor):
# KR0004 2025.4Q = DART 엠지 FY2025 (assets 728억) vs 예별 경영공시 (38,191억)
CQ_EXCLUDE = {("KR0004", "2025.4Q")}
QOQ_TIED = 3.0          # ratio bound for tables whose unit/column is tied to the master totals
QOQ_UNTIED = 0.30       # +-30% for tables without a master tie


def group_of(o) -> str:
    """calibration group: K-IFRS statement lines vs supervisory forms (summary/8-1-S/equity)"""
    return "K" if o.form == "K" else "S"


def reserve_trio_ok(an, docs, unit_infos):
    """책임준비금(sum_bs) == master 20+21+22 at Q4 anchors  ->  supervisory 8-1 trio mapping is group-calibrated."""
    checks = []
    for q, doc in docs.items():
        if not q.endswith("4Q"):
            continue
        a20, a21 = an.get((20, q)), an.get((21, q))
        if a20 is None or a21 is None:
            continue
        a22 = an.get((22, q), 0.0)
        tabs = B.pick_tables(doc, "sum_bs")
        unit = (unit_infos.get(q) or {}).get("sum_bs", (None,))[0]
        if not tabs or unit is None:
            continue
        va = view_all(tabs[0])
        r = (va.get("책임준비금") or [None])[0]
        v = cur(r) if r else None
        if v is None:
            continue
        checks.append(abs(v * B.UNIT_FACTOR[unit] - (a20 + a21 + a22)) <= B.UNIT_TOL[unit])
    return (bool(checks) and all(checks)), checks


def company_is_simple(docs) -> bool:
    """no separate account (특별계정자산 = 0 in every summary table)"""
    seen = False
    for q, doc in docs.items():
        for t in B.pick_tables(doc, "sum_bs"):
            va = view_all(t)
            r = (va.get("특별계정자산") or [None])[0]
            if r is None:
                continue
            seen = True
            v = r["vals"][0] if r["vals"] else None
            if v not in (None, 0, 0.0):
                return False
    return seen


def is_audit_obs(o) -> bool:
    """an observation read from a year-end K-IFRS statement (audit report in raw_aux, or the audited statements embedded in
    the annual disclosure PDF): current column, statement lines (form K)"""
    return (o.kind == "bs_full" and o.form == "K" and not o.comparative and o.quarter.endswith("4Q")
            and o.basis in (None, "별도"))


def process_company(code, all_v, anchor, disc, meta, population, pop_rules=None, pop_simple=None):
    mv = all_v.get(code, {})
    an = anchor.get(code, {})
    reins_like = not an                                    # no DART/owner anchor at all (reinsurer branches)
    kpi = B.load_kpi_anchors(code) if reins_like else {}   # independent KPI totals as unit tie / cross-check
    docs, obs_by_q, unit_infos, notes, id_fail = {}, {}, {}, [], {}
    for q in QUARTERS:
        doc = B.load_tables(code, q)
        if doc is None:
            continue
        docs[q] = doc
        unit_ref = {it: v for (it, qq), v in kpi.items() if qq == q} if kpi else None
        obs, unit_info, nts = B.observations(code, q, doc, all_v, disc, unit_ref)
        unit_infos[q] = unit_info
        bad = set()
        for kind, (unit, how) in unit_info.items():
            if kind == "equity" or unit is None:
                continue
            ok, det = B.table_identity(doc, kind, unit)
            if ok is False:
                bad.add(kind)
                id_fail[f"{q}|{kind}"] = det
        obs = [o for o in obs if o.kind not in bad]
        obs_by_q[q] = obs
        notes += [f"{q} {n}" for n in nts]
    audit_src = {}
    if reins_like:
        # The audited year-end statements (raw_aux/<KR>_*__audit.pdf, exact K-IFRS lines, the same lines DART tags) stand in
        # for the missing DART anchors: they are the anchor, every OTHER table (summary / 8-1 supervisory form) must
        # reproduce them at the year-ends to be trusted for the interim quarters.
        an = {}
        for q, obs in obs_by_q.items():
            for o in obs:
                if not is_audit_obs(o):
                    continue
                if o.quarter in B.FORBIDDEN_ANCHOR_Q:
                    continue
                if B.is_anchor_concept(o.concept):
                    an.setdefault((o.item, o.quarter), o.value_mn)
                    audit_src[(o.item, o.quarter)] = o.src_pdf or docs[q]["pdf"]
    trio_ok, trio_checks = reserve_trio_ok(an, docs, unit_infos)
    simple = company_is_simple(docs)

    # ---- calibration: per (concept, group), evidence merged over table kinds ----
    calib = defaultdict(list)
    for q, obs in obs_by_q.items():
        for o in obs:
            a = an.get((o.item, o.quarter))
            if a is None:
                continue
            if reins_like and (is_audit_obs(o) or o.comparative):
                # the audit statements ARE the anchors (never evidence for themselves); comparative columns of the
                # interim 8-1 tables are not used because their meaning differs between filings (prior year-end in
                # 2024, same quarter of the prior year in KR1106's 2026 filings)
                continue
            # reinsurer totals: the supervisory-basis summary can differ from the audited K-IFRS totals by a few 억원
            # (KR1102 2024.4Q: 13,632 vs 13,637.7, equity identical) -- near-equal (<= 1%) counts as reproduced
            tol_ev = max(o.tol_mn, 0.01 * abs(a)) if (reins_like and o.item in (1, 2, 3)) else o.tol_mn
            calib[(o.concept, group_of(o))].append(
                (o.pdf_quarter, o.quarter, o.col, o.kind, B.match(o.value_mn, tol_ev, a, o.col > 0), o.value_mn, a))
    status = {}
    for key, ev in calib.items():
        status[key] = "accepted" if all(e[4] for e in ev) else "rejected"
    seen = {(o.concept, group_of(o)) for obs in obs_by_q.values() for o in obs}
    for key in seen:
        status.setdefault(key, "untested")
        pop = population[(key[0], key[1])]
        pop[status[key]].add(code)
        if simple and pop_simple is not None and not reins_like:
            pop_simple[(key[0], key[1])][status[key]].add(code)

    def bracket_ok(o):
        """opt-in: a (concept, group) that fails somewhere in the whole history is trusted for an INTERIM cell of fiscal year Y when
        the evidence of that year reproduces the master at BOTH bracketing year-ends (Y-1.4Q and Y.4Q): the master's definition
        of the item is then the rule's for the whole fiscal year.  Entries that merely say 'line not found' (0.0 against a non-zero
        anchor, read from ANOTHER filing's comparative column) are not evidence; the cell's own filing must pass when it has any."""
        if not BRACKET or o.col != 0 or o.quarter.endswith("4Q") or o.basis not in (None, "별도"):
            return False
        ev = calib.get((o.concept, group_of(o)))
        if not ev:
            return False
        y = int(o.quarter[:4])
        a1, a2 = f"{y - 1}.4Q", f"{y}.4Q"

        def informative(e):
            return not (abs(e[5]) < 1e-9 and abs(e[6]) > 1e-9 and e[0] != o.pdf_quarter)

        fy = lambda e: int(e[0][:4])
        if any(not e[4] for e in ev if e[0] == o.pdf_quarter):
            return False
        e1 = [e for e in ev if informative(e) and e[1] == a1 and fy(e) == y]
        e2 = [e for e in ev if informative(e) and e[1] == a2 and fy(e) in (y, y + 1)]
        return bool(e1) and bool(e2) and all(e[4] for e in e1) and all(e[4] for e in e2)

    def decide(o):
        if reins_like and is_audit_obs(o) and B.is_anchor_concept(o.concept):
            return "accepted"                 # the audited year-end statement line IS the anchor
        key = (o.concept, group_of(o))
        st = status.get(key, "untested")
        if st == "rejected" and bracket_ok(o):
            return "bracket_ok"
        if st == "untested":
            item = o.item
            if group_of(o) == "K":
                if item in B.SAFE_UNTESTED_K and (item, o.concept[1]) not in B.K_BLOCKED_UNTESTED_LABELS:
                    return "untested_ok"
            else:
                if item in B.SAFE_UNTESTED_S:
                    return "untested_ok"
                if item in (20, 21, 22) and o.kind == "bs_full" and trio_ok:
                    return "group_ok"
                # no DART series at all (reinsurer branches): population evidence from simple balance sheets
                if (pop_rules and not an and simple and pop_rules.get(f"{B.cname(o.concept)}|{group_of(o)}")):
                    return "population_ok"
            return "untested_blocked"
        return st

    # R1 (owner 2026-10-09, reinsurers): a year-end value restated in a LATER filing's prior-year-end column wins over the
    # original filing's own column.  Later comparatives are trusted only when the latest filing of the group is an annual
    # filing / audit report, or at least two later filings agree (the meaning of the comparative column of an interim 8-1
    # differs between filings: KR1106's 2026 tables print the same quarter of the prior year).
    later_cmp = defaultdict(list)
    if reins_like:
        for qq, obs in obs_by_q.items():
            for o in obs:
                if o.comparative and o.kind == "bs_full" and o.basis in (None, "별도") and o.quarter.endswith("4Q"):
                    later_cmp[(o.item, o.quarter)].append(o)

    def r1_value(pick, item, q):
        # like with like: the pick is a line of the audited year-end K statement, the later source is the prior-year
        # column of the NEXT annual K statement (an interim 8-1 aggregates lines differently, e.g. 기타부채)
        if not is_audit_obs(pick):
            return None
        lst = [o for o in later_cmp.get((item, q), [])
               if o.form == "K" and o.concept == pick.concept and o.pdf_quarter.endswith("4Q")
               and B.qkey(o.pdf_quarter) > B.qkey(q)]
        if not lst:
            return None
        lst.sort(key=lambda o: B.qkey(o.pdf_quarter))
        groups = []
        for o in lst:
            for g in groups:
                if abs(g[0].value_mn - o.value_mn) <= max(o.tol_mn, g[0].tol_mn, 0.002 * abs(o.value_mn), 1.0):
                    g.append(o)
                    break
            else:
                groups.append([o])
        latest = max(groups, key=lambda g: max(B.qkey(o.pdf_quarter) for o in g))
        annual = any(o.pdf_quarter.endswith("4Q") or o.src_pdf for o in latest)
        if len(latest) < 2 and not annual:
            return None
        lo = max(latest, key=lambda o: B.qkey(o.pdf_quarter))
        if abs(lo.value_mn - pick.value_mn) <= max(pick.tol_mn, lo.tol_mn, 0.002 * abs(pick.value_mn), 1.0):
            return None
        # the later statement's comparative column must itself close (A = L + E): KR1105's FY2024 statement prints the
        # 2022 total assets (2,941.88억) in the 2023.12.31 cell while its own 부채및자본총계 says 2,753.34억
        tots = {o2.item: o2.value_mn for it in (1, 2, 3) for o2 in later_cmp.get((it, q), [])
                if o2.pdf_quarter == lo.pdf_quarter and o2.form == "K" and o2.concept[1] == {1: ("자산총계",), 2: ("부채총계",), 3: ("자본총계",)}[it]}
        if len(tots) < 3 or abs(tots[1] - tots[2] - tots[3]) > max(lo.tol_mn * 3, 1.0, 0.0005 * abs(tots[1])):
            return None
        return lo, len(latest)

    cands = []
    for q, obs in sorted(obs_by_q.items(), key=lambda kv: B.qkey(kv[0])):
        by_item = defaultdict(list)
        for o in obs:
            if (code, o.quarter) in CQ_EXCLUDE:
                continue
            if o.col == 0 and o.basis in (None, "별도"):
                by_item[o.item].append(o)
        for item, lst in by_item.items():
            if (item, q) in mv:
                m = mv[(item, q)]
                tol_m = 100.5 if (item, q) in disc.get(code, {}) else 0.0      # master cell itself 억원-rounded
                good_obs = [o for o in lst if decide(o) in ("accepted", "group_ok", "untested_ok", "population_ok")]
                pool = good_obs if good_obs else lst
                same = [o for o in pool if B.match(o.value_mn, max(o.tol_mn, tol_m), m)]
                best = min(same or pool, key=lambda o: o.prec_mn)
                if same:
                    st = "EXISTS_SAME"
                elif good_obs:
                    st = "EXISTS_DIFF"          # a calibrated mapping disagrees with the master value: real conflict
                else:
                    st = "EXISTS_BASIS"         # only uncalibrated/rejected (supervisory-basis) lines differ: informational
                cands.append({"code": code, "item": item, "quarter": q, "status": st, "master": m,
                              "value_mn": best.value_mn, "rule": B.cname(best.concept), "kind": best.kind,
                              "page": best.page, "unit": best.unit})
                continue
            ds = [(o, decide(o)) for o in lst]
            good = [(o, d) for o, d in ds if d in ("accepted", "untested_ok", "group_ok", "population_ok", "bracket_ok")]
            if good:
                # calibration class first, then the statement itself (K) before supervisory aggregates (S/E), then precision
                rank = {"accepted": 0, "group_ok": 1, "population_ok": 2, "bracket_ok": 2, "untested_ok": 3}
                frank = {"K": 0, "S": 1, "E": 1}
                krank = {"bs_full": 0, "sum_bs": 1, "equity": 2}
                good.sort(key=lambda t: (rank[t[1]], frank.get(t[0].form, 2), t[0].prec_mn, krank.get(t[0].kind, 3)))
                pick, how = good[0]
                # precision refinement: the calibrated pick may be a rounded supervisory line (억원) while the same filing
                # prints the statement line exactly (원/천원/백만원) and the two agree within the rounding -> keep the pick's
                # calibration class but use the exact value (KR1107 2025.2Q cash: 176 vs 176.2)
                fine = [t for t in good if t[0] is not pick and t[0].prec_mn < pick.prec_mn
                        and abs(t[0].value_mn - pick.value_mn) <= max(pick.tol_mn, 1.01 * pick.prec_mn)
                        and t[0].comparative == pick.comparative]
                if fine and reins_like:
                    pick = min((t for t in fine), key=lambda t: t[0].prec_mn)[0]
                # observations of the same cell that differ by <= 1% (classification / rounding differences between a
                # statement, an 8-1 detail and a summary table) are not conflicts: the most direct table wins.  Larger
                # differences (unit / column / basis errors) hold the cell.
                def _differs(a, b, tol):
                    return abs(a - b) > max(0.01 * max(abs(a), abs(b)), pick.tol_mn, tol)
                alts = [t for t in good[1:] if _differs(t[0].value_mn, pick.value_mn, t[0].tol_mn)]
                note = None
                if alts and item in (11, 12) and all(t[0].concept[2] != pick.concept[2] and t[0].concept[1] == pick.concept[1] for t in alts):
                    # first-row vs sum-of-rows of the same label: the DART total tag is the sum -> prefer sum_all
                    sa = [t for t in good if t[0].concept[2] == "sum_all" and t[0].form == pick.form]
                    if sa:
                        pick, how = sa[0]
                        alts = [t for t in good if t[0].concept[2] == "first" and t[0].concept[1] == pick.concept[1]
                                and t[0].form == pick.form and _differs(t[0].value_mn, pick.value_mn, t[0].tol_mn)]
                if not alts and len(good) > 1 and any(abs(t[0].value_mn - pick.value_mn) > max(pick.tol_mn, t[0].tol_mn) for t in good[1:]):
                    note = "other tables of the same PDF differ by <=1% (classification/rounding); most direct table used"
                st = ("HOLD_ALT_DISAGREE" if alts else ("CAND" if how in ("accepted", "group_ok")
                                                       else "CAND_BRACKET" if how == "bracket_ok" else "CAND_UNTESTED"))
                rec = {"code": code, "item": item, "quarter": q, "status": st, "calib": how, "note": note,
                       "value_mn": pick.value_mn, "rule": B.cname(pick.concept), "kind": pick.kind, "form": pick.form,
                       "page": pick.page, "unit": pick.unit, "unit_how": pick.how, "prec_mn": pick.prec_mn,
                       "tol_mn": pick.tol_mn, "pdf": pick.src_pdf or docs[q]["pdf"], "sha256": pick.src_sha or docs[q]["sha256"],
                       "alt": [{"rule": B.cname(o.concept), "kind": o.kind, "value_mn": o.value_mn, "decision": d}
                               for o, d in ds if o is not pick][:6]}
                r1 = r1_value(pick, item, q) if (reins_like and q.endswith("4Q") and st in ("CAND", "CAND_UNTESTED")) else None
                if r1:
                    lo, support = r1
                    rec.update({"r1": {"own_value_mn": pick.value_mn, "own_pdf_quarter": pick.pdf_quarter, "from": lo.pdf_quarter,
                                       "support": support},
                                "value_mn": lo.value_mn, "kind": lo.kind, "form": lo.form, "page": lo.page, "unit": lo.unit,
                                "unit_how": lo.how, "prec_mn": lo.prec_mn, "tol_mn": lo.tol_mn,
                                "pdf": lo.src_pdf or docs[lo.pdf_quarter]["pdf"], "sha256": lo.src_sha or docs[lo.pdf_quarter]["sha256"],
                                "note": f"R1: later filing {lo.pdf_quarter} prior-year-end column (restated) replaces the original {pick.pdf_quarter} value"})
                elif kpi and item in (1, 2, 3) and (item, q) in kpi:
                    rec["kpi_mn"] = kpi[(item, q)]
                    if (abs(rec["value_mn"] - kpi[(item, q)]) > max(0.01 * abs(kpi[(item, q)]), 100.5)
                            and st in ("CAND", "CAND_UNTESTED")):
                        rec["status"] = "HOLD_KPI_DIFF"
                cands.append(rec)
                continue
            # nothing loadable: report the best blocked observation
            blocked = sorted(ds, key=lambda t: t[0].prec_mn)[0]
            o, d = blocked
            cands.append({"code": code, "item": item, "quarter": q,
                          "status": "HOLD_REJECTED_RULE" if d == "rejected" else "HOLD_UNTESTED",
                          "value_mn": o.value_mn, "rule": B.cname(o.concept), "kind": o.kind, "form": o.form,
                          "page": o.page, "unit": o.unit, "prec_mn": o.prec_mn,
                          "pdf": o.src_pdf or docs[q]["pdf"], "sha256": o.src_sha or docs[q]["sha256"]})
    # ---- R1 for interim quarters whose own filing gives nothing usable (reinsurers): the NEXT YEAR's summary BS prints the
    # same quarter of the previous year in its column 2 (restated numbers: RGA 2023.2Q/3Q, owner R1 2026-10-09).  The
    # comparative column must close (A = L + E, share columns 100 %) -- see stage_b.sumbs_prev_year_ok.
    if reins_like:
        have = {(c["item"], c["quarter"]) for c in cands}
        for qq, obs in sorted(obs_by_q.items(), key=lambda kv: B.qkey(kv[0])):
            for o in obs:
                if not (o.kind == "sum_bs" and o.comparative and o.col == 2):
                    continue
                if (code, o.quarter) in CQ_EXCLUDE or o.quarter not in QUARTERS or o.basis not in (None, "별도"):
                    continue
                if (o.item, o.quarter) in have or (o.item, o.quarter) in mv:
                    continue
                d = decide(o)
                if d not in ("accepted", "untested_ok", "group_ok", "population_ok"):
                    continue
                have.add((o.item, o.quarter))
                cands.append({"code": code, "item": o.item, "quarter": o.quarter,
                              "status": "CAND" if d in ("accepted", "group_ok") else "CAND_UNTESTED", "calib": d,
                              "note": (f"R1: the own filing of {o.quarter} gave no usable value; value = same-quarter column of the "
                                       f"summary BS of the later filing {o.pdf_quarter} (restated comparative)"),
                              "value_mn": o.value_mn, "rule": B.cname(o.concept), "kind": o.kind, "form": o.form, "page": o.page,
                              "unit": o.unit, "unit_how": o.how, "prec_mn": o.prec_mn, "tol_mn": o.tol_mn,
                              "pdf": o.src_pdf or docs[o.pdf_quarter]["pdf"], "sha256": o.src_sha or docs[o.pdf_quarter]["sha256"],
                              "alt": [], "gapfill": o.pdf_quarter, "r1": {"own_value_mn": None, "own_pdf_quarter": o.quarter,
                                                                          "from": o.pdf_quarter, "support": 1}})
    # ---- equity cells that the quarter's own filing could not give (e.g. its 4-1 column failed the closure test) are taken
    # from the NEXT filing's prior-quarter column of the same 4-1 table (header '당분기-1분기'; the column that closes is
    # trusted, the '-2분기' column is not: KR1102's third column holds year-end values under a quarter header)
    have = {(c["item"], c["quarter"]) for c in cands}
    sel3 = {c["quarter"]: c["value_mn"] for c in cands if c["item"] == 3 and c["status"] in ("CAND", "CAND_UNTESTED")}
    for (it_, q_), v_ in mv.items():
        if it_ == 3:
            sel3.setdefault(q_, v_)
    eq3 = {(o.pdf_quarter, o.quarter): o.value_mn for obs in obs_by_q.values() for o in obs
           if o.kind == "equity" and o.comparative and o.col == 1 and o.item == 3}
    for qq, obs in sorted(obs_by_q.items(), key=lambda kv: B.qkey(kv[0])):
        for o in obs:
            if not (o.kind == "equity" and o.comparative and o.col == 1 and o.item in (3, 4, 30, 31)):
                continue
            if o.item != 30:
                s3, t3 = sel3.get(o.quarter), eq3.get((o.pdf_quarter, o.quarter))
                if s3 is not None and t3 is not None and abs(s3 - t3) > max(3 * o.tol_mn, 0.005 * abs(s3)):
                    continue            # the quarter's total was restated: the as-published equity split no longer fits
            if (code, o.quarter) in CQ_EXCLUDE or o.quarter not in QUARTERS or o.basis not in (None, "별도") or (o.item, o.quarter) in have or (o.item, o.quarter) in mv:
                continue
            d = decide(o)
            if d not in ("accepted", "untested_ok", "group_ok", "population_ok"):
                continue
            have.add((o.item, o.quarter))
            cands.append({"code": code, "item": o.item, "quarter": o.quarter,
                          "status": "CAND" if d in ("accepted", "group_ok") else "CAND_UNTESTED", "calib": d,
                          "note": f"later filing {o.pdf_quarter} 4-1 equity table, prior-quarter column (closure verified); the quarter's own filing had no usable value",
                          "value_mn": o.value_mn, "rule": B.cname(o.concept), "kind": o.kind, "form": o.form, "page": o.page,
                          "unit": o.unit, "unit_how": o.how, "prec_mn": o.prec_mn, "tol_mn": o.tol_mn,
                          "pdf": o.src_pdf or docs[o.pdf_quarter]["pdf"], "sha256": o.src_sha or docs[o.pdf_quarter]["sha256"],
                          "alt": [], "gapfill": o.pdf_quarter})
    # ---- totals dispute resolved by the balance-sheet identity (assets = liabilities + equity) ----
    # One table of a PDF may carry a typo (KR1106 2024.1Q: the 4-1 equity table prints 자본총계 3,635 = the previous
    # quarter), while the statement and the summary agree.  A disputed total is accepted only when exactly one of the
    # competing values closes A = L + E against the other two totals of the same quarter.
    pickv = {(c["item"], c["quarter"]): c for c in cands if c["status"] in ("CAND", "CAND_UNTESTED")}
    for c in cands:
        if c["status"] != "HOLD_ALT_DISAGREE" or c["item"] not in (1, 2, 3):
            continue
        q = c["quarter"]
        others = {}
        for it in (1, 2, 3):
            if it == c["item"]:
                continue
            o = pickv.get((it, q))
            if o is not None:
                others[it] = o["value_mn"]
            elif (it, q) in mv:
                others[it] = mv[(it, q)]
        if len(others) != 2:
            continue
        vals = [c["value_mn"]] + [a["value_mn"] for a in c.get("alt", []) if a.get("decision") in ("accepted", "untested_ok", "group_ok", "population_ok")]
        tol = max(c.get("tol_mn", 1.0) * 3, 1.5 * c.get("prec_mn", 1.0), 1.0)

        def resid(v):
            t = dict(others)
            t[c["item"]] = v
            return t[1] - t[2] - t[3]
        okv = [v for v in vals if abs(resid(v)) <= tol]
        if okv and len({round(v, 1) for v in okv}) >= 1 and all(abs(v - okv[0]) <= 0.01 * abs(okv[0]) for v in okv):
            best = min(okv, key=lambda v: abs(resid(v)))
            if abs(best - c["value_mn"]) > 1e-9:
                # switch to the closing alternative's value (keep the most direct table's metadata of the pick otherwise)
                c["value_mn"] = best
            c["status"] = "CAND_UNTESTED" if c.get("calib") not in ("accepted", "group_ok") else "CAND"
            c["note"] = (f"disputed total resolved by A=L+E (residual {resid(best):.1f} 백만원); dissenting tables: "
                         + ", ".join(f"{a['kind']} {a['value_mn']:.0f}" for a in c.get("alt", []) if abs(a["value_mn"] - best) > 0.01 * abs(best)))
            pickv[(c["item"], q)] = c
    # ---- reserve-trio identity gate: summary 책임준비금 == 보험계약부채 + 재보험계약부채 + 투자계약부채 (statement lines) ----
    # catches partial lines (e.g. only the 유배당 half of 보험계약부채) and unit/column slips for items 20/21/22
    by_q = defaultdict(dict)
    for c in cands:
        if c["status"] in ("CAND", "CAND_UNTESTED", "CAND_BRACKET") and c["item"] in (20, 21, 22):
            by_q[c["quarter"]][c["item"]] = c
    for q, items_q in by_q.items():
        tabs = B.pick_tables(docs[q], "sum_bs") if q in docs else []
        unit = (unit_infos.get(q) or {}).get("sum_bs", (None,))[0]
        if not tabs or unit is None:
            continue
        r = (view_all(tabs[0]).get("책임준비금") or [None])[0]
        v = cur(r) if r else None
        if v is None:
            continue
        reserve_mn = v * B.UNIT_FACTOR[unit]
        total = 0.0
        for it in (20, 21, 22):
            if it in items_q:
                total += items_q[it]["value_mn"]
            elif (it, q) in mv:
                total += mv[(it, q)]
        if abs(total - reserve_mn) > max(0.01 * abs(reserve_mn), B.UNIT_TOL[unit] * 1.5):
            for c in items_q.values():
                c["status"] = "HOLD_TRIO"
                c["trio"] = {"reserve_mn": reserve_mn, "sum_mn": total}

    # ---- QoQ plausibility gate ----
    # neighbours for the plausibility gate are EXISTING master values only: letting candidates validate each other lets two
    # adjacent wrong cells (e.g. a partial line read in two consecutive quarters) vouch for one another
    known = dict(mv)

    def nb(item, q, direction):
        best = None
        for (it, qq), v in known.items():
            if it != item or qq == q or qq in B.FORBIDDEN_ANCHOR_Q:
                continue
            dq = B.qidx(qq) - B.qidx(q)
            if (direction < 0 and dq < 0) or (direction > 0 and dq > 0):
                if best is None or abs(dq) < best[0]:
                    best = (abs(dq), v, qq)
        return best

    for c in cands:
        if c["status"] not in ("CAND", "CAND_UNTESTED", "CAND_BRACKET"):
            continue
        v = c["value_mn"]
        tied = str(c.get("unit_how", "")).startswith("master")
        untied = c.get("unit_how") in ("caption", "peer")
        sides = [s for s in (nb(c["item"], c["quarter"], -1), nb(c["item"], c["quarter"], +1)) if s and abs(s[1]) >= 100.0]
        if not sides or abs(v) < 1000.0 or c["item"] in (4, 31) or (c["item"] in (1, 2, 3) and not untied):
            continue
        sides = [s for s in sides if abs(s[1]) >= 1000.0]
        if not sides:
            continue
        if tied:
            ok = any((1.0 / QOQ_TIED) <= (v / s[1]) <= QOQ_TIED for s in sides if s[1] != 0)
        else:
            ok = any(abs(v / s[1] - 1.0) <= QOQ_UNTIED for s in sides if s[1] != 0)
        if not ok:
            c["status"] = "HOLD_QOQ"
            c["qoq"] = [{"q": s[2], "v": s[1]} for s in sides]

    # ---- partial groups: a quarter that has NO filing of its own and is rebuilt from later filings' comparatives only may
    # not end up as an equity-only fragment (the BS census wants the core items 1-4 of a (company, quarter) group together:
    # KR1104 2025.3Q has no PDF and no later comparative for the totals) ----
    if reins_like:
        have_q = defaultdict(set)
        for c in cands:
            if c["status"] in ("CAND", "CAND_UNTESTED"):
                have_q[c["quarter"]].add(c["item"])
        for (it_, q_) in mv:
            have_q[q_].add(it_)
        for c in cands:
            if c["status"] in ("CAND", "CAND_UNTESTED") and c["quarter"] not in docs and not ({1, 2} <= have_q[c["quarter"]]):
                c["status"] = "HOLD_PARTIAL_GROUP"
                c["note"] = (c.get("note") or "") + " | held: the quarter has no filing of its own and no total assets/liabilities"

    cal_out = {}
    for (concept, grp) in sorted(seen, key=lambda k: (k[0][0], B.cname(k[0]), k[1])):
        ev = calib.get((concept, grp), [])
        cal_out[f"{B.cname(concept)}|{grp}"] = {
            "status": status[(concept, grp)],
            "evidence": [[e[0], e[1], e[2], e[3], bool(e[4]), round(e[5], 3), round(e[6], 3)] for e in ev]}
    return {"code": code, "name": meta.get(code, ("?",))[0], "trio_ok": trio_ok, "trio_checks": trio_checks,
            "calibration": cal_out, "candidates": cands, "notes": notes, "identity_fail": id_fail}


def pop_rules_from(pop_simple):
    rules = {}
    for (concept, grp), d in pop_simple.items():
        acc, rej = len(d["accepted"]), len(d["rejected"])
        rules[f"{B.cname(concept)}|{grp}"] = bool(acc >= 3 and acc / max(1, acc + rej) >= 0.85)
    return rules


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", required=True)
    ap.add_argument("--bracket", action="store_true", help="opt-in year-end bracket acceptance; writes to candidates_bracket/ only")
    a = ap.parse_args()
    global BRACKET, OUT
    BRACKET = a.bracket
    if BRACKET:
        OUT = OUT_BRACKET
    codes = (TIER2 + REINS if a.company == "all" else LISTED if a.company == "listed"
             else a.company.split(","))
    all_v, anchor, disc, meta = B.load_master()
    OUT.mkdir(parents=True, exist_ok=True)
    population = defaultdict(lambda: {"accepted": set(), "rejected": set(), "untested": set()})
    pop_simple = defaultdict(lambda: {"accepted": set(), "rejected": set(), "untested": set()})
    rules_file = OUT / "_population_rules.json"
    pop_rules = None
    for code in codes:
        if code in REINS and pop_rules is None:
            # rules from the DART-anchored companies of this run; else from the file saved by the last full run
            if pop_simple:
                pop_rules = pop_rules_from(pop_simple)
            elif rules_file.exists():
                pop_rules = json.loads(rules_file.read_text(encoding="utf-8"))["rules"]
            else:
                pop_rules = {}
        res = process_company(code, all_v, anchor, disc, meta, population, pop_rules, pop_simple)
        (OUT / f"{code}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        cnt = defaultdict(int)
        for c in res["candidates"]:
            cnt[c["status"]] += 1
        print(code, dict(cnt), flush=True)
    pop = {f"{B.cname(k[0])}|{k[1]}": {kk: sorted(v) for kk, v in d.items()} for k, d in population.items()}
    (OUT / "_population.json").write_text(json.dumps(pop, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    if pop_simple and any(c in TIER2 for c in codes):
        rules_file.write_text(json.dumps({
            "_note": "population evidence for companies WITHOUT any DART anchor (reinsurer branches): a supervisory-table concept is accepted "
                     "when >= 3 DART-anchored companies with no separate account reproduce it with pass rate >= 0.85",
            "rules": pop_rules_from(pop_simple),
            "evidence": {f"{B.cname(k[0])}|{k[1]}": {kk: sorted(v) for kk, v in d.items()} for k, d in pop_simple.items()}},
            ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
