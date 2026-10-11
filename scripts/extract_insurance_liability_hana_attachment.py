# -*- coding: utf-8 -*-
"""
Reader for the 하나손해보험(KR0050) 별첨 재무제표 PDFs (downloader ticket 20261011T0830Z, `data/disclosure/FY*/attachments/`).

Why it exists: Hana Non-life's quarterly 경영공시 PDF leaves the financial statements to an attachment (「Ⅷ. 재무제표 사항은 첨부 파일 참조」), and the
company is not a DART quarterly filer, so items 10-15 of insurance_liability_portfolio.json (발생사고요소·잔여보장요소·보험계약부채 합계, DART 부채 기준) could only be
loaded for the three year-ends.  The attachments carry the full 별도 재무제표 and notes, so every quarter can be read the way the DART 주석 of the listed companies is read.

What is read (units 천원 in the PDFs; the master is 억원 = 100,000 천원):
  note 18 「보험계약자산 및 보험계약부채」: the movement tables of the ISSUED contracts (원수 + 수재; 출재 tables are skipped by their heading)
      * 일반모형 (GMM)  closing row 「(2) 기말/분기말/반기말 보험계약부채」  [잔여보장(손실요소 제외), 손실요소, 발생사고부채(단일열), 합계]          -> items 13 (+14)
      * 보험료배분접근법 (PAA, 일반 and 자동차, one table each or one combined table)  [손실요소 제외, 손실요소, 발생사고 BEL, 발생사고 RA, 합계]    -> items 11, 12 (+14)
      * 2026 filings split the GMM table into ① 배당요소가 있는 / ② 없는 보험계약: the closing rows of the sections are added up.
  the separate 재무상태표 line 「보험계약부채」 (원) = anchor of R-LIC1 for the filing itself.
Same definitions as the DART cells of the 23 listed companies and the three Hana year-end cells (class A2):
  14 잔여보장요소_합계 = sum of the liability closing rows (손실요소 제외 + 손실요소) · 10 발생사고요소_합계 = sum of the LIC columns · 11 / 12 = PAA BEL / RA · 13 = GMM single-column LIC
  15 보험계약부채_합계 = sum of the liability closing totals (= the 재무상태표 보험계약부채).

Pure reading: no master is written here (the loader is scripts/load_ilp_hana_attachments.py).  Python: venv full path, UTF-8, no BOM.
"""
from __future__ import annotations

import glob
import hashlib
import json
import re
from pathlib import Path

import pdfplumber

REPO = Path(__file__).resolve().parents[1]
CODE = "KR0050"
QUARTERS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q",
            "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"]
FY_OF = {q: f"FY{q[:4]}_Q{q[5]}" for q in QUARTERS}
QEND = {"1Q": "03-31", "2Q": "06-30", "3Q": "09-30", "4Q": "12-31"}

# ------------------------------------------------------------------------------------------------------------------------------
# text helpers
# ------------------------------------------------------------------------------------------------------------------------------
NUM_TOK = re.compile(r"\(?-?\d[\d,]*(?:\.\d+)?\)?|(?<=\s)-(?=\s|$)")
PERIOD_RE = re.compile(r"^-\s*(당분기|당반기|당기|전분기|전반기|전기)\s*$")
CLOSE_LIAB = re.compile(r"^\((?P<n>\d)\)\s*(?:분기말|반기말|기말)\s*(?P<kind>재보험계약부채|보험계약부채|재보험계약자산|보험계약자산)\s+(?P<rest>.*)$")
NET_ROW = re.compile(r"^(?:분기말|반기말|기말)\s*(?P<kind>재보험계약순부채\(자산\)|보험계약순부채\(자산\)|재보험계약순자산\(부채\)|재보험계약순자산)\s+(?P<rest>.*)$")
NET8 = re.compile(r"^8\.\s*(?:분기말|반기말|기말)\s*보험계약자산\s*및\s*부채\s+(?P<rest>.*)$")
NET9 = re.compile(r"^9\.\s*(?:분기말|반기말|기말)\s*보험계약순부채\(자산\)\s+(?P<rest>.*)$")
SEC_RE = re.compile(r"^([①②③④⑤⑥⑦⑧⑨⑩])\s*(.*)$")
LOB_RE = re.compile(r"^(\d)\)\s*(일반|자동차|장기)\s*$")
BS_LIAB = re.compile(r"^\d+\.\s*보험계약부채\s+(?:[\d,]+\s+)?(?P<cur>\d{1,3}(?:,\d{3}){3,})\s+(?P<prev>\d{1,3}(?:,\d{3}){3,})")
BS_DATE = re.compile(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*현재")
HEAD_FIRST = re.compile(r"^\(\d+\)\s*(?:당(?:분|반)?기와\s*전(?:분|반)?기\s*중|(?:당사|회사)의\s*보험료배분접근법모형을\s*적용하는)")


def to_num(tok: str) -> float:
    tok = tok.strip()
    if tok == "-":
        return 0.0
    neg = tok.startswith("(") and tok.endswith(")")
    v = float(tok.strip("()").replace(",", ""))
    return -v if neg else v


def numbers(rest: str) -> list:
    return [to_num(t) for t in NUM_TOK.findall(" " + rest)]


def flat(s: str) -> str:
    return re.sub(r"\s+", "", s)


def classify_heading(w: str):
    """w = whitespace-free text of a 3-line window that starts at a '(N) ' line.  -> dict or None"""
    head = w[:130]
    if not re.search(r"(잔여보장|측정요소|변동내역|차이조정)", head) or not re.search(r"(적용한|적용하는)", head):
        return None
    what = "MEAS" if "측정요소" in head else ("LRCLIC" if "잔여보장" in head else "OTHER")
    cut = head.find("다음과")
    scope = head[:cut] if cut > 0 else head
    if "보험료배분접근법" in scope:
        model = "PAA"
    elif "변동수수료" in scope:
        model = "VFA"
    elif "일반모형" in scope:
        model = "GMM"
    else:
        model = "?"
    lob = "일반" if re.search(r"(?<![장기])일반보험계약", scope) else ("자동차" if "자동차보험계약" in scope else None)
    return {"what": what, "reins": "출재" in scope, "model": model, "lob": lob, "text": w[:100]}


def read_pdf(path) -> dict:
    """all closing rows of the movement tables + the 재무상태표 보험계약부채 line(s) of one attachment"""
    out = {"file": str(path), "tables": [], "headings": [], "bs_liab": [], "bs_dates": []}
    lines = []
    with pdfplumber.open(str(path)) as pdf:
        for i, pg in enumerate(pdf.pages):
            for ln in (pg.extract_text() or "").split("\n"):
                s = ln.strip()
                if s:
                    lines.append((i + 1, s))
    state = {"model": None, "reins": False, "what": None, "lob": None, "period": None, "section": None}

    def add(pg, row, n, rest, s):
        out["tables"].append({"page": pg, "what": state["what"], "model": state["model"], "lob": state["lob"], "reins": state["reins"], "period": state["period"],
                              "section": state["section"], "row": row, "n": n, "nums": numbers(rest), "line": s[:170]})

    for k, (pg, s) in enumerate(lines):
        if HEAD_FIRST.match(s):
            h = classify_heading(flat("".join(x[1] for x in lines[k:k + 3])))
            if h:
                state = {"model": h["model"], "reins": h["reins"], "what": h["what"], "lob": h["lob"], "period": None, "section": None}
                out["headings"].append({"page": pg, **h})
                continue
        ml = LOB_RE.match(s)
        if ml and state["what"] in ("LRCLIC", "MEAS"):
            state["lob"], state["period"] = ml.group(2), None
            continue
        mbs = BS_LIAB.match(s)
        if mbs:
            out["bs_liab"].append({"page": pg, "line": s[:150], "cur_won": float(mbs.group("cur").replace(",", "")), "prev_won": float(mbs.group("prev").replace(",", ""))})
            continue
        md = BS_DATE.search(s)
        if md and len(out["bs_dates"]) < 6 and re.match(r"^제\s*\d+\s*(?:\(\w+\))?\s*기", s):
            out["bs_dates"].append({"page": pg, "line": s[:100], "date": f"{md.group(1)}-{int(md.group(2)):02d}-{int(md.group(3)):02d}"})
        mp = PERIOD_RE.match(s)
        if mp:
            state["period"] = "cur" if mp.group(1).startswith("당") else "prior"
            state["section"] = None
            continue
        ms = SEC_RE.match(s)
        if ms:
            state["section"] = ms.group(1) + " " + ms.group(2)[:40]
        if state["what"] not in ("LRCLIC", "MEAS"):
            continue
        mc = CLOSE_LIAB.match(s)
        if mc:
            add(pg, mc.group("kind"), mc.group("n"), mc.group("rest"), s)
            continue
        for rx, n in ((NET8, "8"), (NET9, "9")):
            m = rx.match(s)
            if m:
                add(pg, "NET:보험계약순부채(자산)", n, m.group("rest"), s)
                break
        else:
            mn = NET_ROW.match(s)
            if mn:
                add(pg, "NET:" + mn.group("kind"), "", mn.group("rest"), s)
    return out


# ------------------------------------------------------------------------------------------------------------------------------
# aggregation
# ------------------------------------------------------------------------------------------------------------------------------
def aggregate(tabs: list, period: str) -> dict:
    """closing rows of the ISSUED-contract tables of one period ('cur' | 'prior') -> sums in 천원"""
    A = {"lrc": 0.0, "lic": 0.0, "bel": 0.0, "ra": 0.0, "single": 0.0, "total": 0.0, "foot_gap": 0.0, "n_tables": 0, "tables": [], "problems": [],
         "asset_lrc": 0.0, "asset_lic": 0.0, "asset_total": 0.0, "net_lrc": 0.0, "net_total": 0.0, "meas_net_csm": 0.0, "meas_net_total": 0.0, "meas_tables": 0}
    for t in tabs:
        if t["reins"] or t["period"] != period:
            continue
        nums = t["nums"]
        if t["what"] == "MEAS":
            if t["row"].startswith("NET:") and len(nums) == 6 and t["model"] == "GMM" and any(nums):
                A["meas_net_csm"] += nums[2] + nums[3] + nums[4]
                A["meas_net_total"] += nums[5]
                A["meas_tables"] += 1
            continue
        if t["what"] != "LRCLIC":
            continue
        if t["row"] == "보험계약부채":
            if len(nums) == 4:                       # [ex-loss LRC, loss component, LIC, total]
                ex, loss, lic, tot = nums
                bel = ra = 0.0
                kind = "GMM4"
                A["single"] += lic
            elif len(nums) == 5:                     # [ex-loss LRC, loss component, LIC BEL, LIC RA, total]
                ex, loss, bel, ra, tot = nums
                lic = bel + ra
                kind = "PAA5"
            else:
                A["problems"].append({"page": t["page"], "problem": f"unexpected column count {len(nums)}", "nums": nums})
                continue
            A["lrc"] += ex + loss
            A["lic"] += lic
            A["bel"] += bel
            A["ra"] += ra
            A["total"] += tot
            A["foot_gap"] += (ex + loss + lic) - tot
            A["n_tables"] += 1
            A["tables"].append({"page": t["page"], "kind": kind, "model": t["model"], "lob": t["lob"], "section": t["section"], "nums": nums})
        elif t["row"] == "보험계약자산" and len(nums) in (4, 5):
            A["asset_lrc"] += nums[0] + nums[1]
            A["asset_lic"] += sum(nums[2:-1])
            A["asset_total"] += nums[-1]
        elif t["row"].startswith("NET:보험계약순부채") and t["what"] == "LRCLIC" and len(nums) in (4, 5):
            A["net_lrc"] += nums[0] + nums[1]
            A["net_total"] += nums[-1]
    return A


def eok(x_chonwon: float) -> float:
    """천원 -> 억원 (1억 = 100,000 천원), two decimals, never -0.0"""
    return round(x_chonwon / 1e5, 2) + 0.0


# ------------------------------------------------------------------------------------------------------------------------------
# files
# ------------------------------------------------------------------------------------------------------------------------------
def attachment_path(quarter: str, scope: str = "separate") -> Path:
    q4 = quarter.endswith("4Q")
    kind = {("separate", False): "separate_fs", ("separate", True): "audit_separate", ("consol", False): "consol_fs", ("consol", True): "audit_consol"}[(scope, q4)]
    g = glob.glob(str(REPO / "data" / "disclosure" / FY_OF[quarter] / "attachments" / f"{CODE}_*_attachment_{kind}.pdf"))
    if len(g) != 1:
        raise FileNotFoundError(f"{quarter} {kind}: {g}")
    return Path(g[0])


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def as_of(quarter: str) -> str:
    return f"{quarter[:4]}-{QEND[quarter[5:]]}"


def read_quarter(quarter: str) -> dict:
    """everything the loader needs for one quarter: cur / prior aggregates, the filing's own 재무상태표 line, the period check"""
    p = attachment_path(quarter)
    r = read_pdf(p)
    bs = r["bs_liab"][0] if r["bs_liab"] else None
    dates = [d["date"] for d in r["bs_dates"]]
    return {"quarter": quarter, "file": str(p.relative_to(REPO)).replace("\\", "/"), "sha256": sha256(p), "headings": r["headings"],
            "cur": aggregate(r["tables"], "cur"), "prior": aggregate(r["tables"], "prior"), "bs_liab": bs, "bs_liab_all": r["bs_liab"][:4], "bs_dates": r["bs_dates"],
            "period_ok": (as_of(quarter) in dates[:1]) if dates else None}


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    qs = sys.argv[1:] or QUARTERS
    out = {}
    for q in qs:
        rec = read_quarter(q)
        c = rec["cur"]
        print(f"{q}: tables {c['n_tables']}  LRC {eok(c['lrc']):,.2f}  LIC {eok(c['lic']):,.2f} (BEL {eok(c['bel']):,.2f} RA {eok(c['ra']):,.2f} single {eok(c['single']):,.2f})  total {eok(c['total']):,.2f}"
              f"  BS {None if not rec['bs_liab'] else round(rec['bs_liab']['cur_won'] / 1e8, 4)}  period_ok {rec['period_ok']}")
        out[q] = rec
    print(json.dumps({q: {"file": v["file"], "n_cur": v["cur"]["n_tables"]} for q, v in out.items()}, ensure_ascii=False))
