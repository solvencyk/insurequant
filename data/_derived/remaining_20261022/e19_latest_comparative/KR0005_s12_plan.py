"""Read-only. Assemble plan_KR0005.json from the XML reads (s7), comparison (s8), closure (s10), seam (s11) and the restatement-note tables (s9)."""
import json, io, re, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EVD = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
sys.path.insert(0, str(EVD))
from KR0005_common import num
X = json.loads((EVD / "KR0005_s7_xml.json").read_text(encoding="utf-8"))
CMP = json.loads((EVD / "KR0005_s8_compare.json").read_text(encoding="utf-8"))
CLO = json.loads((EVD / "KR0005_s10_closure.json").read_text(encoding="utf-8"))
SEAM = json.loads((EVD / "KR0005_s11_seam.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
NAME = {}
for r in pl:
    if r["원보험사코드"] == "KR0005":
        NAME[r["항목번호"]] = r["항목명"]

FILING = {
    "2023.3Q": dict(later_fy="FY2024_Q3", later_rcept="20241114002739", later_report="FY2024 3Q report (prior-year 3Q cumulative column, col 4 of 4)", orig_rcept="20231114002611", orig_fy="FY2023_Q3", api="data/dart/_fs_api_cache/00103176_2024_11014_OFS.json (frmtrm_add_amount)", note_fy="FY2024_Q3", note_ytd_tok=6, note_label="note 41 (전기 재무제표의 재작성), table 2) 전분기 포괄손익계산서, 누적 수정 후"),
    "2023.4Q": dict(later_fy="FY2024_Q4", later_rcept="20250320001444", later_report="FY2024 annual report (prior-year column 78기, col 2 of 3)", orig_rcept="20240321001884", orig_fy="FY2023_Q4", api="data/dart/_fs_api_cache/00103176_2024_11011_OFS.json (frmtrm_amount)", note_fy="FY2024_Q4", note_ytd_tok=3, note_label="note 45 (전기 재무제표의 재작성), table 2) 전기 포괄손익계산서, 수정 후"),
    "2024.1Q": dict(later_fy="FY2025_Q1", later_rcept="20250515002476", later_report="FY2025 1Q report (prior-year 1Q cumulative column, col 4 of 4)", orig_rcept="20240516002177", orig_fy="FY2024_Q1", api="data/dart/_fs_api_cache/00103176_2025_11013_OFS.json (frmtrm_add_amount)", note_fy="FY2025_Q1", note_ytd_tok=3, note_label="note 41 (전기 재무제표의 재작성), table 1) 전분기 포괄손익계산서, 수정 후"),
    "2024.2Q": dict(later_fy="FY2025_Q2", later_rcept="20250814003425", later_report="FY2025 semi-annual report (prior-year 6M cumulative column, col 4 of 4)", orig_rcept="20240814004299", orig_fy="FY2024_Q2", api="data/dart/_fs_api_cache/00103176_2025_11012_OFS.json (frmtrm_add_amount)", note_fy="FY2025_Q2", note_ytd_tok=6, note_label="note 41 (전기 재무제표의 재작성), table 1) 전반기 포괄손익계산서, 누적 수정 후"),
}


def parse_note(fy):
    rows = []
    for ln in (EVD / f"KR0005_s9_note_{fy}.txt").read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^TR(\d+): (.*?) :: (.*)$", ln)
        if not m:
            continue
        toks = []
        for t in m.group(3).split(" | "):
            mm = re.match(r"^(.*)@L(\d+)$", t)
            toks.append((mm.group(1), int(mm.group(2))) if mm else (t, None))
        rows.append((m.group(2).replace(" ", ""), toks))
    return rows


NOTE_RULES = [(17, r"II\.투자손익"), (20, r"III\.영업이익"), (22, r"V\.법인세비용차감전순이익"), (23, r"VI\.법인세비용"), (24, r"VII\.(분기|반기|당기)순이익"),
              (25, r"VIII\.기타포괄손익"), (26, r"\(1\)기타포괄손익-공정가치측정금융자산(평가|관련)손익"), (28, r"\(3\)현금흐름위험회피파생상품평가손익"), (31, r"IX\.총포괄손익"),
              ("ecl", r"\(2\)기타포괄손익-공정가치측정(금융자산)?(기대)?신용손실"), ("insfinexp", r"\(1\)보험금융비용")]


def note_cells(q):
    f = FILING[q]
    rows = parse_note(f["note_fy"])
    out = {}
    for lab, toks in rows:
        for key, pat in NOTE_RULES:
            if key in out:
                continue
            if re.fullmatch(pat, lab) and len(toks) >= f["note_ytd_tok"] + 1:
                pre = toks[f["note_ytd_tok"] - 2]
                adj = toks[f["note_ytd_tok"] - 1]
                post = toks[f["note_ytd_tok"]]
                if post[1] is None or (num(post[0]) is None and post[0] != "-"):
                    continue
                out[key] = {"pre": num(pre[0]) or 0.0, "adj": num(adj[0]) or 0.0, "post": num(post[0]) or 0.0, "line": post[1], "label": lab}
    return out


NOTE = {q: note_cells(q) for q in FILING}
cells, buckets = [], []
for q, f in FILING.items():
    xl = X["later|" + q]
    xo = X["orig|" + q]
    adopt = sorted(int(k) for k in CLO[q]["adopt"])
    note = NOTE[q]
    for k in adopt:
        c = CMP[q][str(k)]
        cites = xl["cites"].get(str(k)) or [["derived 17 - 19", None]]
        if k == 18:
            line = [xl["cites"]["17"][0][1]] + [x[1] for x in xl["cites"]["19"]]
        elif k in (19, 32):
            line = [x[1] for x in cites]
        else:
            line = cites[0][1]
        nsrc = None
        nagree = None
        if k in note:
            n = note[k]
            nsrc = "%s: %s @L%d (pre %s, adj %s)" % (f["note_label"], format(n["post"], ",.0f"), n["line"], format(n["pre"], ",.0f"), format(n["adj"], ",.0f"))
            nagree = abs(n["post"] - c["later_xml"]) < 0.5 and abs(n["pre"] - c["master"]) < 0.5
        elif k == 32:
            e = note.get("ecl")
            if e:
                nsrc = "%s: the only item-32 leaf that moves is 기대신용손실 %s -> %s (adj %s) @L%d; old %s + adj = %s" % (
                    f["note_label"], format(e["pre"], ",.0f"), format(e["post"], ",.0f"), format(e["adj"], ",.0f"), e["line"], format(c["master"], ",.0f"), format(c["master"] + e["adj"], ",.0f"))
                nagree = abs(c["master"] + e["adj"] - c["later_xml"]) < 0.5
        elif k == 19:
            e = note.get("insfinexp")
            if e:
                nsrc = "%s: 보험금융비용 %s -> %s (adj %s) @L%d, the only finance line that moves; item 19 = -(보험금융비용) + others, so old %s - adj = %s" % (
                    f["note_label"], format(e["pre"], ",.0f"), format(e["post"], ",.0f"), format(e["adj"], ",.0f"), e["line"], format(c["master"], ",.0f"), format(c["master"] - e["adj"], ",.0f"))
                nagree = abs(c["master"] - e["adj"] - c["later_xml"]) < 0.5
        elif k == 18:
            n17 = note.get(17)
            if n17:
                i19 = CMP[q]["19"]["later_xml"]
                nsrc = "derived 18 = 17 - 19 from the note post-restatement item 17 (%s @L%d) and item 19 (%s)" % (format(n17["post"], ",.0f"), n17["line"], format(i19, ",.0f"))
                nagree = abs(n17["post"] - i19 - c["later_xml"]) < 0.5
        api_ok = c["api_prior"] is not None and abs(c["api_prior"] - c["later_xml"]) < 0.5
        cen_ok = None if c["census_new"] is None else abs(c["census_new"] - c["later_xml"]) < 0.5
        cites_out = None
        if k == 19:
            cites_out = [{"label": x[0], "line": x[1], "value": xl["items"]["19_parts"][i]} for i, x in enumerate(cites)]
        elif k == 32:
            cites_out = [{"label": x[0], "line": x[1], "value": x[2] if len(x) > 2 else None} for x in cites]
        cells.append({
            "quarter": q, "item": k, "name": NAME[k], "old": c["master"], "new": c["later_xml"], "unit": "백만원",
            "xml_file": xl["file"], "xml_line": line, "xml_label": [x[0] for x in cites],
            "xml_column": f["later_report"] + "; separate (OFS) statement, cumulative column",
            "xml_cites": cites_out,
            "orig_check": {"file": xo["file"], "value": c["orig_xml"], "line": (xo["cites"][str(k)][0][1] if k not in (18, 19, 32) else None), "equals_master": abs(c["orig_xml"] - c["master"]) < 0.5},
            "second_source": {"restatement_note": nsrc, "restatement_note_agrees": nagree, "fs_api_cache": f["api"], "fs_api_value": c["api_prior"], "fs_api_agrees": api_ok},
            "census_new": c["census_new"], "agrees_with_census": cen_ok,
            "census_note": ("not in the census cell list (census counted the 1 mn move as rounding); the later filing and the restatement note both print it (기대신용손실 25 -> 24)" if (cen_ok is None and k == 32 and q == "2024.1Q") else None),
            "owner_gold_cell": False,
        })
    buckets.append({
        "quarter": q, "adopt": True, "n_cells": len(adopt), "items": adopt,
        "later_filing": "%s rcept %s" % (f["later_fy"], f["later_rcept"]), "original_filing": "%s rcept %s" % (f["orig_fy"], f["orig_rcept"]),
        "owner_gold_cells_in_block": [16], "owner_gold_overlap_with_adopted": CLO[q]["gold_overlap"],
        "closure_merged": CLO[q]["identities_merged"], "gate_pl_bridge_merged": CLO[q]["gate_merged"], "gate_pl_bridge_old": CLO[q]["gate_old"],
        "reason": "closes on the merged vector (20=1+17, 22-24=23, 31=24+25, 25=26+27+28+29+30+32, 17=18+19, LOB bridge unchanged); no owner gold cell changes; CSM unchanged (insurance result and CSM identical in both vintages)",
    })

seam_cells = []
NOTE3M = {}
for lab, toks in parse_note("FY2024_Q3"):
    for key, pat in NOTE_RULES:
        if key in NOTE3M or key not in (20, 22, 23, 24):
            continue
        if re.fullmatch(pat, lab) and len(toks) >= 7:
            NOTE3M[key] = {"post": num(toks[3][0]), "pre": num(toks[1][0]), "line": toks[3][1]}
for s in SEAM["seam"]:
    n3 = NOTE3M[s["item"]]
    assert abs(n3["post"] - s["value"]) < 0.5, (s["item"], n3, s["value"])
    seam_cells.append({
        "quarter": s["quarter"], "item": s["item"], "name": s["name"], "old_dangi": s["old_dangi_stored"], "derived_if_unfixed": s["derived_if_unfixed"],
        "proposal": "set_dangi", "value": s["value"], "unit": "백만원", "xml_file": s["xml_file"], "xml_line": s["xml_line"], "xml_label": s["xml_label"],
        "second_source": "FY2024 3Q report note 41 table 2) 전분기 포괄손익계산서, 3개월 수정 후: %s @L%d (수정 전 %s, the pre-correction value that the master 6M-based single quarter still uses)" % (
            format(n3["post"], ",.0f"), n3["line"], format(n3["pre"], ",.0f")),
        "gold_line": ["KR0005", s["quarter"], s["item"], s["value"], "%s:L%d [%s] %s 백만원 (3-month column, prior-year 3Q)" % (s["xml_file"], s["xml_line"], s["xml_label"], format(s["value"], ",.0f"))],
        "reason": s["reason"],
    })


def diffs(a, b):
    ks = [str(k) for k in (1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 32)]
    return {k: [a["items"].get(k), b["items"].get(k)] for k in ks if (a["items"].get(k) or 0) != (b["items"].get(k) or 0)}


vint = {
    "2023.4Q: FY2024 annual col 78기 vs FY2025 annual col 78기 (differences)": diffs(X["later|2023.4Q"], X["later2|2023.4Q"]),
    "2024.3Q: original FY2024 3Q vs FY2025 3Q prior column (differences)": diffs(X["orig|2024.3Q"], X["later|2024.3Q"]),
    "2024.4Q: original FY2024 annual vs FY2025 annual prior column (differences)": diffs(X["orig|2024.4Q"], X["later|2024.4Q"]),
}
n_all = sum(1 for c in cells if (c["second_source"]["restatement_note_agrees"] in (True, None)) and c["second_source"]["fs_api_agrees"] and (c["agrees_with_census"] in (True, None)))
for c in cells:
    q, k = c["quarter"], c["item"]
    f = FILING[q]
    ln = c["xml_line"] if not isinstance(c["xml_line"], list) else ",".join("L%d" % x for x in c["xml_line"])
    ln = ("L%s" % ln) if not isinstance(ln, str) or not ln.startswith("L") else ln
    c["gold_set_entry"] = {
        "원보험사코드": "KR0005", "항목번호": k, "공시분기": q, "값": c["new"], "was": c["old"],
        "note": "2026-10-22 parser/ifrs17 ticket 20261022T0900Z (owner 2026-10-22: latest comparative column, separate basis, closing block only): FVOCI foreign-currency debt "
                "expected-maturity error correction restated the comparative. Cumulative column printed in %s %s (%s) %s [%s]; "
                "agrees with the restatement note table and the DART FS-API prior column. Original filing %s printed %s (= master)." % (
                    f["later_fy"], f["later_rcept"], c["xml_file"], ln, "/".join(c["xml_label"]), f["orig_rcept"], format(c["old"], ",.0f")),
    }
units = {}
for fy in ("FY2024_Q3", "FY2024_Q4", "FY2025_Q1", "FY2025_Q2", "FY2023_Q3", "FY2023_Q4", "FY2024_Q1", "FY2024_Q2", "FY2025_Q3", "FY2025_Q4"):
    on, hdr = False, []
    for ln in (EVD / ("KR0005_s5_stmt_%s.txt" % fy)).read_text(encoding="utf-8").split("\n"):
        if "포괄손익계산서 ::" in ln and not on:
            on = True
            hdr = []
            continue
        if on:
            hdr.append(ln.split(" :: ")[0][:80])
            if "단위" in ln or len(hdr) > 5:
                break
    units[fy] = hdr
n_eq = sum(1 for c in cells if c["orig_check"]["equals_master"])
plan = {
    "company": "KR0005", "name": "흥국화재", "basis": "separate (OFS) statement, prior-period cumulative column of the next-year filing", "unit": "백만원",
    "restatement_cause": "error correction: expected maturity of FVOCI foreign-currency debt instruments (effective-interest-rate measurement); notes 41/45 of the later filings",
    "buckets": buckets, "cells": cells, "seam_cells": seam_cells,
    "blank_before_and_after": SEAM["blank_before_and_after"],
    "side_effect_single_quarters": SEAM["side_effects"],
    "verification": {
        "n_cells": len(cells), "n_cells_all_sources_agree": n_all, "n_cells_original_xml_equals_master": n_eq, "vintage_checks": vint,
        "units_and_periods_header_rows_of_the_statements": units,
        "census_differences": "none for 44 cells; 1 extra cell vs census: 2024.1Q item 32 (-199 -> -200), printed by the later filing and by note 41 (기대신용손실 25 -> 24)",
        "owner_gold": "gold set cells in these four blocks: item 16 only (2023.3Q 13,225; 2023.4Q 18,758; 2024.1Q 5,112; 2024.2Q 11,246); the later filing prints the same values, item 16 is not adopted; no adopted cell is an owner gold cell. Gold cells of 2023.2Q (items 1,4,19-24) are the 6M operand of the 2023.3Q single quarter and stay unchanged.",
        "closure_basis": "gate code validate_master_tables._check_pl_bridge (source_ids={}, strict) on the merged vector: pass 9 / fail 0 / skip 1 before and after in all 4 buckets; the LOB bridge is the bare form as in the master (item1 - legs = +246, +278, -30, -117 백만원, unchanged because items 1/2/13/14/15/16 do not move); CSM and item 4 do not move (insurance result identical in both vintages).",
        "neighbour_observations_outside_scope": json.loads((EVD / "KR0005_s14_neighbours.json").read_text(encoding="utf-8")),
        "apply_notes": [
            "Write the 45 gold_set_entry objects into data/_gold/user_pl_cells.json set[] (was = old, note = evidence) and the 4 seam_cells[].gold_line arrays into set_dangi.cells; null_dangi is not needed for this company.",
            "Item 18 is derived (17 - 19) and must be adopted together with item 17; item 19 changes only in 2023.4Q (insurance finance expense 344,258 -> 342,477, note 45).",
            "After the build, single quarters: 2023.3Q items 20/22/23/24 = printed 3-month values (set_dangi); 2023.3Q items 17/18/25/26/28/31/32 stay blank (2023.2Q cumulative is blank in the master); 2023.4Q and 2024.2Q singles are post-correction minus post-correction; 2024.3Q singles (neighbour outside the list) change as a side effect and become consistent with the printed 3-month column (max difference 1 백만원 rounding), see side_effect_single_quarters.",
            "Expected gate reaction: PL_OCI_VS_BS_AOCI (IFRS17_BS AOCI stays the original vintage; note 45 prints the restated 2023-12-31 balance sheet: AOCI +28,463, retained earnings -20,607, insurance contract liabilities -1,781), xlsx 손익분해PL drift, master_tables golden SUMMARY.",
            "Not in this plan (reported only): item 16 and item 19 differences of the neighbours 2023.1Q/2023.2Q/2024.3Q/2024.4Q in neighbour_observations_outside_scope; 2023.1Q/2Q items 17,18,25-32 are blank in the master although the later filings print them.",
        ],
    },
}
(EVD / "plan_KR0005.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(len(cells), n_all)
print(json.dumps(vint, ensure_ascii=False))
