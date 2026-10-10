# -*- coding: utf-8 -*-
"""
LIC stage 2 (owner 2026-10-10 「계산값 사용」): INDIRECT 발생사고요소 BEL / RA of the non-PAA book for the filers that disclose the LIC in ONE column only
(class T, and the non-PAA part of class A2).  New items of insurance_liability_portfolio.json

    16 발생사고요소_최선추정_간접(비PAA)   = 측정요소별 변동표 기말 BEL (DART, 별도, 당기)  -  경영공시 2-4 BEL (items 1 + 4) x100
    17 발생사고요소_위험조정_간접(비PAA)   = 측정요소별 변동표 기말 RA                       -  경영공시 2-4 RA  (items 2 + 5) x100

(2-4 holds the 잔여보장요소 only, the DART measurement tables hold LRC + LIC together, so the difference is the LIC's BEL / RA.)

A cell is written ONLY when it passes all of these, each recorded in the provenance (list `indirect_lic_cells`, basis = "derived"):
  1. window     a contiguous run of the cell's measurement-element tables (별도, 발행한 보험계약, current period, unit known) whose closing CSM equals the 2-4 CSM
                (items 3 + 6) x100 within max(60 백만원, 1e-4) -- the 2-4 table is in 억원 so its 합계 is a sum of rounded lines.  The CSM equality selects the
                right book at once (a product subset or a prior-period table does not reproduce the 2-4 CSM).
  2. whitelist  indirect BEL + RA equals the DIRECTLY disclosed single-column LIC of the same cell (item 13 x100) within max(500 백만원, 0.05 %)
                (the criterion owner-approved on 2026-10-10: only cells whose direct value is reproduced are written)
  3. exclusion  the three filers whose 2-4 total already contains the LIC (data/_derived/ilp_includes_lic.json) are never derived (indirect would be 0 there);
                cells on the restated (latest-filing) basis are skipped as well (the measurement tables of the original and of the restated filing differ).
  4. unique     if several accepted windows give different BEL/RA splits the cell is reported as ambiguous and NOT written.

Both the LIABILITY closing row and the NET (after 보험계약자산) closing row are tried; the one that reproduces item 13 is used (flag `row`).
Reader is pure; the writer is guarded + additive (back up first, abort on an existing key, byte round-trip check) -- same discipline as stage 1.

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_insurance_liability_lic_indirect.py [--quarters 2025.1Q ...] [--codes KR0069 ...] [--report out.json] [--write]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_lic as X  # noqa: E402

PROV = REPO / "insurance_liability_portfolio_provenance.json"
SIDE_INCL = REPO / "data" / "_derived" / "ilp_includes_lic.json"
TICKET = "inbox/parser/20261011T0320Z__orchestrator__MULTI_2023.1Q-2026.2Q__ilp_remaining_backfill_lic23_reinsurers.md"
TOL_CSM_ABS, TOL_CSM_REL = 60.0, 1e-4         # 백만원: 2-4 is in 억원
TOL_LIC_ABS, TOL_LIC_REL = 500.0, 5e-4        # 백만원: owner-approved whitelist criterion
SC = X.UNIT_SCALE


def me_role(path: str):
    """column role of a measurement-element table: BEL / RA / CSM / TOT (None for anything else)"""
    leaf = path.split("|")[-1]
    if X.PRIOR_COL.search(path):
        return None
    if leaf in ("합계", "계", "총계") or leaf.endswith("합계"):
        return "TOT"
    if leaf == "소계":
        return None                 # a sub-total column under 보험계약마진 (신한라이프) would double the CSM
    if "보험계약마진" in path:
        return "CSM"
    if "위험조정" in path or "위험요소" in path:
        return "RA"
    if ("현금흐름" in path and "취득" not in path) or "최선추정" in path:
        return "BEL"
    return None


def harvest_me(path):
    """measurement-element tables of one xml (BEL, RA and CSM columns, no 잔여보장/발생사고 split) in document order, as records the stage-1 annotator
    understands (note, top, pre, unit_cue, nrows, ncols, hdr, roles, rows{cls: {label, vals}}).  Pure function of the file bytes."""
    t = X.read_xml(path)
    ms = X.markers(t)
    tops = [(m.start(), m.group(1).strip()) for m in X.TITLE_RE.finditer(t) if re.search(r"재무제표|재무상태표|주석|감사보고서", m.group(1))]
    out = []
    prev_small, prev_unit, last_end = "", None, 0
    for i, m in enumerate(X.TAB_RE.finditer(t)):
        b = m.group(0)
        ntr = b.upper().count("<TR")
        s_pos = m.start()
        pre = X.clean(t[max(last_end, s_pos - 1500):s_pos])[-260:]
        last_end = m.end()
        if ntr <= 3:
            sm = X.clean(b)
            prev_small, prev_unit = sm[:200], X.unit_of(sm)
            continue
        if ntr >= 8 and "보험계약마진" in b and "위험조정" in b and ("현금흐름" in b or "최선추정" in b):
            g, _ = X.parse_table(b)
            h = X.split_header_rows(g)
            nl = X.label_cols(g, h)
            paths = X.col_paths(g, h)
            roles = [me_role(p) if k >= nl else None for k, p in enumerate(paths)]
            if any(("발생사고" in pp or "잔여보장" in pp) for pp in paths) or not {"BEL", "RA", "CSM"} <= set(roles):
                prev_small, prev_unit = "", None
                continue
            if not any(re.search(r"기초|기시", X.row_label(r, nl)) for r in g[h:]):
                prev_small, prev_unit = "", None
                continue
            rows, mode = {}, None
            for r in g[h:]:
                lab = X.row_label(r, nl)
                if re.search(r"기초|기시", lab):
                    mode = "open"
                elif "말" in lab:
                    mode = "close"
                cls = X.classify_row(lab)
                if not cls and mode == "close":
                    cls = X.classify_bare(lab)
                if not cls:
                    continue
                vals = [X.parse_num(c) if k >= nl else None for k, c in enumerate(r)]
                if not any(x is not None for x in vals):
                    continue
                rows.setdefault(cls, {"label": lab[:60], "vals": vals})
            in_table_unit = X.unit_of(" ".join(r[0] for r in g[:min(h, 2)]))           # '(단위:백만원)' is the first header cell of some filers (신한라이프)
            out.append({"i": i, "pos": s_pos, "note": X.scope_at(ms, s_pos), "top": X.scope_at(tops, s_pos), "pre": (prev_small + " " + pre)[-200:],
                        "unit_cue": in_table_unit or prev_unit or X.unit_of(prev_small + " " + pre), "nrows": len(g), "ncols": len(g[0]), "h": h, "nl": nl,
                        "hdr": X.comp(" ".join(" ".join(r) for r in g[:max(h, 1)]))[:300], "paths": paths, "roles": roles, "roles_loose": roles,
                        "rows": rows, "open_rows": {}, "period_cue": X.explicit_period(prev_small + " " + pre[-140:])})
        prev_small, prev_unit = "", None
    return out


def sums(t, k, cls):
    r = t["rows"].get(cls)
    if r is None:
        return None
    vals = r["vals"]
    s = {"BEL": 0.0, "RA": 0.0, "CSM": 0.0}
    for c, role in enumerate(t["roles"]):
        if role in s and c < len(vals) and vals[c] is not None:
            s[role] += vals[c]
    return {x: v * k for x, v in s.items()}


def windows(el, cls_pref):
    """all contiguous windows of the eligible tables with their (BEL, RA, CSM) sums on the closing-row class cls_pref ('LIAB' or 'NET'); a table without that
    row class falls back to the other one (a LIAB-only table has no NET row and vice versa)"""
    per = []
    for t, k in el:
        per.append(sums(t, k, cls_pref) or sums(t, k, "NET" if cls_pref == "LIAB" else "LIAB"))
    n = len(el)
    for a in range(n):
        acc = {"BEL": 0.0, "RA": 0.0, "CSM": 0.0}
        for b in range(a, n):
            if per[b] is None:
                break
            for x in acc:
                acc[x] += per[b][x]
            yield a, b, dict(acc)


def candidates(el, two4_bel, two4_ra, two4_csm, direct, offset=None):
    """offset = (item 14 - item 8) x100 = the 보험계약자산 offset by which the 2-4 (NET of assets) is below the DART liability-basis LRC.  On the LIABILITY row the
    indirect BEL+RA is  LIC + offset  (ME holds LRC_liab + LIC, 2-4 holds LRC_net), so a cell whose gap equals the offset reproduces the direct LIC once the 2-4 is
    brought to the liability basis (flag asset_offset_adjusted; the whole offset is taken off the BEL: CSM is equal, the RA part is negligible)."""
    tol_csm = max(TOL_CSM_ABS, TOL_CSM_REL * abs(two4_csm))
    tol_lic = max(TOL_LIC_ABS, TOL_LIC_REL * abs(direct))
    out = []
    for cls in ("LIAB", "NET"):
        for a, b, s in windows(el, cls):
            if abs(s["CSM"] - two4_csm) > tol_csm:
                continue
            ib, ir = s["BEL"] - two4_bel, s["RA"] - two4_ra
            gap = ib + ir - direct
            c = {"row": cls, "tables": [el[j][0]["i"] for j in range(a, b + 1)], "n": b - a + 1, "me": s, "ind_bel": ib, "ind_ra": ir, "gap": gap,
                 "ok": abs(gap) <= tol_lic, "csm_diff": s["CSM"] - two4_csm, "adjusted": False}
            if not c["ok"] and cls == "LIAB" and offset is not None and abs(offset) > tol_lic and abs(gap - offset) <= tol_lic:
                c.update(ok=True, adjusted=True, offset=offset, ind_bel=ib - offset, gap=gap - offset, gap_plain=gap)
            out.append(c)
    return out, tol_csm, tol_lic


def derive(code, q, d, src):
    """-> result dict for one cell.  d = master items of the cell; src = DART source file (repo-relative).  status: ok | fail | no_me | no_window"""
    two4_bel = ((d.get(1) or 0.0) + (d.get(4) or 0.0)) * 100.0
    two4_ra = ((d.get(2) or 0.0) + (d.get(5) or 0.0)) * 100.0
    two4_csm = ((d.get(3) or 0.0) + (d.get(6) or 0.0)) * 100.0
    direct = d[13] * 100.0
    offset = (d[14] - d[8]) * 100.0 if (d.get(14) is not None and d.get(8) is not None) else None
    tabs = X.annotate_tables(harvest_me(str(REPO / src)))
    base = [(t, SC.get(t["unit"])) for t in tabs if not t["reins"] and not t["con"] and SC.get(t["unit"]) and ("LIAB" in t["rows"] or "NET" in t["rows"])]
    cur = [(t, k) for t, k in base if t["period"] == "cur"]
    res = {"code": code, "quarter": q, "direct_mm": direct, "two4": {"bel": two4_bel, "ra": two4_ra, "csm": two4_csm}, "n_me_tables": len(tabs), "n_eligible": len(base), "n_current": len(cur)}
    if not base:
        res["status"] = "no_me"
        return res
    cands, mode = [], None
    for mode_name, el in (("current_period", cur), ("any_period", base)):
        if not el:
            continue
        cands, tol_csm, tol_lic = candidates(el, two4_bel, two4_ra, two4_csm, direct, offset)
        if cands:
            mode = mode_name
            break
    if not cands:
        res["status"] = "no_window"
        res["tables_csm"] = [(t["i"], t["period"], {x: round(v) for x, v in (sums(t, k, "LIAB") or sums(t, k, "NET") or {}).items()}) for t, k in base][:8]
        return res
    res.update(mode=mode, tol_csm=tol_csm, tol_lic=tol_lic, candidates=len(cands))
    # plain passes first, then the offset-adjusted ones; shorter windows first
    ok = sorted((c for c in cands if c["ok"]), key=lambda c: (c["adjusted"], c["n"], abs(c["gap"]), c["row"]))
    if not ok:
        res.update(status="fail", best=sorted(cands, key=lambda c: abs(c["gap"]))[0])
        return res
    same_kind = [c for c in ok if c["adjusted"] == ok[0]["adjusted"]]
    # accepted windows are 'different answers' only if their BEL/RA differ by more than the rounding noise of the 2-4 table (200 백만원)
    spread = max(max(c["ind_bel"] for c in same_kind) - min(c["ind_bel"] for c in same_kind), max(c["ind_ra"] for c in same_kind) - min(c["ind_ra"] for c in same_kind))
    res.update(status="ok", best=ok[0], n_ok=len(same_kind), ambiguous=spread > 200.0, spread_mm=round(spread, 1))
    return res


# ------------------------------------------------------------------------------------------------------------------------------
def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def targets(quarters):
    ilp = load_json(X.ILP)
    prov = load_json(PROV)
    incl_cos = set(load_json(SIDE_INCL).get("companies", {}))
    items = {}
    for r in ilp:
        items.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]
    cells = {(c["company_code"], c["quarter"]): c for c in prov["cells"]}
    out, skipped = [], []
    for (code, q), d in sorted(items.items()):
        if q not in quarters or (code, q) not in cells:
            continue
        pc = cells[(code, q)]
        if (d.get(13) or 0.0) <= 0 or 1 not in d or 8 not in d:
            continue
        if code in incl_cos:
            skipped.append((code, q, "2-4 total already contains the LIC (sidecar company)"))
            continue
        if pc.get("period_basis"):
            skipped.append((code, q, "cell is on the restated latest-filing basis (items 10-15 from the 2025 prior-period tables)"))
            continue
        out.append((code, q, d, pc))
    return out, items, cells, skipped


def eok(mm: float) -> float:
    return round(mm / 100.0, 2) + 0.0


def write_cells(oks, results_by_key, ilp_rows_reg):
    """append items 16/17 of the accepted cells + provenance list indirect_lic_cells (additive, guarded)"""
    new_rows = []
    for code, q, d, pc, r in oks:
        b = r["best"]
        info = ilp_rows_reg[code]
        for n, v in ((16, eok(b["ind_bel"])), (17, eok(b["ind_ra"]))):
            name, section, level = X.ITEM_CATALOG[n]
            new_rows.append({"원보험사코드": code, "원수사명": info["원수사명"], "티커": info["티커"], "생손보여부": info["생손보여부"], "항목번호": n, "항목명": name,
                             "섹션": section, "레벨": level, "공시분기": q, "값": v})
    new_rows.sort(key=lambda x: (x["원보험사코드"], x["공시분기"], x["항목번호"]))
    backup = X.merge_into_ilp(new_rows, tag="pre_lic_stage2")
    raw0 = PROV.read_bytes()
    txt = raw0.decode("utf-8")
    prov = json.loads(txt)
    if json.dumps(prov, ensure_ascii=False, indent=1) + "\n" != txt:
        raise SystemExit("abort: provenance file does not round-trip byte for byte")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    pback = X.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_lic_stage2.json"
    k = 2
    while pback.exists():
        pback = X.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_lic_stage2_{k}.json"
        k += 1
    shutil.copyfile(PROV, pback)
    have = {(c["company_code"], c["quarter"]) for c in prov.get("indirect_lic_cells", [])}
    recs = []
    for code, q, d, pc, r in oks:
        if (code, q) in have:
            raise SystemExit(f"abort: indirect_lic_cells already has {(code, q)}")
        b = r["best"]
        recs.append({
            "company_code": code, "quarter": q, "item_block": "lic_indirect_bel_ra", "basis": "derived", "source_file": pc["source_file"],
            "as_of_date": X.as_of_date(q), "class": pc["class"], "mode": r["mode"], "row": b["row"], "window_tables": b["tables"],
            "formula": "item16 = sum(BEL closing of the window tables) - (items 1+4)x100 ; item17 = sum(RA closing) - (items 2+5)x100 ; 백만원 -> 억원 /100",
            "me_closing_mm": {x: round(v, 1) for x, v in b["me"].items()},
            "two_four_x100_mm": {x: round(v, 1) for x, v in r["two4"].items()},
            "indirect_mm": {"bel": round(b["ind_bel"], 1), "ra": round(b["ind_ra"], 1)},
            "direct_item13_mm": round(r["direct_mm"], 1), "gap_mm": round(b["gap"], 1), "tolerance_mm": round(r["tol_lic"], 1),
            "csm_diff_mm": round(b["csm_diff"], 1), "csm_tolerance_mm": round(r["tol_csm"], 1),
            "asset_offset_adjusted": bool(b.get("adjusted")),
            **({"asset_offset_mm": round(b["offset"], 1), "gap_plain_mm": round(b["gap_plain"], 1),
                "adjustment_note": "2-4 is NET of 보험계약자산, the DART tables hold the liability basis: ME(BEL+RA) - 2-4(BEL+RA) = LIC + (item14 - item8)x100; the offset was taken off the BEL "
                                   "(CSM equal, RA part negligible), the adjusted sum reproduces item 13"} if b.get("adjusted") else {}),
            "n_accepted_windows": r["n_ok"], "items_eok": {"16": eok(b["ind_bel"]), "17": eok(b["ind_ra"])},
            "criterion": "indirect BEL+RA reproduces the directly disclosed single-column LIC (item 13) within max(500 백만원, 0.05 %) -- owner decision 2026-10-10 (계산값 사용, 화이트리스트)"})
    prov["indirect_lic_cells"] = prov.get("indirect_lic_cells", []) + recs
    prov["backfills"] = prov.get("backfills", []) + [{
        "stage": "lic-stage2-indirect", "at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"), "emitted_by": "scripts/extract_insurance_liability_lic_indirect.py", "ticket": TICKET,
        "note": f"items 16/17 (indirect BEL/RA of the non-PAA LIC) for {len(recs)} cells that reproduce the direct single-column LIC (item 13); see indirect_lic_cells"}]
    out = json.dumps(prov, ensure_ascii=False, indent=1) + "\n"
    tmp = PROV.with_name(PROV.name + ".tmp")
    tmp.write_bytes(out.encode("utf-8"))
    os.replace(tmp, PROV)
    return backup, pback, len(new_rows)


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--quarters", nargs="*")
    ap.add_argument("--codes", nargs="*", help="debug: restrict to these company codes (never with --write)")
    ap.add_argument("--report")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    if args.write and args.codes:
        raise SystemExit("--write needs the full run (no --codes)")
    qs = set(args.quarters) if args.quarters else set(X.QMAP.values())
    tg, items, cells, skipped = targets(qs)
    if args.codes:
        tg = [x for x in tg if x[0] in set(args.codes)]
    results, oks = [], []
    for code, q, d, pc in tg:
        r = derive(code, q, d, pc["source_file"])
        results.append(r)
        b = r.get("best")
        tail = ""
        if b:
            tail = (f" mode={r['mode']} window T{b['tables']} row={b['row']}{' ADJ(asset offset ' + format(b['offset'], ',.0f') + ')' if b.get('adjusted') else ''} "
                    f"ind BEL {b['ind_bel']:,.0f} RA {b['ind_ra']:,.0f} sum {b['ind_bel'] + b['ind_ra']:,.0f} vs direct {r['direct_mm']:,.0f} gap {b['gap']:,.0f}")
        print(f"{code} {q} {pc['class']:2s} {r['status']:9s}{tail}" + (" AMBIGUOUS" if r.get("ambiguous") else ""), flush=True)
        if r["status"] == "ok" and not r.get("ambiguous"):
            oks.append((code, q, d, pc, r))
    print(collections.Counter(r["status"] for r in results), "ambiguous:", sum(1 for r in results if r.get("ambiguous")), "| skipped (excluded):", len(skipped))
    for s in skipped:
        print("  skipped", s)
    if args.report:
        Path(args.report).write_text(json.dumps(results, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if args.write:
        ilp = load_json(X.ILP)
        reg = X.ilp_registry(ilp)
        backup, pback, n = write_cells(oks, {}, reg)
        print(f"appended {n} rows ({len(oks)} cells); backup {backup.name}; provenance backup {pback.name}")
    else:
        print(f"dry run: {len(oks)} cells would be written (use --write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
