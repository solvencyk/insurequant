# -*- coding: utf-8 -*-
"""KR1102 (스위스리아시아) 2026.1Q items 1-8 of insurance_liability_portfolio.json := the SUM OF ALL ROWS of the two 경영공시 2-4 tables.

Ticket : inbox/parser/20261012T1450Z__orchestrator__KR1102_2026.1Q__ilp_total_derived_load.md  (owner decision 2026-10-12, chat: "2는 계산값 넣으면 안 되나?")
Why    : the printed 합계 rows of BOTH sections of the FY2026_Q1 2-4 table (PDF p9) leave out the Indirect-Par portfolio (life (2,664) 313 197, non-life (2,801) 411 487),
         so the printed totals are not the issuer's book total (the same issuer's 2025.4Q / 2026.2Q totals include the Indirect-Par rows).  The cell was withheld
         (provenance `lrc_model_not_loaded`) and the portfolio gate flags R2_CENSUS.  The owner chose to load the computed total of every printed row instead of
         registering an exemption.
What   : eight master cells (items 1-8) of (KR1102, 2026.1Q): item 1/2/3 = sum over the 3 life + 5 non-life rows of the 일반모형 최선추정부채 / 위험조정 / 보험계약마진,
         items 4-7 = 0.0 (every 변동수수료접근법 / 보험료배분접근법 cell of every row prints '-'), item 8 = sum(items 1..7).  Item 9 (2-5) is NOT loaded: this filing
         has no 2-5 section, the same as the other KR1102 interim quarters (R4 stays a YELLOW there).
         Provenance sidecar: one `lrc_model_cells` entry (how=derived_sum_of_rows + note), the `lrc_model_not_loaded` record gets a `resolved` marker, one `backfills` record.
Reads  : PDF p9 (rows) and p6 (2-2 narrative, corroboration only) of data/disclosure/FY2026_Q1/raw/KR1102_스위스리아시아.pdf through PyMuPDF (text layer).  The table was also
         read by eye on a 150 dpi render (img/kr1102_2026q1_p9.png); the numbers below are checked against that reading (EXPECTED) and the script aborts on any difference.
Guards : both files must round-trip byte-exactly (master: indent 2 + CRLF, no trailing newline; sidecar: detected), the new keys must not exist, backup first, atomic replace
         (retry while a gate holds the file), re-read, row-by-row / entry-by-entry proof that nothing else moved, manifest for an exact --revert.  The live write is built by the very
         same function as the dry-run candidate and is refused when the baseline bytes moved after the dry run (the gates then ran on a different file).

  default            dry run: re-read the PDF, run every internal check, write plan + evidence + the candidate files (WORK/sim) -- the live files are not touched
                     (only possible BEFORE the load: afterwards the keys exist and the dry run aborts)
  --apply            write the live files
  --check            read-only, any time: re-read the PDF and compare the loaded eight cells and the sidecar entry with the all-row sums
  --revert --apply   take the eight cells and the three sidecar edits out again

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_kr1102_derived_20261012.py [--apply] [--check] [--revert]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data" / "_derived" / "ilp_kr1102_derived_load_20261012"
SIM = WORK / "sim"
BACKUP = ROOT / "data" / "_derived" / "ilp_kr1102_derived_load_backup_20261012"
MASTER = ROOT / "insurance_liability_portfolio.json"
PROV = ROOT / "insurance_liability_portfolio_provenance.json"
CSMW = ROOT / "CSM_waterfall.json"
PDF_REL = "data/disclosure/FY2026_Q1/raw/KR1102_스위스리아시아.pdf"
CODE, Q = "KR1102", "2026.1Q"
TICKET = "inbox/parser/20261012T1450Z__orchestrator__KR1102_2026.1Q__ilp_total_derived_load.md"
EMITTER = "scripts/load_ilp_kr1102_derived_20261012.py"
HOW = "derived_sum_of_rows"
NOTE = "인쇄 합계는 Indirect-Par 행 제외, 전체 행 합으로 적재(owner 2026-10-12)"
sys.stdout.reconfigure(encoding="utf-8")

# the table as read by eye on the 150 dpi render of PDF p9 (억원; negative = remaining-coverage asset); (BEL, RA, CSM) of the 일반모형 columns, all other columns '-'
EXPECTED = {
    "life": {"rows": [("무배당사망", "Non-Par", (-297, 19, 30)), ("무배당건강", "Non-Par", (-2367, 294, 166)), ("무배당사망", "Indirect-Par", (-4842, 50, 1207))],
             "printed_total": (-2664, 313, 197)},
    "nonlife": {"rows": [("무배당상해", "Non-Par", (-78, 5, 41)), ("무배당질병", "Non-Par", (-1979, 238, 194)), ("무배당질병", "Indirect-Par", (-1914, 20, 310)),
                         ("일반", "Non-Par", (-751, 165, 252)), ("자동차", "Non-Par", (7, 3, 0))],
                "printed_total": (-2801, 411, 487)},
}
NUM = r"\(?[\d,]+\)?"
ROW_RE = re.compile(rf"(무배당사망|무배당건강|무배당상해|무배당질병|일반|자동차|합계)\s+({NUM})\s+({NUM})\s+({NUM})\s+-\s+-\s+-\s+-\s*$")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def num(tok: str) -> int:
    t = tok.strip()
    v = int(t.strip("()").replace(",", ""))
    return -v if t.startswith("(") and t.endswith(")") else v


def dump_master(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


def detect_prov(raw: bytes, obj):
    """the sidecar's exact serialisation (indent 1 or 2, LF or CRLF, trailing newline or not)"""
    for indent in (1, 2):
        for nl in ("\n", "\r\n"):
            for tail in (b"", nl.encode()):
                if json.dumps(obj, ensure_ascii=False, indent=indent).replace("\n", nl).encode("utf-8") + tail == raw:
                    return indent, nl, tail
    raise SystemExit("ABORT: the provenance sidecar does not round-trip byte-exactly with indent 1/2, LF/CRLF")


def dump_prov(obj, fmt) -> bytes:
    indent, nl, tail = fmt
    return json.dumps(obj, ensure_ascii=False, indent=indent).replace("\n", nl).encode("utf-8") + tail


def replace_retry(tmp: Path, path: Path, tries: int = 40, wait: float = 3.0) -> None:
    """os.replace fails with WinError 5 while another process (a gate run) has the target open: wait and retry, never half-write"""
    for _ in range(tries):
        try:
            tmp.replace(path)
            return
        except PermissionError:
            time.sleep(wait)
    raise SystemExit(f"ABORT: could not replace {path.name} after {tries} tries (file locked) -- {tmp.name} is left for inspection")


# --------------------------------------------------------------------------------------------------------------------------------------------------
# PDF reading
# --------------------------------------------------------------------------------------------------------------------------------------------------
def read_pdf() -> dict:
    import fitz  # PyMuPDF (in the project venv)
    doc = fitz.open(str(ROOT / PDF_REL))
    p9 = doc[8].get_text("text", sort=True)
    p6 = doc[5].get_text("text", sort=True)
    lines = p9.splitlines()
    if not any("2-4)" in l and "회계모형별" in l for l in lines):
        raise SystemExit("ABORT: PDF p9 is not the 2-4 table")
    if not re.search(r"<\s*2026\s*년\s*1\s*분기\s*>", p9):
        raise SystemExit("ABORT: PDF p9 is not the <2026년 1분기> table")
    i_life = next(i for i, l in enumerate(lines) if "[생명보험]" in l)
    i_non = next(i for i, l in enumerate(lines) if "[손해보험]" in l)
    sections = {}
    for name, seg in (("life", lines[i_life + 1:i_non]), ("nonlife", lines[i_non + 1:])):
        rows, total, pending = [], None, False
        for l in seg:
            if "Indirect" in l:
                pending = True
            m = ROW_RE.search(l)
            if not m:
                continue
            vec = (num(m.group(2)), num(m.group(3)), num(m.group(4)))
            if m.group(1) == "합계":
                total = vec
            else:
                rows.append((m.group(1), "Indirect-Par" if pending else "Non-Par", vec))
                pending = False
        sections[name] = {"rows": rows, "printed_total": total}
    for name in ("life", "nonlife"):
        got, exp = sections[name], EXPECTED[name]
        if got["rows"] != exp["rows"] or got["printed_total"] != exp["printed_total"]:
            raise SystemExit(f"ABORT: text layer of PDF p9 [{name}] differs from the by-eye reading:\n  text layer {got}\n  by eye     {exp}")
    flat = re.sub(r"\s+", " ", p6)
    m1 = re.search(r"보험계약마진은 ([\d,]+) 억원 중 (\d+)%인 ([\d,]+) 억원이 상각", flat)
    m2 = re.search(r"잔여위험조정 ([\d,]+) 억원 중 (\d+)%인 ([\d,]+) 억원이 상각", flat)
    m3 = re.search(r"최선추정부채 △ ([\d,]+) 억원, 위험조정 ([\d,]+) 억, 보험계약마진 ([\d,]+) 억원", flat)
    if not (m1 and m2 and m3):
        raise SystemExit("ABORT: the 2-2 narrative sentences on PDF p6 were not found")
    narrative = {
        "csm_before_release": num(m1.group(1)), "csm_release_pct": num(m1.group(2)), "csm_release": num(m1.group(3)),
        "ra": num(m2.group(1)), "ra_release_pct": num(m2.group(2)), "ra_release": num(m2.group(3)),
        "life_longterm_bel_negated": num(m3.group(1)), "life_longterm_ra": num(m3.group(2)), "life_longterm_csm": num(m3.group(3)),
    }
    return {"sections": sections, "narrative": narrative}


def derive(read: dict) -> dict:
    """sums over every printed row, footing against the printed totals, and the corroboration against the 2-2 narrative"""
    sec = read["sections"]
    all_rows = sec["life"]["rows"] + sec["nonlife"]["rows"]

    def s(rows):
        return tuple(sum(r[2][k] for r in rows) for k in range(3))

    life_sum, non_sum, tot = s(sec["life"]["rows"]), s(sec["nonlife"]["rows"]), s(all_rows)
    non_indirect = [r for r in all_rows if r[1] != "Indirect-Par"]
    printed_sum = tuple(sec["life"]["printed_total"][k] + sec["nonlife"]["printed_total"][k] for k in range(3))
    footing = {}
    for name in ("life", "nonlife"):
        rows_ex = [r for r in sec[name]["rows"] if r[1] != "Indirect-Par"]
        footing[name] = {"rows_excluding_indirect": s(rows_ex), "printed_total": sec[name]["printed_total"],
                         "diff": tuple(s(rows_ex)[k] - sec[name]["printed_total"][k] for k in range(3))}
        if any(abs(d) > 1 for d in footing[name]["diff"]):
            raise SystemExit(f"ABORT: printed total of [{name}] is not the sum of its non-Indirect rows within 1 (rounding): {footing[name]}")
    items = {1: tot[0], 2: tot[1], 3: tot[2], 4: 0, 5: 0, 6: 0, 7: 0}
    items[8] = sum(items[i] for i in range(1, 8))
    nar = read["narrative"]
    life_long = s(sec["life"]["rows"] + [r for r in sec["nonlife"]["rows"] if r[0] in ("무배당상해", "무배당질병")])
    corro = {
        "csm_after_release_narrative": nar["csm_before_release"] - nar["csm_release"], "csm_item3_plus_item6": items[3] + items[6],
        "ra_narrative": nar["ra"], "ra_item2_plus_item5": items[2] + items[5],
        "life_longterm_csm_narrative": nar["life_longterm_csm"], "life_longterm_csm_row_sum": life_long[2],
        "life_longterm_csm_if_printed_life_total_used": sec["life"]["printed_total"][2] + sum(
            r[2][2] for r in sec["life"]["rows"] if r[1] == "Indirect-Par") + sum(r[2][2] for r in sec["nonlife"]["rows"] if r[0] in ("무배당상해", "무배당질병")),
        "life_longterm_ra_row_sum_lrc_only": life_long[1], "life_longterm_ra_narrative": nar["life_longterm_ra"],
        "life_longterm_bel_row_sum_lrc_only": life_long[0], "life_longterm_bel_narrative": -nar["life_longterm_bel_negated"],
    }
    if corro["csm_after_release_narrative"] != corro["csm_item3_plus_item6"]:
        raise SystemExit(f"ABORT: 2-2 narrative CSM 2,353 - 153 does not equal the row-sum CSM: {corro}")
    if corro["ra_narrative"] != corro["ra_item2_plus_item5"]:
        raise SystemExit(f"ABORT: 2-2 narrative RA does not equal the row-sum RA: {corro}")
    if corro["life_longterm_csm_narrative"] != corro["life_longterm_csm_row_sum"]:
        raise SystemExit(f"ABORT: 2-2 narrative life+long-term CSM does not equal the row sum: {corro}")
    return {"life_sum": life_sum, "nonlife_sum": non_sum, "total": tot, "printed_totals_sum": printed_sum, "footing": footing, "items": items,
            "corroboration": corro, "non_indirect_sum": s(non_indirect)}


# --------------------------------------------------------------------------------------------------------------------------------------------------
# candidate files
# --------------------------------------------------------------------------------------------------------------------------------------------------
def build(raw_m: bytes, raw_p: bytes, read: dict, d: dict, stamp: str) -> dict:
    rows = json.loads(raw_m.decode("utf-8"))
    if dump_master(rows) != raw_m:
        raise SystemExit("ABORT: insurance_liability_portfolio.json does not round-trip (indent 2, CRLF, no trailing newline)")
    prov = json.loads(raw_p.decode("utf-8"))
    fmt = detect_prov(raw_p, prov)
    have = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in rows}
    clash = [n for n in range(1, 10) if (CODE, Q, n) in have]
    if clash:
        raise SystemExit(f"ABORT: master already holds {CODE} {Q} items {clash}")
    if any(c["company_code"] == CODE and c["quarter"] == Q for c in prov["lrc_model_cells"]):
        raise SystemExit("ABORT: lrc_model_cells already holds KR1102 2026.1Q")
    nl = [e for e in prov["lrc_model_not_loaded"] if e["company_code"] == CODE and e["quarter"] == Q]
    if len(nl) != 1 or "resolved" in nl[0]:
        raise SystemExit(f"ABORT: expected exactly one unresolved lrc_model_not_loaded record for KR1102 2026.1Q, found {nl}")
    printed = nl[0]["detail"]["readings"][0]["vec_eok"]
    if [printed["1"], printed["2"], printed["3"]] != [float(x) for x in d["printed_totals_sum"]]:
        raise SystemExit(f"ABORT: the withheld printed-total vector in the sidecar {printed} differs from this reading {d['printed_totals_sum']}")
    cat = {r["항목번호"]: r for r in rows if r["원보험사코드"] == CODE and r["공시분기"] == "2026.2Q" and 1 <= r["항목번호"] <= 8}
    if sorted(cat) != list(range(1, 9)):
        raise SystemExit("ABORT: cannot take the item catalogue from KR1102 2026.2Q")
    new_rows = []
    for n in range(1, 9):
        c = cat[n]
        new_rows.append({"원보험사코드": CODE, "원수사명": c["원수사명"], "티커": c["티커"], "생손보여부": c["생손보여부"], "항목번호": n, "항목명": c["항목명"],
                         "섹션": c["섹션"], "레벨": c["레벨"], "공시분기": Q, "값": float(d["items"][n])})
    new_master = dump_master(rows + new_rows)

    sec = read["sections"]

    def vec_of(t3):
        return {"1": float(t3[0]), "2": float(t3[1]), "3": float(t3[2]), "4": 0.0, "5": 0.0, "6": 0.0, "7": 0.0}

    def section(name):
        r = sec[name]
        return {"page": 9, "run": [float(x) for x in r["printed_total"]] + [0.0, 0.0, 0.0, 0.0], "vec": vec_of(d["life_sum"] if name == "life" else d["nonlife_sum"]),
                "footing": "printed_total_excludes_indirect_par",
                "rows": [{"portfolio": p, "kind": k, "bel_ra_csm": list(v)} for p, k, v in r["rows"]],
                "printed_total_bel_ra_csm": list(r["printed_total"]), "rows_excluding_indirect_bel_ra_csm": list(d["footing"][name]["rows_excluding_indirect"]),
                "printed_total_minus_rows_excluding_indirect": list(d["footing"][name]["diff"]),
                "row_sum_bel_ra_csm": list(d["life_sum"] if name == "life" else d["nonlife_sum"])}

    c = d["corroboration"]
    entry = {
        "company_code": CODE, "quarter": Q, "item_block": "lrc_model_table_2-4", "source_id": "PDF", "as_of_date": "2026-03-31", "source_file": PDF_REL, "page": 9,
        "table": None, "table_label": "<2026년 1분기>", "table_year": 2026, "table_year_src": "label", "unit_in_source": "억원", "printed_run": None,
        "run_kind": "two_sections_row_sum", "text_source": "pymupdf",
        "items_eok": {str(n): float(d["items"][n]) for n in range(1, 9)}, "item9": None, "item9_evidence": None,
        "flags": [HOW, "printed_total_excludes_indirect_par", "sum_of_life_and_nonlife_sections"],
        "evidence": ("PDF p9 2-4 <2026년 1분기> (단위 억원): 생명 3행 (Non-Par 무배당사망 (297)·19·30 / 무배당건강 (2,367)·294·166 / Indirect-Par 무배당사망 (4,842)·50·1,207) + 손해 5행 "
                     "(Non-Par 무배당상해 (78)·5·41 / 무배당질병 (1,979)·238·194 / Indirect-Par 무배당질병 (1,914)·20·310 / 일반 (751)·165·252 / 자동차 7·3·0) 의 일반모형 열을 전 행 합산: "
                     f"최선추정부채 {d['items'][1]:,} · 위험조정 {d['items'][2]:,} · 보험계약마진 {d['items'][3]:,} (변동수수료접근법·보험료배분접근법은 전 행 '-' = 0). "
                     "인쇄 합계 행은 두 절 모두 Indirect-Par 행을 뺀 값이다(생명 (2,664)·313·197, 손해 (2,801)·411·487; 합 (5,465)·724·684). "
                     f"p6 2-2 서술 대조: 보험계약마진 2,353억 중 153억 상각 → 2,353 - 153 = {c['csm_after_release_narrative']:,} = 항목 3+6; 잔여위험조정 794억 = 항목 2+5; "
                     f"생명 및 장기 보험계약마진 1,948억 = 생명 전 행 + 장기손해 3행(Indirect 포함) 합."),
        "how": HOW, "note": NOTE,
        "owner_decision": {"at": "2026-10-12", "channel": "chat", "quote": "2는 계산값 넣으면 안 되나?", "ticket": TICKET,
                           "instead_of": "R2_CENSUS exemption registration (DOCUMENTED_EXCEPTIONS)"},
        "published_in": "FY2026_Q1 경영공시 2-4", "basis": "own_filing",
        "basis_note": ("basis=own_filing keeps scripts/build_master_xlsx.py::_ilp_lrc_label working (label '해당 분기 공시'); the derivation is carried by how/flags/note -- the xlsx 비고 column "
                       "does not know `how` yet (publishing)"),
        "alternatives": [
            {"role": "own", "fy": "FY2026_Q1", "page": 9, "label": "<2026년 1분기>", "unit": "억원", "vec_eok": vec_of(d["printed_totals_sum"]),
             "footing": "printed_total_excludes_indirect_par", "footing_exception": None, "usable": False, "used": False,
             "reason_not_used": "the printed 합계 rows of both sections omit the Indirect-Par portfolio (owner 2026-10-12: load the sum of all rows instead)"},
            {"role": "own_row_sum", "fy": "FY2026_Q1", "page": 9, "label": "<2026년 1분기>", "unit": "억원", "vec_eok": vec_of(d["total"]),
             "footing": "ok", "footing_exception": None, "usable": True, "used": True}],
        "sections": {"life": section("life"), "nonlife": section("nonlife")},
        "corroboration_p6_2_2_narrative": {
            "page": 6, "csm_before_release_eok": read["narrative"]["csm_before_release"], "csm_release_eok": read["narrative"]["csm_release"],
            "csm_after_release_eok": c["csm_after_release_narrative"], "equals_item3_plus_item6": c["csm_after_release_narrative"] == c["csm_item3_plus_item6"],
            "ra_eok": c["ra_narrative"], "equals_item2_plus_item5": c["ra_narrative"] == c["ra_item2_plus_item5"],
            "life_and_longterm_csm_eok": c["life_longterm_csm_narrative"], "life_plus_longterm_nonlife_rows_csm_row_sum": c["life_longterm_csm_row_sum"],
            "equals_row_sum": c["life_longterm_csm_narrative"] == c["life_longterm_csm_row_sum"],
            "same_total_built_from_printed_life_total_instead_of_rows": c["life_longterm_csm_if_printed_life_total_used"],
            "not_used_as_anchor": {"life_and_longterm_bel_eok": c["life_longterm_bel_narrative"], "table_lrc_bel_row_sum": c["life_longterm_bel_row_sum_lrc_only"],
                                   "life_and_longterm_ra_eok": c["life_longterm_ra_narrative"], "table_lrc_ra_row_sum": c["life_longterm_ra_row_sum_lrc_only"],
                                   "why": "the narrative BEL/RA of 생명 및 장기 do not equal the LRC-only 2-4 row sums (RA 635 vs 626, BEL -6,550 vs -11,477); the scope difference was not investigated, so they are not used as anchors -- only the CSM and the all-business RA tie exactly"}},
        "previously_withheld_reason": nl[0]["reason"],
        "ticket": TICKET, "at": stamp, "emitted_by": EMITTER,
    }
    prov2 = json.loads(json.dumps(prov))
    prov2["lrc_model_cells"].append(entry)
    for e in prov2["lrc_model_not_loaded"]:
        if e["company_code"] == CODE and e["quarter"] == Q:
            e["resolved"] = {"at": stamp, "how": "loaded as the sum of all rows (owner decision 2026-10-12); " + NOTE, "see": f"lrc_model_cells[how={HOW}]", "emitted_by": EMITTER}
    prov2["backfills"].append({"stage": "kr1102_2026.1Q_derived_sum_20261012", "at": stamp, "emitted_by": EMITTER, "ticket": TICKET,
                               "note": "KR1102 2026.1Q items 1-8 := sum of all rows of the 2-4 tables (the printed totals omit the Indirect-Par rows); how=" + HOW})
    return {"rows": rows, "prov": prov, "fmt": fmt, "new_rows": new_rows, "new_master": new_master, "prov2": prov2, "new_prov": dump_prov(prov2, fmt), "entry": entry}


# --------------------------------------------------------------------------------------------------------------------------------------------------
# evidence
# --------------------------------------------------------------------------------------------------------------------------------------------------
def neighbours(rows: list) -> dict:
    out = {}
    for q in ("2025.3Q", "2025.4Q", "2026.2Q"):
        out[q] = {r["항목번호"]: r["값"] for r in rows if r["원보험사코드"] == CODE and r["공시분기"] == q and 1 <= r["항목번호"] <= 8}
    wf = json.loads(CSMW.read_text(encoding="utf-8"))
    out["csm_waterfall_2025.4Q_closing"] = next(r["값"] for r in wf if r["원보험사코드"] == CODE and r["공시분기"] == "2025.4Q" and r["항목번호"] == 6)
    return out


def write_evidence(read: dict, d: dict, b: dict, plan: dict) -> None:
    sec, it = read["sections"], d["items"]
    nb = plan["neighbours"]
    L = []
    L.append("# KR1102 스위스리아시아 2026.1Q ILP 항목 1~8 — 전체 행 합 적재 증빙 (parser-ifrs17, 2026-10-12, 티켓 20261012T1450Z)\n")
    L.append(f"재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_kr1102_derived_20261012.py --check` (적재 후 언제든: PDF 를 다시 읽어 적재된 8칸과 사이드카 항목을 전체 행 합과 대조). 이 표는 적재 전 dry run(인자 없음)이 만들었다. 원문 `{PDF_REL}` 9쪽(인쇄 -9-), 렌더링 `img/kr1102_2026q1_p9.png`.\n")
    L.append("## 1. 원문 행 (단위 억원, 일반모형 열; 변동수수료접근법·보험료배분접근법 열은 전 행 `-`)\n")
    L.append("| 절 | 포트폴리오 | 구분 | 최선추정부채 | 위험조정 | 보험계약마진 |\n|---|---|---|---:|---:|---:|")
    for name, label in (("life", "생명"), ("nonlife", "손해")):
        for p, k, v in sec[name]["rows"]:
            L.append(f"| {label} | {p} | {k} | {v[0]:,} | {v[1]:,} | {v[2]:,} |")
        pt = sec[name]["printed_total"]
        L.append(f"| {label} | **인쇄 합계** | (Indirect-Par 제외) | {pt[0]:,} | {pt[1]:,} | {pt[2]:,} |")
    L.append("")
    L.append("## 2. 합 항등식 확인표\n")
    ind = tuple(sum(r[2][k] for n in ("life", "nonlife") for r in sec[n]["rows"] if r[1] == "Indirect-Par") for k in range(3))
    L.append("| 항목 | 생명 행 합 | 손해 행 합 | 전체 행 합(적재값) | 그중 Indirect-Par 2행 | 인쇄 합계 합(적재 안 함) | 전체 행 합 - 인쇄 합계 합 |\n|---|---:|---:|---:|---:|---:|---:|")
    for k, nm in enumerate(("1 일반모형_최선추정부채", "2 일반모형_위험조정", "3 일반모형_보험계약마진")):
        L.append(f"| {nm} | {d['life_sum'][k]:,} | {d['nonlife_sum'][k]:,} | **{d['total'][k]:,}** | {ind[k]:,} | {d['printed_totals_sum'][k]:,} | {d['total'][k] - d['printed_totals_sum'][k]:,} |")
    L.append(f"| 4~7 변동수수료접근법 3열 · 보험료배분접근법 | 0 | 0 | **0** | 0 | 0 | 0 |")
    L.append(f"| 8 보험부채_합계 = 1+…+7 | | | **{it[8]:,}** (= {it[1]:,} + {it[2]:,} + {it[3]:,}) | | {sum(d['printed_totals_sum']):,} | {it[8] - sum(d['printed_totals_sum']):,} |")
    L.append("")
    L.append("인쇄 합계가 Indirect-Par 행을 뺀 것의 증명(행 합 대 인쇄 합계, 억원): "
             + "; ".join(f"{('생명' if n == 'life' else '손해')} 비-Indirect 행 합 {tuple(d['footing'][n]['rows_excluding_indirect'])} 대 인쇄 {tuple(d['footing'][n]['printed_total'])} (차 {tuple(d['footing'][n]['diff'])})" for n in ('life', 'nonlife'))
             + ". 생명 보험계약마진 인쇄 197 은 행 30 + 166 = 196 과 1 어긋난다(원문 반올림) — 그래서 항목 3 의 「전체 행 합 - 인쇄 합계 합」 1,516 은 Indirect-Par 2행 합 1,517 보다 1 작다. "
               "적재는 인쇄된 각 칸을 한 번씩만 더한 행 합이다.\n")
    L.append("## 3. 전(공란) → 후 — 적재한 8칸 (원보험사코드 KR1102 · 공시분기 2026.1Q, 키 = 원보험사코드·공시분기·항목번호)\n")
    L.append("| 항목번호 | 항목명 | 전 | 후 |\n|---:|---|---|---:|")
    for r in b["new_rows"]:
        L.append(f"| {r['항목번호']} | {r['항목명']} | (행 없음, R2_CENSUS RED) | {r['값']:,.1f} |")
    L.append("\n항목 9(2-5 해지율 예외모형 사용여부)는 적재하지 않는다 — 이 공시 PDF 는 24쪽 전부 텍스트층 쪽(이미지 0)이고 2-4(9~10쪽) 다음 쪽(11쪽)이 바로 Ⅲ. 자산의 건전성이라 2-5 절이 없다(`해지율`·`무저해지` 0쪽). KR1102 의 다른 중간분기(2025.1Q~3Q·2026.2Q)와 같은 상태이고 R4 YELLOW 로 남는다(RED 아님).\n")
    L.append("## 4. 같은 공시 안의 독립 대조 (PDF 6쪽 2-2 서술)\n")
    c = d["corroboration"]
    n = read["narrative"]
    L.append(f"- 「보험계약마진은 {n['csm_before_release']:,}억원 중 {n['csm_release_pct']}%인 {n['csm_release']:,}억원이 상각」 → {n['csm_before_release']:,} - {n['csm_release']:,} = **{c['csm_after_release_narrative']:,}** = 항목 3 + 6 = {c['csm_item3_plus_item6']:,} (일치)")
    L.append(f"- 「잔여위험조정 {n['ra']:,}억원」 = 항목 2 + 5 = {c['ra_item2_plus_item5']:,} (일치; 인쇄 합계 합 {d['printed_totals_sum'][1]:,} 이 아니다)")
    L.append(f"- 「생명 및 장기 … 보험계약마진 {n['life_longterm_csm']:,}억원」 = 생명 3행 + 장기손해 3행(무배당상해·무배당질병·Indirect 무배당질병) 행 합 {c['life_longterm_csm_row_sum']:,} (일치; "
             f"인쇄 생명 합계 197 로 만들면 {c['life_longterm_csm_if_printed_life_total_used']:,} 로 1 어긋나 서술은 행 단위 합과 맞는다)")
    L.append(f"- 쓰지 않은 서술: 「최선추정부채 △{n['life_longterm_bel_negated']:,}」·「위험조정 {n['life_longterm_ra']}」 는 2-4 표의 생명+장기 행 합(BEL {c['life_longterm_bel_row_sum_lrc_only']:,} · RA {c['life_longterm_ra_row_sum_lrc_only']:,})과 같지 않다. 범위 차이는 조사하지 않았고 앵커로도 안 쓴다(CSM 과 전 업종 RA 794 만 정확히 맞는다).\n")
    L.append("## 5. 이웃 분기와 계열 정합 (같은 발행사, 억원)\n")
    L.append("| 분기 | 일반모형 BEL | RA | CSM | 항목 8 |\n|---|---:|---:|---:|---:|")
    for q in ("2025.3Q", "2025.4Q"):
        v = nb[q]
        L.append(f"| {q} | {v[1]:,.0f} | {v[2]:,.0f} | {v[3]:,.0f} | {v[8]:,.0f} |")
    L.append(f"| **2026.1Q (이번, 전체 행 합)** | **{it[1]:,}** | **{it[2]:,}** | **{it[3]:,}** | **{it[8]:,}** |")
    v = nb["2026.2Q"]
    L.append(f"| 2026.2Q | {v[1]:,.0f} | {v[2]:,.0f} | {v[3]:,.0f} | {v[8]:,.0f} |")
    pr = d["printed_totals_sum"]
    L.append(f"\n인쇄 합계 합(적재 안 함)이었다면 BEL {pr[0]:,}(이웃 {nb['2025.4Q'][1]:,.0f}·{nb['2026.2Q'][1]:,.0f} 의 약 절반) · CSM {pr[2]:,}(이웃 {nb['2025.4Q'][3]:,.0f}·{nb['2026.2Q'][3]:,.0f} 의 약 3분의 1)에서 끊기고 RA {pr[1]:,} 만 이웃({nb['2025.4Q'][2]:,.0f}·{nb['2026.2Q'][2]:,.0f})과 비슷하다. CSM 워터폴 2025.4Q 기말 CSM = {nb['csm_waterfall_2025.4Q_closing']:,.2f} 대 항목 3 의 2025.4Q {nb['2025.4Q'][3]:,.0f}(같은 개념, Indirect-Par 포함).\n")
    L.append(f"## 6. 게이트·사이드카\n\n- 사이드카 `insurance_liability_portfolio_provenance.json`: `lrc_model_cells` +1(`how={HOW}`, `basis=own_filing`, 비고 「{NOTE}」), `lrc_model_not_loaded`(KR1102 2026.1Q)에 `resolved` 표식, `backfills` +1. `basis` 는 새 값을 만들지 않았다 — `scripts/build_master_xlsx.py::_ilp_lrc_label` 이 모르는 `basis` 에서 KeyError 를 내므로(publishing 이 xlsx 비고 열에 「계산값」 표기를 달 때 `how` 를 읽으면 된다).\n- 게이트 전후 비교는 `gate_before_*.txt` / `gate_after_*.txt`(같은 코드, 후 = 후보 파일을 읽히는 덮개 `gate_overlay.py`, 저장소 쓰기 차단).\n")
    (WORK / "evidence.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    plan_path, manifest_path = WORK / "plan.json", WORK / "manifest.json"
    raw_m, raw_p = MASTER.read_bytes(), PROV.read_bytes()

    if a.check:
        d = derive(read_pdf())
        live = {r["항목번호"]: r["값"] for r in json.loads(raw_m.decode("utf-8")) if r["원보험사코드"] == CODE and r["공시분기"] == Q}
        ent = [c for c in json.loads(raw_p.decode("utf-8"))["lrc_model_cells"] if c["company_code"] == CODE and c["quarter"] == Q]
        ok = (sorted(live) == list(range(1, 9)) and all(live[n] == float(d["items"][n]) for n in range(1, 9)) and len(ent) == 1 and ent[0].get("how") == HOW
              and all(ent[0]["items_eok"][str(n)] == float(d["items"][n]) for n in range(1, 9)))
        print(f"CHECK {'OK' if ok else 'MISMATCH'}: master {live} | PDF row sums {d['items']} | sidecar entries {len(ent)}")
        return 0 if ok else 1

    if a.revert:
        if not manifest_path.exists():
            raise SystemExit("ABORT: no manifest -- nothing to revert")
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = json.loads(raw_m.decode("utf-8"))
        if dump_master(rows) != raw_m:
            raise SystemExit("ABORT: master does not round-trip")
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        want = {(CODE, Q, c["item"]): c["after"] for c in plan["cells"]}
        keep, gone = [], []
        for r in rows:
            k = (r["원보험사코드"], r["공시분기"], r["항목번호"])
            (gone if k in want else keep).append(r)
        if len(gone) != 8 or any(r["값"] != want[(r["원보험사코드"], r["공시분기"], r["항목번호"])] for r in gone):
            raise SystemExit("ABORT: the eight cells are not (any longer) exactly the loaded ones")
        prov = json.loads(raw_p.decode("utf-8"))
        fmt = detect_prov(raw_p, prov)
        prov["lrc_model_cells"] = [c for c in prov["lrc_model_cells"] if not (c["company_code"] == CODE and c["quarter"] == Q and c.get("emitted_by") == EMITTER)]
        for e in prov["lrc_model_not_loaded"]:
            if e["company_code"] == CODE and e["quarter"] == Q and e.get("resolved", {}).get("emitted_by") == EMITTER:
                e.pop("resolved")
        prov["backfills"] = [r for r in prov["backfills"] if r.get("emitted_by") != EMITTER]
        new_m, new_p = dump_master(keep), dump_prov(prov, fmt)
        print(f"revert: master {len(rows)} -> {len(keep)} rows; sidecar sha {sha(raw_p)[:12]} -> {sha(new_p)[:12]}; master sha {sha(raw_m)[:12]} -> {sha(new_m)[:12]}"
              f" (pre-load backup: master {man['baseline']['master_sha256'][:12]}, sidecar {man['baseline']['prov_sha256'][:12]})")
        if not a.apply:
            print("(dry run -- nothing written; add --apply)")
            return 0
        for path, data in ((MASTER, new_m), (PROV, new_p)):
            tmp = path.with_suffix(".json.tmp_kr1102")
            tmp.write_bytes(data)
            replace_retry(tmp, path)
        manifest_path.rename(manifest_path.with_name("manifest.reverted.json"))
        print("reverted")
        return 0

    read = read_pdf()
    d = derive(read)
    stamp = json.loads(plan_path.read_text(encoding="utf-8"))["stamp"] if plan_path.exists() else time.strftime("%Y%m%dT%H%MZ", time.gmtime())
    b = build(raw_m, raw_p, read, d, stamp)
    plan = {
        "stamp": stamp, "ticket": TICKET, "company": CODE, "quarter": Q, "how": HOW, "note": NOTE,
        "cells": [{"item": r["항목번호"], "항목명": r["항목명"], "before": None, "after": r["값"]} for r in b["new_rows"]],
        "rows_read": {n: {"rows": [{"portfolio": p, "kind": k, "bel_ra_csm": list(v)} for p, k, v in read["sections"][n]["rows"]],
                          "printed_total": list(read["sections"][n]["printed_total"])} for n in ("life", "nonlife")},
        "derived": {"life_sum": d["life_sum"], "nonlife_sum": d["nonlife_sum"], "total": d["total"], "printed_totals_sum": d["printed_totals_sum"], "footing": d["footing"],
                    "corroboration": d["corroboration"]},
        "neighbours": neighbours(b["rows"]),
        "baseline": {"master_sha256": sha(raw_m), "master_rows": len(b["rows"]), "prov_sha256": sha(raw_p)},
        "candidate": {"master_sha256": sha(b["new_master"]), "master_rows": len(b["rows"]) + 8, "prov_sha256": sha(b["new_prov"])},
    }
    for c in plan["cells"]:
        print(f"  item {c['item']} {c['항목명']}: {c['before']} -> {c['after']:,.1f}")
    print(f"life rows sum {d['life_sum']}  non-life rows sum {d['nonlife_sum']}  total {d['total']}  printed totals only {d['printed_totals_sum']}")
    print(f"corroboration (2-2 narrative p6): {d['corroboration']}")

    if not a.apply:
        SIM.mkdir(parents=True, exist_ok=True)
        (SIM / MASTER.name).write_bytes(b["new_master"])
        (SIM / PROV.name).write_bytes(b["new_prov"])
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        write_evidence(read, d, b, plan)
        print(f"dry run: candidates in {SIM.relative_to(ROOT)} (master {len(b['rows']) + 8} rows); plan.json + evidence.md written; live files untouched")
        return 0

    # ---- apply
    if not plan_path.exists():
        raise SystemExit("ABORT: run the dry run (and the gates on its candidates) first")
    old = json.loads(plan_path.read_text(encoding="utf-8"))
    if old["baseline"]["master_sha256"] != sha(raw_m) or old["baseline"]["prov_sha256"] != sha(raw_p):
        raise SystemExit("ABORT: a live file changed after the dry run -- the gates ran on a different baseline; re-run the dry run and the gates")
    if old["candidate"]["master_sha256"] != sha(b["new_master"]) or old["candidate"]["prov_sha256"] != sha(b["new_prov"]):
        raise SystemExit("ABORT: the bytes to be written differ from the simulated candidates")
    if manifest_path.exists():
        raise SystemExit("ABORT: manifest.json exists -- already applied (use --revert first)")
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MASTER, BACKUP / (MASTER.name + ".pre_kr1102_derived"))
    shutil.copyfile(PROV, BACKUP / (PROV.name + ".pre_kr1102_derived"))
    if sha((BACKUP / (MASTER.name + ".pre_kr1102_derived")).read_bytes()) != sha(raw_m) or sha((BACKUP / (PROV.name + ".pre_kr1102_derived")).read_bytes()) != sha(raw_p):
        raise SystemExit("ABORT: backup does not match the source")
    if MASTER.read_bytes() != raw_m or PROV.read_bytes() != raw_p:
        raise SystemExit("ABORT: a live file changed while the write was prepared -- nothing written")
    for path, data in ((PROV, b["new_prov"]), (MASTER, b["new_master"])):       # sidecar first, so a cell never exists without its provenance
        tmp = path.with_suffix(".json.tmp_kr1102")
        tmp.write_bytes(data)
        replace_retry(tmp, path)

    # ---- proof
    raw_m2, raw_p2 = MASTER.read_bytes(), PROV.read_bytes()
    rows2 = json.loads(raw_m2.decode("utf-8"))
    prov2 = json.loads(raw_p2.decode("utf-8"))
    assert dump_master(rows2) == raw_m2 and dump_prov(prov2, b["fmt"]) == raw_p2, "written files do not round-trip"
    assert rows2[:len(b["rows"])] == b["rows"] and rows2[len(b["rows"]):] == b["new_rows"], "master: existing rows moved or new rows differ"
    for k in b["prov"]:
        if k in ("lrc_model_cells", "backfills", "lrc_model_not_loaded"):
            continue
        assert b["prov"][k] == prov2[k], f"sidecar section {k} changed"
    assert prov2["lrc_model_cells"][:-1] == b["prov"]["lrc_model_cells"] and prov2["lrc_model_cells"][-1] == b["entry"], "sidecar lrc_model_cells"
    assert prov2["backfills"][:-1] == b["prov"]["backfills"], "sidecar backfills"
    assert len(prov2["lrc_model_not_loaded"]) == len(b["prov"]["lrc_model_not_loaded"])
    n_resolved = 0
    for x, y in zip(b["prov"]["lrc_model_not_loaded"], prov2["lrc_model_not_loaded"]):
        if x == y:
            continue
        assert x["company_code"] == CODE and x["quarter"] == Q and {k: v for k, v in y.items() if k != "resolved"} == x, "an unrelated not_loaded record changed"
        n_resolved += 1
    assert n_resolved == 1
    manifest = {"stamp": stamp, "emitted_by": EMITTER, "baseline": plan["baseline"], "candidate": plan["candidate"],
                "written": {"master_sha256": sha(raw_m2), "prov_sha256": sha(raw_p2)}, "backups": [str(BACKUP / (MASTER.name + ".pre_kr1102_derived")), str(BACKUP / (PROV.name + ".pre_kr1102_derived"))]}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"written: master {len(b['rows'])} -> {len(rows2)} rows (+8, existing rows byte-identical), sidecar lrc_model_cells +1, backfills +1, 1 not_loaded record resolved; "
          f"sha256 master {sha(raw_m)[:12]} -> {sha(raw_m2)[:12]}, sidecar {sha(raw_p)[:12]} -> {sha(raw_p2)[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
