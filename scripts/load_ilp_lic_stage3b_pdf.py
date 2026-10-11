# -*- coding: utf-8 -*-
"""
ILP leftovers (ticket 20261011T1000Z, task 2), "LIC stage 3b": the pre-2025 quarters of the two non-listed filers whose 경영공시 PDF prints the incurred-claims component
although DART has no 분기·반기보고서 (stage 3 of ticket 20261011T0320Z loaded only their 2025-2026 quarters).

  KR0074 라이나생명  2023.1Q-3Q   class T (발생사고 단일열): items 10, 13, 14, 15.  Closing row 「기말 보험계약부채」 of the issued-contract LRC/LIC note (천원).
        The 2023 layout has a 4th column 「보험취득현금흐름자산」 (5 numbers); item 14 = total - LIC (the DART engine's definition: the IACF asset sits in the LRC side).
        Source rule = the LATEST filing that prints the quarter (owner: 「최신 공시 쓰기」): the 전분기 table of the FY2024 filing of the same quarter, confirmed by the own FY2023 filing.
          2023.1Q, 2023.2Q: the FY2024_Q1/Q2 전분기 tables equal the own filings (old 5-column layout)               -> loaded, basis = own filing confirmed by the later comparative
          2023.3Q: the FY2024_Q3 전분기 table is RESTATED (new 4-column layout, 보험계약의 경계 변경 소급, total 2,843.84억 vs 4,405.19억 originally) -> loaded on the restated basis,
                   original values kept in the provenance and in the restated-comparative sidecar (the sidecar is the R-LIC1 anchor of a restated cell)
  KR0100 처브라이프  2023.1Q-2024.3Q  class A1 (BEL / RA split): items 10-15, 13 = 0.  The 업무보고서식 재무상태표 「1. 보험계약부채 / 가. 잔여보장요소 / 나. 발생사고요소 / (1) 최선추정 (2) 위험조정」 (원).
        General-account basis, exactly like the 2025.1Q-3Q cells of stage 3 (the special-account 변액 liabilities are not in these lines; LIC is the same on both bases, see the checks).

Every cell must pass or the whole run aborts (nothing is written):
  Lina   foot (LRC components + LIC + IACF = total), own = latest comparative OR a documented restatement, R-LIC1 against IFRS17_BS item 20 for original-basis cells (0.1 %), identity 10 + 14 = 15.
  Chubb  identities (가 + 나 + 다 = 1. 보험계약부채, (1) + (2) = 나), the prior-year-end column agrees across the three quarters of a year, R-LIC1 against IFRS17_BS item 20 where the BS lane has one (0.1 %).

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_lic_stage3b_pdf.py [--write] [--report out.json]
Writes (with --write): insurance_liability_portfolio.json (append-only, backed up), insurance_liability_portfolio_provenance.json (cells + backfills, backed up),
data/_derived/ilp_restated_comparative.json (one cell, backed up).
Undo = restore the three files from the backups named in the provenance `backfills` record (stage lic-stage3b-pdf): data/_derived/ilp_*_pre_lic_stage3b*.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import fitz
import pdfplumber

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_lic as lic  # noqa: E402
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

PROV = REPO / "insurance_liability_portfolio_provenance.json"
SIDE = REPO / "data" / "_derived" / "ilp_restated_comparative.json"
TICKET = "inbox/parser/20261011T1000Z__orchestrator__MULTI_2023.1Q-2026.2Q__ilp_leftovers_hana_attachments.md"
ITEMS = (10, 11, 12, 13, 14, 15)
TOL_ROUND = 0.0301

# ------------------------------------------------------------------------------------------------------------------------------
# Lina
# ------------------------------------------------------------------------------------------------------------------------------
LINA_PLAN = {"2023.1Q": ("FY2023_Q1", "FY2024_Q1"), "2023.2Q": ("FY2023_Q2", "FY2024_Q2"), "2023.3Q": ("FY2023_Q3", "FY2024_Q3")}
CLOSE = re.compile(r"^(?:분기말|반기말|기말)\s*보험계약부채\s+(?P<rest>.*)$")
CLOSE_ASSET = re.compile(r"^(?:분기말|반기말|기말)\s*보험계약자산\s+(?P<rest>.*)$")
PER = re.compile(r"^<\s*(당분기|당반기|전분기|전반기)\s*>")
TOK = re.compile(r"\(?-?\d[\d,]*\)?|(?<=\s)-(?=\s|$)")


def _nums(rest: str) -> list:
    out = []
    for t in TOK.findall(" " + rest):
        if t == "-":
            out.append(0.0)
        else:
            neg = t.startswith("(") and t.endswith(")")
            v = float(t.strip("()").replace(",", ""))
            out.append(-v if neg else v)
    return out


def lina_rows(path: Path) -> list:
    """closing rows (liability / asset) of the issued-contract LRC/LIC tables, with page and period marker"""
    lines = []
    with pdfplumber.open(str(path)) as pdf:
        for i, pg in enumerate(pdf.pages):
            for ln in (pg.extract_text() or "").split("\n"):
                if ln.strip():
                    lines.append((i + 1, ln.strip()))
    rows = []
    for k, (pg, s) in enumerate(lines):
        m, ma = CLOSE.match(s), CLOSE_ASSET.match(s)
        if not (m or ma):
            continue
        kind = per = None
        for j in range(k - 1, max(-1, k - 70), -1):
            t = lines[j][1]
            if per is None and PER.match(t):
                per = "cur" if PER.match(t).group(1).startswith("당") else "prior"
            if kind is None and "잔여보장부채" in t.replace(" ", "") and "보험계약마진" not in t:
                kind = "LRCLIC"
            if kind is None and "보험계약마진" in t:
                kind = "MEAS"
            if kind and per:
                break
        if kind == "LRCLIC":
            rows.append({"page": pg, "row": "LIAB" if m else "ASSET", "period": per, "nums": _nums((m or ma).group("rest")), "line": s[:150]})
    return rows


def lina_split(nums: list) -> dict | None:
    """5 numbers (2023 layout) or 4 numbers (2024+ layout) -> components in 천원"""
    if len(nums) == 5:
        return {"layout": "5col_with_iacf", "lrc_ex_loss": nums[0], "loss": nums[1], "lic": nums[2], "iacf": nums[3], "total": nums[4]}
    if len(nums) == 4:
        return {"layout": "4col", "lrc_ex_loss": nums[0], "loss": nums[1], "lic": nums[2], "iacf": 0.0, "total": nums[3]}
    return None


def lina_cells(M: dict, bs20: dict) -> tuple[list, list]:
    cells, notes = [], []
    for q, (fy_own, fy_next) in LINA_PLAN.items():
        own_pdf = disclosure_pdfs(fy_own, "KR0074")
        nxt_pdf = disclosure_pdfs(fy_next, "KR0074")
        if not own_pdf or not nxt_pdf:
            notes.append((q, f"PDF missing own={bool(own_pdf)} next-year={bool(nxt_pdf)}"))
            continue
        own = [r for r in lina_rows(own_pdf[0]) if r["row"] == "LIAB" and r["period"] == "cur"]
        asset_own = [r for r in lina_rows(own_pdf[0]) if r["row"] == "ASSET" and r["period"] == "cur"]
        nxt_all = lina_rows(nxt_pdf[0])
        nxt = [r for r in nxt_all if r["row"] == "LIAB" and r["period"] == "prior"]
        asset_nxt = [r for r in nxt_all if r["row"] == "ASSET" and r["period"] == "prior"]
        if len(own) != 1 or len(nxt) != 1:
            notes.append((q, f"closing row not unique: own {len(own)} next-year prior {len(nxt)}"))
            continue
        o, n = lina_split(own[0]["nums"]), lina_split(nxt[0]["nums"])
        if o is None or n is None:
            notes.append((q, f"column count: own {own[0]['nums']} next {nxt[0]['nums']}"))
            continue
        same = o["layout"] == n["layout"] and all(abs(o[k] - n[k]) <= 3 for k in ("lrc_ex_loss", "loss", "lic", "iacf", "total"))
        use = o if same else n
        use_row, use_file, use_asset = (own[0], own_pdf[0], asset_own) if same else (nxt[0], nxt_pdf[0], asset_nxt)
        a = lina_split(use_asset[0]["nums"]) if use_asset else None
        cells.append({"code": "KR0074", "quarter": q, "same": same, "own": o, "own_file": str(own_pdf[0].relative_to(REPO)).replace("\\", "/"), "own_page": own[0]["page"],
                      "next": n, "next_file": str(nxt_pdf[0].relative_to(REPO)).replace("\\", "/"), "next_page": nxt[0]["page"], "use": use, "use_file": str(use_file.relative_to(REPO)).replace("\\", "/"),
                      "use_page": use_row["page"], "use_line": use_row["line"], "use_period": "current" if same else "prior-year same quarter (<전분기> table of the FY2024 filing)",
                      "asset": a, "bs20_mm": bs20.get(("KR0074", q)), "class": "T"})
    return cells, notes


# ------------------------------------------------------------------------------------------------------------------------------
# Chubb
# ------------------------------------------------------------------------------------------------------------------------------
CHUBB_QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2024.1Q", "2024.2Q", "2024.3Q"]
NUMTOK = re.compile(r"^\(?-?[\d,]+\)?$|^[-—]$")


def _tonum(t: str) -> float:
    if t in ("-", "—"):
        return 0.0
    neg = t.startswith("(") and t.endswith(")")
    v = float(t.strip("()").replace(",", ""))
    return -v if neg else v


def _two_after(lines: list, k: int, span: int = 8):
    got = []
    for s in lines[k + 1: k + 1 + span]:
        if NUMTOK.match(s):
            got.append(_tonum(s))
            if len(got) == 2:
                return got
        elif re.match(r"^(\d\.|[가-라]\.|\(\d\)|\[)", s):
            break
    return None


def chubb_block(lines: list) -> dict | None:
    i1 = next((k for k, s in enumerate(lines) if s == "1. 보험계약부채"), None)
    if i1 is None:
        return None
    rec = {"total": _two_after(lines, i1)}
    i_lic = None
    for k in range(i1 + 1, min(i1 + 120, len(lines))):
        s = lines[k]
        if s == "2. 재보험계약부채":
            break
        if s == "가. 잔여보장요소" and "LRC" not in rec:
            rec["LRC"] = _two_after(lines, k)
        elif s == "나. 발생사고요소" and "LIC" not in rec:
            rec["LIC"] = _two_after(lines, k)
            i_lic = k
        elif s == "다. 사전인식 보험취득현금흐름" and "IACF" not in rec:
            rec["IACF"] = _two_after(lines, k)
        elif i_lic is not None and s == "(1) 최선추정" and "BEL" not in rec and k > i_lic:
            rec["BEL"] = _two_after(lines, k)
        elif i_lic is not None and s == "(2) 위험조정" and "RA" not in rec and "BEL" in rec:
            rec["RA"] = _two_after(lines, k)
    return rec if all(rec.get(x) for x in ("total", "LRC", "LIC", "BEL", "RA")) else None


def chubb_cells(M: dict, bs20: dict) -> tuple[list, list]:
    cells, notes = [], []
    for q in CHUBB_QS:
        fy = f"FY{q[:4]}_Q{q[5]}"
        pdfs = disclosure_pdfs(fy, "KR0100")
        found = []
        for p in pdfs:
            doc = fitz.open(str(p))
            for i, pg in enumerate(doc):
                t = pg.get_text("text") or ""
                if "나. 발생사고요소" not in t:
                    continue
                b = chubb_block([x.strip() for x in t.split("\n") if x.strip()])
                if b:
                    found.append((p, i + 1, b))
        if len(found) != 1:
            notes.append((q, f"balance-sheet block found {len(found)} times in {[p.name for p in pdfs]}"))
            continue
        p, pg, b = found[0]
        cur = {k: v[0] for k, v in b.items()}
        prv = {k: v[1] for k, v in b.items()}
        cells.append({"code": "KR0100", "quarter": q, "file": str(p.relative_to(REPO)).replace("\\", "/"), "page": pg, "cur_won": cur, "prev_won": prv, "bs20_mm": bs20.get(("KR0100", q)), "class": "A1"})
    return cells, notes


def eok_won(w: float) -> float:
    return round(w / 1e8, 2) + 0.0


def eok_chon(x: float) -> float:
    return round(x / 1e5, 2) + 0.0


def evaluate(cells: list, M: dict) -> tuple[list, list]:
    acc, rej = [], []
    by_year_prev = {}
    for c in cells:
        if c["code"] == "KR0100":
            by_year_prev.setdefault(c["quarter"][:4], []).append(c)
    for c in cells:
        why, extra = [], {}
        if c["code"] == "KR0074":
            u, o = c["use"], c["own"]
            foot = u["lrc_ex_loss"] + u["loss"] + u["lic"] + u["iacf"] - u["total"]
            if abs(foot) > 3:
                why.append(f"foot: {foot:.0f} 천원")
            items = {10: eok_chon(u["lic"]), 13: eok_chon(u["lic"]), 14: eok_chon(u["total"] - u["lic"]), 15: eok_chon(u["total"])}
            b = c["bs20_mm"]
            if c["same"]:
                if b is None:
                    why.append("no IFRS17_BS item 20 to close an original-basis cell against")
                elif abs(u["total"] / 1000.0 / b - 1) > lic.TOL_CLOSE:
                    why.append(f"R-LIC1: item 15 / BS item 20 = {u['total'] / 1000.0 / b:.5f}")
                extra["ratio_bs20"] = None if not b else round(u["total"] / 1000.0 / b, 6)
            else:
                extra["original_basis"] = {"layout": o["layout"], "lic_eok": eok_chon(o["lic"]), "lrc_eok": eok_chon(o["total"] - o["lic"]), "total_eok": eok_chon(o["total"]),
                                           "bs20_original_eok": None if b is None else lic.eok(b)}
                if b is not None and abs(o["total"] / 1000.0 / b - 1) > lic.TOL_CLOSE:
                    why.append(f"original-basis total {o['total'] / 1000.0:,.1f} 백만원 does not close with IFRS17_BS item 20 {b:,.1f}")
            if abs((items[10] + items[14]) - items[15]) > TOL_ROUND:
                why.append("identity 10 + 14 = 15 on rounded values")
            extra["asset_side_eok"] = None if not c["asset"] else {"total": eok_chon(c["asset"]["total"]), "lrc": eok_chon(c["asset"]["lrc_ex_loss"] + c["asset"]["loss"] + c["asset"]["iacf"]),
                                                                    "lic": eok_chon(c["asset"]["lic"])}
        else:
            cur, prv = c["cur_won"], c["prev_won"]
            iacf = cur.get("IACF") or 0.0
            if abs(cur["LRC"] + cur["LIC"] + iacf - cur["total"]) > 1 or abs(cur["BEL"] + cur["RA"] - cur["LIC"]) > 1:
                why.append("identities of the balance-sheet block")
            items = {10: eok_won(cur["LIC"]), 11: eok_won(cur["BEL"]), 12: eok_won(cur["RA"]), 13: 0.0, 14: eok_won(cur["total"] - cur["LIC"]), 15: eok_won(cur["total"])}
            if abs((items[11] + items[12] + items[13]) - items[10]) > TOL_ROUND or abs(items[10] + items[14] - items[15]) > TOL_ROUND:
                why.append("rounded identities")
            b = c["bs20_mm"]
            if b is not None:
                r = cur["total"] / 1e6 / b
                extra["ratio_bs20"] = round(r, 6)
                if abs(r - 1) > lic.TOL_CLOSE:
                    why.append(f"R-LIC1: item 15 / BS item 20 = {r:.5f}")
            # the prior-year-end column must be the same in all three quarters of the year
            sibs = by_year_prev[c["quarter"][:4]]
            for s in sibs:
                for k in ("total", "LIC", "BEL", "RA"):
                    if abs(s["prev_won"][k] - prv[k]) > 1:
                        why.append(f"prior-year-end column differs between {c['quarter']} and {s['quarter']} ({k})")
                        break
            extra["prior_year_end_eok"] = {"total": eok_won(prv["total"]), "lic": eok_won(prv["LIC"]), "bel": eok_won(prv["BEL"]), "ra": eok_won(prv["RA"])}
        (rej if why else acc).append((c, items, extra, why))
    return acc, rej


def _dump_prov(prov: dict) -> str:
    return json.dumps(prov, ensure_ascii=False, indent=1) + "\n"


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report")
    args = ap.parse_args(argv)
    ilp = json.loads(lic.ILP.read_text(encoding="utf-8"))
    reg = lic.ilp_registry(ilp)
    M = {}
    for r in ilp:
        M.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]
    bs20 = lic.load_bs20()

    cells, notes = [], []
    for fn in (lina_cells, chubb_cells):
        c, n = fn(M, bs20)
        cells += c
        notes += n
    for q, why in notes:
        print("NOTE", q, why)
    acc, rej = evaluate(cells, M)
    for c, items, extra, _ in acc:
        print(f"OK   {c['code']} {c['quarter']} {c['class']:2s} " + " ".join(f"{n}:{items[n]:,.2f}" for n in sorted(items)) + (f" | {'restated' if c.get('same') is False else 'own'}" if c["code"] == "KR0074" else "")
              + f" | {json.dumps(extra, ensure_ascii=False)[:200]}")
    for c, items, extra, why in rej:
        print(f"REJ  {c['code']} {c['quarter']}: {why}")
    have = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in ilp}
    new_rows = []
    for c, items, _, _ in acc:
        info = reg[c["code"]]
        for n, v in sorted(items.items()):
            if (c["code"], c["quarter"], n) in have:
                raise SystemExit(f"abort: key exists {(c['code'], c['quarter'], n)}")
            name, section, level = lic.ITEM_CATALOG[n]
            new_rows.append({"원보험사코드": c["code"], "원수사명": info["원수사명"], "티커": info["티커"], "생손보여부": info["생손보여부"], "항목번호": n, "항목명": name,
                             "섹션": section, "레벨": level, "공시분기": c["quarter"], "값": v})
    new_rows.sort(key=lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]))
    print(f"accepted cells {len(acc)}, rejected {len(rej)}, notes {len(notes)}, rows to add {len(new_rows)}")
    if args.report:
        Path(args.report).write_text(json.dumps({"accepted": [{"cell": c, "items": i, "extra": e} for c, i, e, _ in acc], "rejected": [{"cell": c, "why": w} for c, _, _, w in rej], "notes": notes},
                                                ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if rej or notes:
        print("abort: rejected cells or notes -- nothing written")
        return 1
    if not args.write:
        print("dry run: nothing written (use --write)")
        return 0

    backup = lic.merge_into_ilp(new_rows, tag="pre_lic_stage3b")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    # ---------------- provenance ----------------
    raw0 = PROV.read_bytes().decode("utf-8")
    prov = json.loads(raw0)
    if _dump_prov(prov) != raw0:
        raise SystemExit("abort: provenance does not round-trip")
    pback = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_lic_stage3b.json"
    k = 2
    while pback.exists():
        pback = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_lic_stage3b_{k}.json"
        k += 1
    shutil.copyfile(PROV, pback)
    have_cells = {(c["company_code"], c["quarter"]) for c in prov["cells"]}
    recs, side_cells = [], []
    for c, items, extra, _ in acc:
        if (c["code"], c["quarter"]) in have_cells:
            raise SystemExit(f"abort: provenance cell exists {(c['code'], c['quarter'])}")
        b = c["bs20_mm"]
        if c["code"] == "KR0074":
            u = c["use"]
            restated = c["same"] is False
            flags = ["pdf_source_no_dart_filing", "latest_filing_comparative"] + (["restated_comparative_not_closable_with_bs20"] if restated else ["own_filing_confirmed_by_later_comparative"])
            checks = {"r_lic1": "pass" if not restated else "pass_restated_sidecar", "bs20_eok": None if b is None else lic.eok(b), "ratio_bs20": extra.get("ratio_bs20"), "filing_bs_eok": None, "ratio_filing_bs": None,
                      "r_lic3_gap_eok": round(items[10] + items[14] - items[15], 4), "tag_tables": 0, "tag_cells": 0, "tag_mismatch": 0, "bs20_master_disagrees": False,
                      "foot_gap_chonwon": round(u["lrc_ex_loss"] + u["loss"] + u["lic"] + u["iacf"] - u["total"], 1)}
            rec = {"company_code": "KR0074", "quarter": c["quarter"], "item_block": "lic_pdf_note", "source_id": "PDF", "as_of_date": lic.as_of_date(c["quarter"]), "source_file": c["use_file"], "page": c["use_page"],
                   "scope": "separate", "period": c["use_period"], "class": "T", "bel_ra_source": "none", "basis": "liability", "row_basis": ["LIAB"], "unit": "천원", "unit_source": "cue", "tables": [],
                   "dropped_tables": [], "dedupe": [], "flags": flags, "checks": checks, "net_lrc_eok": None, "items_eok": {str(n): items[n] for n in sorted(items)},
                   "evidence": c["use_line"], "own_filing": {"file": c["own_file"], "page": c["own_page"], "layout": c["own"]["layout"], "closing_row_chonwon": c["own"]},
                   "later_comparative": {"file": c["next_file"], "page": c["next_page"], "layout": c["next"]["layout"], "closing_row_chonwon": c["next"], "equals_own": c["same"]},
                   "asset_side_eok": extra.get("asset_side_eok"),
                   "note": ("closing row 「기말 보험계약부채」 of the issued-contract LRC/LIC note, 천원; item 14 = total - LIC (the 2023 layout has a 4th column 「보험취득현금흐름자산」 that sits on the LRC side, "
                            "as in the DART engine); latest-filing rule: the 전분기 table of the FY2024 filing of the same quarter"
                            + ("; THIS quarter is RESTATED in that table (보험계약의 경계를 만기까지로 변경, 소급 적용; FY2024_Q3 경영공시 p3) -> see data/_derived/ilp_restated_comparative.json" if restated else ""))}
            if restated:
                rec["original_basis_value"] = extra["original_basis"]
                side_cells.append({"company_code": "KR0074", "quarter": c["quarter"], "basis": "latest_filing_comparative_restatable",
                                   "restatement_reason": "FY2024_Q3 경영공시 p3·p8: 「회사는 보험계약의 경계를 만기까지로 변경하고 기업회계기준서 제1117호의 최초 적용시점부터 소급 적용하였습니다. 따라서 비교 표시된 전년 동기 금액도 재작성 되었습니다」"
                                                       " (the FY2024_Q1/Q2 filings still print the 2023 comparatives on the old basis)",
                                   "item8_restated": None, "item8_minus_original_net_lrc": None, "restated_bs_insurance_contract_liability_eok": items[15],
                                   "restated_bs_source": "derived: closing total of the restated <전분기> LRC/LIC table of the FY2024_Q3 경영공시 (no balance sheet for 2023-09-30 is printed there)",
                                   "bs_item20_fy2023_original_eok": extra["original_basis"]["bs20_original_eok"], "bs_item20_original_eok": extra["original_basis"]["bs20_original_eok"],
                                   "bs_source_file": c["use_file"], "items_10_15_restated": {str(n): items[n] for n in sorted(items)},
                                   "items_10_15_original": {"10": extra["original_basis"]["lic_eok"], "13": extra["original_basis"]["lic_eok"], "14": extra["original_basis"]["lrc_eok"], "15": extra["original_basis"]["total_eok"]}})
        else:
            cur = c["cur_won"]
            checks = {"r_lic1": "pass" if b is not None else "pass_filing_anchor", "bs20_eok": None if b is None else lic.eok(b), "ratio_bs20": extra.get("ratio_bs20"),
                      "filing_bs_eok": eok_won(cur["total"]), "ratio_filing_bs": 1.0, "r_lic3_gap_eok": round(items[10] + items[14] - items[15], 4), "tag_tables": 0, "tag_cells": 0, "tag_mismatch": 0,
                      "bs20_master_disagrees": False}
            rec = {"company_code": "KR0100", "quarter": c["quarter"], "item_block": "lic_pdf_bs", "source_id": "PDF", "as_of_date": lic.as_of_date(c["quarter"]), "source_file": c["file"], "page": c["page"],
                   "scope": "separate", "period": "current", "class": "A1", "bel_ra_source": "RF", "basis": "liability", "row_basis": ["LIAB"], "unit": "원", "unit_source": "cue", "tables": [],
                   "dropped_tables": [], "dedupe": [], "flags": ["pdf_source_no_dart_filing", "general_account_basis"] + ([] if b is not None else ["bs20_master_absent_filing_anchor_used"]), "checks": checks,
                   "net_lrc_eok": None, "items_eok": {str(n): items[n] for n in sorted(items)},
                   "evidence": f"업무보고서식 재무상태표 1. 보험계약부채 {cur['total']:,.0f} = 가. 잔여보장요소 {cur['LRC']:,.0f} + 나. 발생사고요소 {cur['LIC']:,.0f} (1) 최선추정 {cur['BEL']:,.0f} (2) 위험조정 {cur['RA']:,.0f} (원)",
                   "prior_year_end_column_eok": extra["prior_year_end_eok"],
                   "note": "업무보고서식 재무상태표 「1. 보험계약부채 / 가. 잔여보장요소 / 나. 발생사고요소 / (1) 최선추정 (2) 위험조정」 (원), general-account basis like the 2025.1Q-3Q cells of stage 3: items 14 and 15 do not contain the "
                           "special-account 변액 liabilities that the DART year-end cells (2023.4Q, 2024.4Q, 2025.4Q) contain; the incurred-claims component (items 10-13) is the same on both bases "
                           "(prior-year-end LIC of the 2024 filings 222.82억 vs DART 2023.4Q item 10 222.83억)"}
        recs.append(rec)
    prov["cells"] = prov["cells"] + recs
    prov["backfills"] = prov.get("backfills", []) + [{"stage": "lic-stage3b-pdf", "at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"), "emitted_by": "scripts/load_ilp_lic_stage3b_pdf.py", "ticket": TICKET,
                                                      "added_cells": [f"{c['code']} {c['quarter']}" for c, *_ in acc], "master_backup": backup.name,
                                                      "note": f"items 10-15 of {len(recs)} pre-2025 cells of Lina (3) and Chubb (6) from the 경영공시 PDFs"}]
    out = _dump_prov(prov)
    tmp = PROV.with_name(PROV.name + ".tmp")
    tmp.write_bytes(out.encode("utf-8"))
    os.replace(tmp, PROV)
    # ---------------- sidecar (restated Lina 2023.3Q) ----------------
    if side_cells:
        s0 = SIDE.read_bytes().decode("utf-8")
        sj = json.loads(s0)
        if json.dumps(sj, ensure_ascii=False, indent=1) + ("\n" if s0.endswith("\n") else "") != s0:
            raise SystemExit("abort: sidecar does not round-trip")
        sback = lic.BACKUP_DIR / f"ilp_restated_comparative_backup_{stamp}_pre_lic_stage3b.json"
        shutil.copyfile(SIDE, sback)
        have_s = {(x["company_code"], x["quarter"]) for x in sj["cells"]}
        for sc in side_cells:
            if (sc["company_code"], sc["quarter"]) in have_s:
                raise SystemExit("abort: sidecar cell exists")
            sj["cells"].append(sc)
        sj["extended_at"] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
        sj["extended_by"] = list(sj.get("extended_by", [])) + ["scripts/load_ilp_lic_stage3b_pdf.py"]
        tmp = SIDE.with_name(SIDE.name + ".tmp")
        tmp.write_bytes((json.dumps(sj, ensure_ascii=False, indent=1) + ("\n" if s0.endswith("\n") else "")).encode("utf-8"))
        os.replace(tmp, SIDE)
    print(f"appended {len(new_rows)} rows; master backup {backup.name}; provenance backup {pback.name}; {len(recs)} provenance cells; sidecar cells {len(side_cells)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
