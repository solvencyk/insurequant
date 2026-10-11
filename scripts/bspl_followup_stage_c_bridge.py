#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5b: prior-year-end BRIDGE calibration for held K-form BS cells (no DART anchor).

Why: for companies without a DART series (reinsurers) the master's year-end cells are the audited statement lines, while the interim 8-1 K
section prints its own line names (현금및현금성자산 vs the audited 현금및예치금, 상각후원가측정금융자산 vs the audited 기타수취채권, ...).  Stage B
refused such lines (no anchor concept).  The interim 8-1 prints [current, prior year-end]; the prior-year-end column of the filings of year D+1
IS the audited balance of D.  So an interim line k and an audited line a are the SAME line when value(k, prior col, filing of D+1) ==
value(a, audited statement of D) for every year-end D that both exist (>= 2 year-ends, nonzero, within 0.15 % / two printed half-steps) and a is
the unique audited line with that value.  A bridged concept is accepted for the item; then
   * interim cells  = the current column of the K table of that line in each quarter whose master cell is blank, and
   * year-end cells  = the audited line (value-matched) of the Q4 audit statement, loaded with the audited exact value.
Item 24 (기타부채) is the cautionary case: the interim aggregate is NOT the audited line (뮌헨 2023.12.31: interim 47,709 = audited 기타부채 19,964 +
기타금융부채 3,678 + 충당부채 269 + 법인세부채 295 + 이연법인세부채 23,503) -> no bridge -> stays held (mixed definition).
Output: bridge_report.json (per company/item verdict + matched labels) and bridge_cells.json (cells in manual schema).  Read-only.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.views import view_all, canon, col  # noqa: E402

W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
TAIL = " (inbox/parser/20261011T0900Z bspl follow-up, step 5b bridge)"
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
CODES = ["KR0004", "KR0029", "KR0049", "KR0050", "KR0051", "KR0074", "KR0075", "KR0076", "KR0080", "KR0095", "KR0097", "KR0100", "KR1010", "KR1011", "KR1098",
         "KR1101", "KR1102", "KR1103", "KR1104", "KR1105", "KR1106", "KR1107", "KR1108"]
# item -> (interim K canonical concepts that carry the line, tolerance rel)
ITEMS = {10: ("현금및현금성자산", "현금및예치금"), 13: ("AC_FA",), 14: ("재보험계약자산",), 15: ("유형자산",), 11: ("FVPL",), 12: ("FVOCI",), 24: ("기타부채",)}
REL = 0.0015
B_CANON = {10: ("현금및현금성자산", "현금및예치금"), 13: ("AC_FA", "AC_SEC"), 14: ("재보험계약자산",), 15: ("유형자산",), 11: ("FVPL",), 12: ("FVOCI",), 24: ("기타부채",)}


def audit_rows(doc, ci):
    """all rows of the first audited 8-1 statement of this Q4 filing: [(label, canon, value_mn)] for column ci (0 current, 1 prior)"""
    for t in doc["tables"]:
        if t["kind"] == "bs_full" and t.get("src") == "audit":
            f = B.UNIT_FACTOR.get(t.get("unit"))
            if f is None:
                continue
            out = []
            for r in t["rows"]:
                if len(r["vals"]) > ci and r["vals"][ci] is not None:
                    v = 0.0 if r["dash"][ci] else r["vals"][ci]
                    out.append((r["label"], canon(r["label"], "bs"), v * f, t["page"], t.get("pdf")))
            if len(out) >= 8:
                return out, t
    return [], None


def stmt_rows_fallback(doc, unit, ci):
    """Q4 filing without a raw_aux audit PDF: the annual disclosure embeds the audited statement as its first K-form 8-1 table (unit resolved by Stage B)"""
    f = B.UNIT_FACTOR.get(unit)
    if f is None:
        return [], None
    for t in B.pick_tables(doc, "bs_full"):
        if B.table_form(t) != "K" or not B._has_cols(t, 2 if ci else 1):
            continue
        out = []
        for r in t["rows"]:
            if len(r["vals"]) > ci and r["vals"][ci] is not None:
                v = 0.0 if r["dash"][ci] else r["vals"][ci]
                out.append((r["label"], canon(r["label"], "bs"), v * f, t["page"], doc["pdf"]))
        if len(out) >= 8:
            return out, t
    return [], None


def near(a, b, prec):
    return abs(a - b) <= max(REL * abs(b), 2 * prec, 0.011)


def main():
    all_v, anchor, disc, meta = B.load_master()
    report, cells = {}, []
    for code in CODES:
        docs = {q: B.load_tables(code, q) for q in QS}
        docs = {q: d for q, d in docs.items() if d}
        mv = all_v.get(code, {})
        kpi = B.load_kpi_anchors(code) if not anchor.get(code) else {}
        # audited statements per year-end D: current col at the Q4 filing; prior col at the next year's Q4 filing
        aud = {}
        # interim K tables' prior-year-end column, via the same observation machinery (units resolved against the master / KPI)
        obs_by_q, uinfos = {}, {}
        for q, d in docs.items():
            unit_ref = {it: v for (it, qq), v in kpi.items() if qq == q} if kpi else None
            obs, uinfo, notes = B.observations(code, q, d, all_v, disc, unit_ref)
            bad = set()
            for kind, (unit, how) in uinfo.items():
                if kind == "equity" or unit is None:
                    continue
                ok, det = B.table_identity(d, kind, unit)
                if ok is False:
                    bad.add(kind)
            obs_by_q[q] = [o for o in obs if o.kind not in bad]
            uinfos[q] = uinfo
        for q, d in docs.items():
            if not q.endswith("4Q"):
                continue
            rows, t = audit_rows(d, 0)
            rows1, t1 = audit_rows(d, 1)
            if not rows:
                rows, t = stmt_rows_fallback(d, (uinfos.get(q, {}).get("bs_full") or (None,))[0], 0)
                rows1, t1 = stmt_rows_fallback(d, (uinfos.get(q, {}).get("bs_full") or (None,))[0], 1)
            if rows:
                aud.setdefault(q, []).append(("cur", rows, t))
            if rows1:
                aud.setdefault(B.prev_year_end(q), []).append(("prior", rows1, t1))
        for item, concepts in ITEMS.items():
            rep = {"item": item, "years": {}, "matched_labels": set(), "verdict": None}
            by_d = defaultdict(list)                       # D -> [(interim obs c1 value, label)]
            for q, obs in obs_by_q.items():
                for o in obs:
                    if o.item != item or o.kind != "bs_full" or o.form != "K" or not o.comparative or o.col != 1:
                        continue
                    if o.concept[1][0] not in concepts and not (o.concept[2] == "first" and o.concept[1][0] in concepts):
                        continue
                    if o.concept[2] not in ("first",) and item in (11, 12):
                        continue
                    by_d[o.quarter].append((o.value_mn, o.concept[1][0], o.prec_mn, q))
            ok_years, bad_years = [], []
            for D, lst in sorted(by_d.items()):
                if D in B.FORBIDDEN_ANCHOR_Q:
                    continue
                v, lab, prec, q0 = lst[0]
                rows = [r for kind, rr, t in aud.get(D, []) for r in rr]
                if not rows:
                    rep["years"][D] = {"interim": round(v, 4), "note": "no audited statement"}
                    continue
                if abs(v) < 1e-9:
                    # a zero interim line must meet an audited zero / absent line of the same kind; an audited NON-zero line of the same
                    # canonical label is a contradiction (KR1107: the 2025 interim 상각후원가측정금융자산 line is 0 against 1,770 audited)
                    same = [(l, round(x, 4)) for l, c, x, pg, pdf in rows if x is not None and c in B_CANON.get(item, ()) and abs(x) > max(2 * prec, 0.011)]
                    if same:
                        bad_years.append(D)
                        rep["years"][D] = {"interim": 0.0, "audited_same_label_nonzero": same}
                    continue
                hits = {(l, round(x, 4)) for l, c, x, pg, pdf in rows if x is not None and abs(x) > 1e-9 and near(v, x, prec)}
                if len({l for l, x in hits}) == 1:
                    mval = mv.get((item, D))
                    xa = sorted(hits)[0][1]
                    if mval is not None and not near(mval, xa, prec):
                        # the master's own year-end cell (DART / audit-report series) is a different line than the disclosure's audited line:
                        # bridging the interim line to the disclosure statement would mix definitions with the master series
                        bad_years.append(D)
                        rep["years"][D] = {"interim": round(v, 4), "audited": sorted(hits)[0], "master_year_end": round(mval, 4), "note": "master year-end differs from the matched audited line"}
                        continue
                    ok_years.append(D)
                    rep["matched_labels"].add(next(iter({l for l, x in hits})))
                    rep["years"][D] = {"interim": round(v, 4), "audited": sorted(hits)[0]}
                else:
                    bad_years.append(D)
                    rep["years"][D] = {"interim": round(v, 4), "audited_hits": sorted(hits)}
            if len(ok_years) >= 2 and not bad_years and len(rep["matched_labels"]) == 1:
                rep["verdict"] = "BRIDGE_OK"
            else:
                rep["verdict"] = "NO_BRIDGE" if (ok_years or bad_years or by_d) else "NO_INTERIM_K_LINE"
            rep["matched_labels"] = sorted(rep["matched_labels"])
            report[f"{code}|{item}"] = rep
            if rep["verdict"] != "BRIDGE_OK":
                continue
            alabel = rep["matched_labels"][0]
            # --- interim cells: c0 of the K table observations whose master cell is blank
            for q, obs in sorted(obs_by_q.items(), key=lambda kv: B.qkey(kv[0])):
                if q.endswith("4Q") and q in aud and any(k == "cur" for k, *_ in aud[q]):
                    continue                                   # year-end handled from the audited statement below
                if (item, q) in mv:
                    continue
                cand = [o for o in obs if o.item == item and o.kind == "bs_full" and o.form == "K" and not o.comparative and o.col == 0
                        and o.concept[1][0] in concepts and o.concept[2] == "first"]
                if not cand:
                    continue
                o = min(cand, key=lambda o: o.prec_mn)
                cells.append({"code": code, "item": item, "quarter": q, "status": "MANUAL", "calib": "bridge_ok", "value_mn": o.value_mn, "rule": B.cname(o.concept),
                              "kind": o.kind, "form": o.form, "page": o.page, "unit": o.unit, "unit_how": o.how, "prec_mn": o.prec_mn, "tol_mn": o.tol_mn,
                              "pdf": o.src_pdf or docs[q]["pdf"], "sha256": o.src_sha or docs[q]["sha256"],
                              "basis": (f"정기경영공시 {q} 재무상태표(8-1 K 구간) p{o.page} 라인「{o.concept[1][0]}」 {o.value_mn / 100:,.3f}억(단위 {o.unit}, 정밀도 ±{o.prec_mn:g}백만원). "
                                        f"프라이어-연말 브리지 5b: 이 라인의 전기말 열 값이 감사 재무제표의 「{alabel}」 라인과 연말 {', '.join(sorted(ok_years))} 에서 모두 같다"
                                        f"(≥2개 연말, 유일 일치) -- 마스터의 감사 연말 칸과 같은 라인. 표 항등식(자산 = 부채 + 자본) 폐합 확인." + TAIL)})
            # --- year-end cells from the audited statement
            for D in sorted(aud):
                if D not in QS or (item, D) in mv:
                    continue
                for kind, rows, t in aud[D]:
                    if kind != "cur":
                        continue
                    hit = [r for r in rows if r[0] == alabel or r[0].replace(" ", "").endswith(alabel.replace(" ", ""))]
                    if len(hit) != 1:
                        continue
                    l, c, x, pg, pdf = hit[0]
                    d = docs[D]
                    cells.append({"code": code, "item": item, "quarter": D, "status": "MANUAL", "calib": "bridge_ok", "value_mn": x, "rule": f"{item}:{alabel}(audit)",
                                  "kind": "bs_full", "form": "K", "page": pg, "unit": "원", "unit_how": "audit statement", "prec_mn": 5e-07, "tol_mn": 0.02,
                                  "pdf": pdf or d["pdf"], "sha256": d["sha256"],
                                  "basis": (f"감사 재무상태표({D}) p{pg} 라인「{alabel}」 {x:,.3f}백만원(원 단위). 프라이어-연말 브리지 5b: 이 라인은 해당 회사 경영공시 8-1 K 구간의 "
                                            f"항목 {item} 라인과 전기말 열 값이 연말 {', '.join(sorted(ok_years))} 에서 모두 같아 같은 라인이다(유일 일치)." + TAIL)})
    for r in report.values():
        r["years"] = {k: v for k, v in r["years"].items()}
    (W / "bridge_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, default=list), encoding="utf-8", newline="\n")
    (W / "bridge_cells.json").write_text(json.dumps({"_note": "step 5b bridge cells (manual schema)", "cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    cnt = defaultdict(int)
    for k, r in report.items():
        cnt[r["verdict"]] += 1
    print(dict(cnt), "cells:", len(cells))
    for k, r in sorted(report.items()):
        if r["verdict"] == "BRIDGE_OK":
            n = sum(1 for c in cells if f"{c['code']}|{c['item']}" == k)
            print(" BRIDGE_OK", k, r["matched_labels"], "cells", n)
    for k, r in sorted(report.items()):
        if r["verdict"] == "NO_BRIDGE":
            print(" NO_BRIDGE", k, json.dumps(r["years"], ensure_ascii=False)[:230])


if __name__ == "__main__":
    main()
