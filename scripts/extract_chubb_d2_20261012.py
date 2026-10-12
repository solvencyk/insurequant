# -*- coding: utf-8 -*-
"""Stage the Chubb (KR0100) definition fix: IFRS17_BS item 20 and ILP items 14/15 of the mid-quarters on the K-IFRS basis (special account included).

Ticket : inbox/parser/20261012T1020Z__orchestrator__MULTI_2023.4Q-2026.2Q__ifrs17_owner_followups_20261012.md item 4 (owner decision (7)).
Problem: Chubb's 경영공시 balance sheet (업무보고서 서식, until FY2025_Q3) prints the insurance contract liability of the GENERAL account (`1. 보험계약부채`,
         D1) and the special-account liability of the variable products as a separate block (`IV. 특별계정부채`, SA).  The year-end cells of the masters (DART /
         audit report, K-IFRS line) and the 2026 filings (K-IFRS 서식: `Ⅰ. 보험계약부채`) include the variable products; the six mid-quarter BS cells and nine ILP
         cells carry D1 only, so item 20 sits 2,400~2,900억 below the 2-4 table total (portfolio validator R3 RED x5) and the series jumps at every year end.
Fix    : D2 = D1 + SA (both printed in the same balance sheet).  BS item 20 := D2 (6 cells with a BS value);  ILP item 15 := D2 and item 14 := LRC(general) + SA
         (9 cells); the incurred-claims items 10~13 do not change (the special account carries no LIC: general-account LIC == DART year-end LIC at both
         year ends, 222.82 vs 222.83 and 250.05 vs 250.05).  K-IFRS line vs D2 at the two year ends: -0.110 % and -0.074 %.

This script is READ-ONLY on the masters.  It re-reads the PDFs (exact digit tokens of D1 / SA / LRC / LIC, the label printed on the line of each token,
the 부채총계 identity and the 2-2 summary) and writes the specs:
  data/_derived/ifrs17_owner_followups_20261012/chubb_d2_spec_bs.json    (cells for scripts/apply_ifrs17_bs_fix_20261012.py)
  data/_derived/ifrs17_owner_followups_20261012/chubb_d2_spec_ilp.json   (cells for scripts/apply_chubb_ilp_d2_20261012.py)
  data/_derived/ifrs17_owner_followups_20261012/chubb_d2_evidence.json

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_chubb_d2_20261012.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "_derived" / "ifrs17_owner_followups_20261012"
DISC = ROOT / "data" / "disclosure"
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

CODE = "KR0100"
PDF = {
    "2023.1Q": "FY2023_Q1/raw/KR0100_처브라이프생명보험.pdf",
    "2023.2Q": "FY2023_Q2/raw/KR0100_처브라이프생명보험.pdf",
    "2023.3Q": "FY2023_Q3/raw/KR0100_처브라이프생명보험.pdf",
    "2024.1Q": "FY2024_Q1/raw/KR0100_처브라이프생명보험_amended.pdf",
    "2024.2Q": "FY2024_Q2/raw/KR0100_처브라이프생명보험.pdf",
    "2024.3Q": "FY2024_Q3/raw/KR0100_처브라이프생명보험_amended.pdf",
    "2025.1Q": "FY2025_Q1/raw/KR0100_처브라이프생명보험.pdf",
    "2025.2Q": "FY2025_Q2/raw/KR0100_처브라이프생명보험.pdf",
    "2025.3Q": "FY2025_Q3/raw/KR0100_처브라이프생명보험.pdf",
}
# the BS lane's compilation (kr0100_item20_table.json) is only the list of numbers to look for; every one is re-found in the PDF below
TABLE = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "kr0100_item20_table.json"
NUM_RE = re.compile(r"\d{1,3}(?:,\d{3}){2,}")


def fmt(won: int) -> str:
    return f"{int(won):,}"


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def line_label(page: "fitz.Page", token: str) -> str | None:
    """the label printed on the same visual line, to the left of the token (words within 3pt of the token's vertical centre)"""
    words = page.get_text("words")
    hit = [w for w in words if w[4] == token]
    if not hit:
        return None
    labels = []
    for w in hit:
        yc = (w[1] + w[3]) / 2
        same = [x for x in words if abs((x[1] + x[3]) / 2 - yc) <= 3.0 and x[2] <= w[0] + 0.5 and x[4] != token and not NUM_RE.fullmatch(x[4])]
        same.sort(key=lambda x: x[0])
        # keep the contiguous label words that sit right before the number (stop at a big gap)
        grp = []
        for x in reversed(same):
            if grp and grp[-1][0] - x[2] > 40:
                break
            grp.append(x)
        labels.append(" ".join(x[4] for x in reversed(grp)))
    return " | ".join(labels)


def main() -> int:
    tab = {r["quarter"]: r for r in json.loads(TABLE.read_bytes().decode("utf-8"))}
    # idempotent: the "old" values are the PRE-APPLY bytes (the backups the appliers wrote) once the masters have been changed
    bk = ROOT / "data" / "_derived" / "ifrs17_owner_followups_backup_20261012"
    bs_src = bk / "chubb_d2" / "IFRS17_BS.json"
    ilp_src = bk / "insurance_liability_portfolio.json.pre_chubb_d2"
    bs = json.loads((bs_src if bs_src.exists() else ROOT / "IFRS17_BS.json").read_bytes().decode("utf-8"))
    bs_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    ilp = json.loads((ilp_src if ilp_src.exists() else ROOT / "insurance_liability_portfolio.json").read_bytes().decode("utf-8"))
    ilp_idx = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in ilp}

    evidence, bs_cells, ilp_cells, problems = {}, [], [], []
    for q, rel in PDF.items():
        p = DISC / rel
        t = tab[q]
        d1 = round(t["D1"] * 1e6)
        sa = round(t["SA"] * 1e6)
        doc = fitz.open(p)
        texts = {i: pg.get_text("text") for i, pg in enumerate(doc, 1)}
        d1_pages = [i for i, tx in texts.items() if fmt(d1) in tx]
        sa_pages = [i for i, tx in texts.items() if fmt(sa) in tx]
        if not d1_pages or not sa_pages:
            problems.append(f"{q}: D1 token {fmt(d1)} pages {d1_pages} / SA token {fmt(sa)} pages {sa_pages}")
            continue
        # labels printed on the lines of the two tokens
        d1_label = line_label(doc[d1_pages[0] - 1], fmt(d1))
        sa_label = line_label(doc[sa_pages[0] - 1], fmt(sa))
        # LRC / LIC of the general account: tokens a (가.잔여보장요소) and b (나.발생사고요소) with a + b == D1 exactly, matching the ILP cell (items 14 / 10)
        old14, old10, old15 = ilp_idx[(CODE, q, 14)], ilp_idx[(CODE, q, 10)], ilp_idx[(CODE, q, 15)]
        toks = set()
        for pg in set(d1_pages):
            for p2 in (pg - 1, pg, pg + 1):
                if 1 <= p2 <= len(doc):
                    toks |= {int(m.group(0).replace(",", "")) for m in NUM_RE.finditer(texts[p2])}
        # the printed components may differ from the printed total by 1 won (2023.2Q: 815,725,033,962 + 20,751,613,057 = 836,476,647,019 vs 836,476,647,018)
        pairs = [(a, b) for a in toks for b in toks
                 if abs(a + b - d1) <= 2 and abs(a / 1e8 - old14) <= 0.006 and abs(b / 1e8 - old10) <= 0.006]
        if len(pairs) != 1:
            problems.append(f"{q}: LRC/LIC token pairs for D1 {fmt(d1)} = {pairs}")
            continue
        lrc, lic = pairs[0]
        # ILP side
        if abs(round(d1 / 1e8, 2) - old15) > 0.006:
            problems.append(f"{q}: ILP item 15 {old15} != round(D1/1e8,2) {round(d1 / 1e8, 2)}")
        new15 = round((d1 + sa) / 1e8, 2)
        new14 = round((lrc + sa) / 1e8, 2)
        if abs(old10 + new14 - new15) > 0.0301:
            problems.append(f"{q}: R-LIC3 would fail: {old10} + {new14} != {new15}")
        ilp_cells.append(dict(quarter=q, item14=dict(old=old14, new=new14), item15=dict(old=old15, new=new15),
                              D1_won=d1, SA_won=sa, LRC_won=lrc, LIC_won=lic, source_file="data/disclosure/" + rel, pages=dict(D1=d1_pages, SA=sa_pages)))
        # BS side (only the six quarters that have a BS item 20)
        old20 = bs_idx.get((CODE, 20, q))
        new20 = round((d1 + sa) / 1e6, 6)
        if old20 is not None:
            if abs(old20 - d1 / 1e6) > 1e-6:
                problems.append(f"{q}: BS item 20 {old20} != D1 {d1 / 1e6}")
            # 2023.1Q lives in KR0100_agent_gran.json (other_agent class; sorted AFTER KR0100_agent_followup.json in merge_bs_disclosure_parts.py, so it must be updated
            # where it is held); the other five keys are held only by the engine part KR0100.json -> the default part KR0100_agent_followup.json (other_agent class)
            # outranks the engine part and an engine re-run cannot bring the general-account value back
            cell = dict(
                key=f"{CODE}|20|{q}", action="replace", old=old20, new=new20, pdf="data/disclosure/" + rel, page=d1_pages[0], pdf_sha256=sha_file(p),
                method="d2_general_account_plus_special_account", scale="원 -> 백만원",
                basis=(f"owner 2026-10-12 결정 ⑦ 정의 통일: 정기경영공시 {q} 재무상태표(8-1) PDF p{d1_pages[0]} 1.보험계약부채(일반계정) {fmt(d1)}원 + "
                       f"PDF p{sa_pages[0]} IV.특별계정부채 {fmt(sa)}원 = {fmt(d1 + sa)}원. 연말 DART·감사보고서 셀과 2026 K-IFRS 서식의 「보험계약부채」는 특별계정 변액 "
                       f"보험계약부채를 포함하므로 같은 정의(특별계정 포함)로 맞췄다. 정정 전 값 {old20:,.6f}백만원은 일반계정 1.보험계약부채만이다."))
            if q == "2023.1Q":
                cell["part_file"] = "KR0100_agent_gran.json"
            bs_cells.append(cell)
        evidence[q] = dict(pdf="data/disclosure/" + rel, pdf_sha256=sha_file(p), D1_won=d1, SA_won=sa, D2_won=d1 + sa, LRC_won=lrc, LIC_won=lic, lrc_plus_lic_minus_d1_won=lrc + lic - d1,
                           D1_pages=d1_pages, SA_pages=sa_pages, D1_line_label=d1_label, SA_line_label=sa_label,
                           bs_item20_old=old20, bs_item20_new=new20 if old20 is not None else None, ilp_old=dict(i10=old10, i14=old14, i15=old15),
                           ilp_new=dict(i14=new14, i15=new15))
        print(f"{q}: D1 {fmt(d1)} (p{d1_pages}, label '{d1_label}')  SA {fmt(sa)} (p{sa_pages}, label '{sa_label}')  LRC {fmt(lrc)} + LIC {fmt(lic)} - D1 = {lrc + lic - d1} won  "
              f"BS20 {old20} -> {new20 if old20 is not None else '(no BS cell)'}  ILP14 {old14} -> {new14}  ILP15 {old15} -> {new15}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "chubb_d2_spec_bs.json").write_text(json.dumps({"cells": bs_cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (OUT / "chubb_d2_spec_ilp.json").write_text(json.dumps({"cells": ilp_cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (OUT / "chubb_d2_evidence.json").write_text(json.dumps({"quarters": evidence, "problems": problems}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"bs cells {len(bs_cells)}, ilp cells {len(ilp_cells)}, problems {len(problems)}")
    for pr in problems:
        print("   PROBLEM:", pr)
    return 3 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
