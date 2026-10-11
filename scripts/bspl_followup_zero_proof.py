#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5a: the zero-proof rule for held BS cells whose printed value is 0.

A zero is loaded only when it is PROVEN from the statement it was read from (never because 'the same item is 0 elsewhere' and never refused
because 'the same item is non-zero in other quarters').  Rules (all must hold):
  Z1  the line is printed in the picked statement with 0 or a dash in the current column (a dash that is the minus-sign cell of a neighbour is
      flagged `unsure` by the row reader and is not a value) and the statement's own identity closes (assets = liabilities + equity, unit-tolerance)
  Z2  siblings that could hold the amount under another measurement category are 0 as well: items 11/12/13 need the loan line (대출채권) and,
      for 13, every amortised-cost family line to be 0 (a securities-only zero does not prove the DART item 13, which also holds loans)
  Z3  CLOSURE of the asset side with the zero line included:
        S-form summary BS (억원):  자산총계 = 현금및예치금 + FVPL + FVOCI + AC + 관계종속 + 대출채권 + 부동산 + 비운용자산 + 특별계정자산
                                   within 0.5 unit per non-zero printed line (rounding of the printed lines), i.e. no room for a hidden amount
        K-form statement (won / 천원): the sum of the statement's top-level asset lines (the K section, before the supervisory 운용자산 breakdown)
                                   equals 자산총계 (exact up to the printed unit); where the layout is hierarchical (parent lines) and the flat
                                   sum does not apply, rule Z3 is reported as 'no_closure' and the cell stays held (reported, not loaded)
Output: data/_derived/bspl_followup_20261011/zero_proof_cells.json (accepted cells in manual-cell schema for bspl_granularity_load_bs.py --manual)
        data/_derived/bspl_followup_20261011/zero_proof_report.json (every zero-valued hold with verdict and reason)
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
from bspl_granularity.views import view_all  # noqa: E402

W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
CAND = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "candidates"
TAIL = " (inbox/parser/20261011T0900Z bspl follow-up, step 5a zero-proof)"
S_LINES = ("현금및예치금", "FVPL", "FVOCI", "AC_SEC", "관계종속", "대출채권", "부동산", "비운용자산", "특별계정자산")
AC_FAMILY = ("AC_SEC", "AC_FA", "AC_LOAN", "AC_DEP", "AC_OTHER")


def val(va, key, c=0):
    """(value, state) of the first row of a canonical line: state 'ok' | 'absent' | 'unsure'"""
    rows = va.get(key)
    if not rows:
        return 0.0, "absent"
    r = rows[0]
    if len(r["vals"]) <= c:
        return 0.0, "absent"
    if r.get("unsure") and r["unsure"][c]:
        return 0.0, "unsure"
    if r["dash"][c]:
        return 0.0, "ok"
    return (r["vals"][c] if r["vals"][c] is not None else 0.0), "ok"


def pick_table(doc, kind, page):
    for t in doc["tables"]:
        if t["kind"] == kind and t["page"] == page:
            return t
    return None


def s_closure(t):
    va = view_all(t)
    unit = t.get("unit")
    if unit not in B.UNIT_FACTOR:
        return False, "unit unresolved"
    a, sa = val(va, "자산총계")
    if sa != "ok":
        return False, "자산총계 not readable"
    tot, nz = 0.0, 0
    parts = {}
    for k in S_LINES:
        v, st = val(va, k)
        if st == "unsure":
            return False, f"{k} unsure sign"
        parts[k] = v
        tot += v
        nz += 1 if abs(v) > 1e-9 else 0
    resid = a - tot
    tol = 0.5 * (nz + 1)
    if abs(resid) <= tol:
        return True, f"자산총계 {a:g} = Σ lines {tot:g} (잔차 {resid:g} 인쇄단위, 허용 {tol:g}; 비영 {nz}줄: " + ", ".join(f"{k} {v:g}" for k, v in parts.items() if abs(v) > 1e-9) + ")"
    return False, f"asset side does not close: 자산총계 {a:g} vs Σ {tot:g} (잔차 {resid:g}, 허용 {tol:g})"


def k_closure(t):
    """flat K section: rows of the statement part (before 운용자산 when the table appends the supervisory breakdown) excluding the total rows"""
    rows = t["rows"]
    labs = [r["label"] for r in rows]
    from bspl_granularity.views import canon
    cn = [canon(l, "bs") for l in labs]
    try:
        i_tot = cn.index("자산총계")
    except ValueError:
        return False, "no 자산총계 row"
    f = B.UNIT_FACTOR.get(t.get("unit"))
    if f is None:
        return False, "unit unresolved"
    va = view_all(t)
    a, st = val(va, "자산총계")
    if st != "ok":
        return False, "자산총계 not readable"
    # candidate sections: after the total (reinsurer 8-1 prints the total first) or before it
    i_op = next((i for i, c in enumerate(cn) if c == "운용자산"), len(rows))
    sections = []
    after = [r for r in rows[i_tot + 1:i_op] if r["vals"]]
    before = [r for r in rows[:i_tot] if r["vals"]]
    for name, sec in (("after-total", after), ("before-total", before)):
        s = 0.0
        ok = True
        n = 0
        for r in sec:
            if r.get("unsure") and any(r["unsure"][:1]):
                ok = False
                break
            v = 0.0 if r["dash"][0] else r["vals"][0]
            if v is None:
                continue
            s += v
            n += 1
        if ok and n >= 3:
            sections.append((name, s, n))
    tol = 2 * B.UNIT_PREC[t["unit"]] / f * 1.0       # raw units: 2 half-steps
    for name, s, n in sections:
        if abs(a - s) <= max(tol, 1.5):
            return True, f"자산총계 {a:,.0f} = K 구간({name}) {n}줄 합 {s:,.0f} (잔차 {a - s:g} 인쇄단위)"
    return False, "no_closure (hierarchical or non-flat K layout)"


def ident(t):
    ok, det = B.table_identity({"tables": [t]}, t["kind"], t.get("unit")) if t["kind"] in ("sum_bs", "bs_full") else (None, "n/a")
    return ok, det


def main():
    report, accepted = [], []
    for p in sorted(CAND.glob("KR*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for c in d["candidates"]:
            if c["status"] not in ("HOLD_UNTESTED", "HOLD_REJECTED_RULE") or abs(c.get("value_mn") or 0.0) > 1e-9:
                continue
            code, item, q = c["code"], c["item"], c["quarter"]
            rec = {"key": f"{code}|{item}|{q}", "status_before": c["status"], "rule": c["rule"], "kind": c["kind"], "form": c.get("form"), "page": c["page"]}
            doc = B.load_tables(code, q)
            t = pick_table(doc, c["kind"], c["page"]) if doc else None
            if t is not None:
                t = dict(t)
                t["unit"] = c["unit"]            # the unit Stage B resolved (the caption may carry none)
            if t is None or item not in (11, 12, 13, 22, 23):
                rec.update(verdict="SKIP", reason=f"item {item} / table not found: not covered by the zero-proof")
                report.append(rec)
                continue
            va = view_all(t)
            reasons = []
            ok_all = True
            # Z1 line printed zero + identity
            key = {11: "FVPL", 12: "FVOCI", 13: "AC_SEC", 22: "투자계약부채", 23: "차입부채"}[item]
            if item == 13 and t["kind"] == "bs_full" and "AC_CHILDREN" in c["rule"]:
                key = None
            v, st = (val(va, key) if key else (0.0, "ok"))
            if st == "unsure":
                ok_all = False
                reasons.append("Z1: sign of the zero cell unsure")
            idk, iddet = ident(t)
            if idk is False:
                ok_all = False
                reasons.append(f"Z1: table identity does not close ({iddet})")
            # Z2 siblings
            if item in (11, 12, 13):
                lv, ls = val(va, "대출채권")
                if ls == "unsure" or abs(lv) > 1e-9:
                    ok_all = False
                    reasons.append(f"Z2: 대출채권 = {lv:g} ({ls}): a zero securities line does not prove the item")
                if item in (11, 12):
                    for other in ("FVPL" if item == 11 else "FVOCI",):
                        pass
                if item == 13:
                    for fam in AC_FAMILY:
                        fv, fs = val(va, fam)
                        if fs == "unsure" or abs(fv) > 1e-9:
                            ok_all = False
                            reasons.append(f"Z2: {fam} = {fv:g} ({fs})")
            # Z3 closure
            if item in (11, 12, 13) and t["kind"] == "sum_bs":
                okc, det = s_closure(t)
            elif item in (11, 12, 13) and t["kind"] == "bs_full":
                okc, det = k_closure(t)
            elif item == 22:
                # 투자계약부채 is a component of the supervisory 책임준비금: 책임준비금 = 보험계약부채 + 재보험계약부채 + 투자계약부채
                rp, sp_ = val(va, "책임준비금")
                ic, sc = val(va, "보험계약부채")
                rc, sr = val(va, "재보험계약부채")
                f = B.UNIT_FACTOR.get(t["unit"])
                if "ok" == sp_ == sc == sr and f:
                    resid = rp - ic - rc - v
                    okc = abs(resid) * f <= max(2 * B.UNIT_PREC[t["unit"]], 0.05)
                    det = f"책임준비금 {rp:,.0f} = 보험계약부채 {ic:,.0f} + 재보험계약부채 {rc:,.0f} + 투자계약부채 {v:g} (잔차 {resid:g} 인쇄단위)"
                else:
                    okc, det = False, "책임준비금·보험계약부채·재보험계약부채 줄을 이 표에서 읽을 수 없어 폐합 불가"
            else:
                okc, det = False, "차입부채 is a sub-line of the supervisory 기타부채: no closure rule (kept held)"
            if not okc:
                ok_all = False
                reasons.append(f"Z3: {det}")
            rec["z3"] = det
            # Z5: the same line family prints 0 at a year-end where the master's own audited/DART anchor of the item is non-zero -> the printed
            # line is narrower than the master's definition (KR1106: S-form 상각후원가측정금융자산 = 0 at every quarter incl. year-ends, audited
            # amortised-cost children 9,087.6 / 3,516.5 / 3,950.2 백만원)
            grp = "K" if c.get("form") == "K" else "S"
            miss = []
            for ck, cv in d["calibration"].items():
                if not ck.startswith(f"{item}:") or not ck.endswith(f"|{grp}"):
                    continue
                for e in cv["evidence"]:
                    if abs(e[5]) < 1e-9 and abs(e[6]) > 1e-9:
                        miss.append((ck, e[1], e[6]))
            if miss:
                ok_all = False
                reasons.append("Z5: line family prints 0 where the audited anchor is non-zero: " + "; ".join(f"{m[0]} @{m[1]} anchor {m[2]:,.1f}" for m in miss[:3]))
            if item == 13:
                # Z6: amortised-cost financial assets include receivables / deposits that the supervisory summary reports under 비운용자산 and
                # that the audited K statements print as separate lines (뮌헨 2023.12.31 기타수취채권 3,085백만원 is amortised cost while the
                # S-form 상각후원가측정유가증권 prints 0): a zero securities line + a closing table does not prove item 13 = 0
                ok_all = False
                reasons.append("Z6: item 13 zero not provable from the line (amortised-cost receivables/deposits sit in other lines of the statement)")
            if ok_all and c["status"] == "HOLD_REJECTED_RULE":
                # the concept was calibrated against the master's DART/owner values and FAILED: its line is narrower/wider than the master's
                # definition (e.g. the supervisory 상각후원가측정유가증권 line is 0 while the audited year-end 상각후원가측정금융자산 is not: the
                # receivables sit in 비운용자산).  A closing table proves the printed zero, not that the master's item is zero.
                ok_all = False
                reasons.append("Z4: concept rejected by the year-end calibration (definition break): a zero of a rejected concept is not evidence for the master item")
            if ok_all:
                unit = t.get("unit")
                prec = f"±{B.UNIT_PREC[unit]:g}백만원 정밀도(인쇄단위 {unit})"
                basis = (f"정기경영공시 {q} {'요약 재무상태표(총괄)' if t['kind'] == 'sum_bs' else '재무상태표(8-1)'} p{t['page']} 라벨「{c['rule']}」이 0(대시)으로 인쇄 -- {prec}. "
                         f"0 증명(후속 5a): {det}; 같은 표의 자산 = 부채 + 자본 폐합 확인" + (f"; 대출채권·상각후원가 계열 줄도 0" if item in (11, 12, 13) else "") + ". 같은 항목이 다른 분기에서 0 이 아니라는 이유로는 거르지 않았다." + TAIL)
                accepted.append({"code": code, "item": item, "quarter": q, "status": "MANUAL", "calib": "zero_proof", "value_mn": 0.0, "rule": c["rule"],
                                 "kind": c["kind"], "form": c.get("form"), "page": t["page"], "unit": unit, "unit_how": "caption/identity", "prec_mn": B.UNIT_PREC[unit],
                                 "tol_mn": B.UNIT_TOL[unit], "pdf": doc["pdf"], "sha256": doc["sha256"], "basis": basis})
                rec.update(verdict="ACCEPT", reason=det)
            else:
                rec.update(verdict="KEEP_HELD", reason="; ".join(reasons))
            report.append(rec)
    (W / "zero_proof_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (W / "zero_proof_cells.json").write_text(json.dumps({"_note": "step 5a zero-proof cells (manual schema)", "cells": accepted}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    cnt = Counter(r["verdict"] for r in report)
    print("zero-valued holds:", len(report), dict(cnt))
    by = Counter((r["key"].split("|")[0], r["verdict"]) for r in report)
    print({f"{k[0]}:{k[1]}": v for k, v in sorted(by.items())})
    reasons = Counter(r["reason"][:70] for r in report if r["verdict"] == "KEEP_HELD")
    for k, v in reasons.most_common(12):
        print("  KEEP_HELD", v, k)


if __name__ == "__main__":
    main()
