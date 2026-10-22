# -*- coding: utf-8 -*-
"""cite_cells: attach filing XML line numbers to the candidate PL cells of a scenario (cands_<name>.json) and write ready_cells_<name>.csv.
Tier-1 items: the printed cell of the LATER filing's separate statement (last numeric column = prior YTD) whose value equals |new| and whose row label matches the item;
derived items: formula + component lines; Tier-2 note items: search inside the LOB/component note table located by the prior-column prototypes (p_lotte/p_meritz/kb_cands).  READ-ONLY.
usage: cite_cells.py <scenario> [<scenario> ...]"""
import csv
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M  # noqa: E402
import plan_lib as PL  # noqa: E402
import stmtlib as S  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
pl, names, inames = M.load_pl()
KEYS = {1: ("보험손익", "보험서비스결과", "보험영업손익", "보험서비스손익"), 16: ("기타사업비용", "사업비"), 17: ("투자손익",), 20: ("영업이익",), 21: ("영업외손익",), 22: ("법인세차감전", "세전"),
        23: ("법인세",), 24: ("순이익", "순손익"), 25: ("기타포괄손익",), 26: ("공정가치측정금융자산관련", "공정가치측정채무", "공정가치측정금융자산평가", "채무"), 27: ("보험계약자산", "보험계약금융", "보험순금융"),
        28: ("위험회피", "현금흐름위험회피"), 29: ("지분", "공정가치측정금융자산평가"), 30: ("재보험계약자산", "재보험순금융", "재보험금융"), 31: ("총포괄", "포괄손익")}
DIRECT = set(KEYS)
DERIVED_TXT = {2: "3 + 8", 3: "보험수익 - 발행보험서비스비용 (statement lines)", 8: "재보험수익 - 재보험비용 (statement lines)", 7: "3 - (4+5+6)", 12: "8 - (9+10+11)", 15: "0.0 (no 기타영업수익 line; assemble default)",
               18: "17 - 19", 19: "보험금융수익-비용 합 (FS-API def.)", 32: "OCI catch-all (leaf rows not in 26..30)", 13: "LOB note", 14: "LOB note"}


def label_ok(item, label):
    nl = M.norm_label(label)
    return any(k in nl for k in KEYS.get(item, ()))


def later_statement(code, q, cache={}):
    fy = M.later_fy(q)
    k = (code, fy)
    if k not in cache:
        path = [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
        lines = M.read_lines(path)
        tabs = S.statement_tables(lines)
        cache.clear()
        cache[k] = (path, lines, tabs[0] if tabs else None)
    return cache[k]


def note_tables(code, q, notes):
    """tables (my reader) of the later filing whose start line is in notes[(code,q)]"""
    fy = M.later_fy(q)
    path = [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
    lines = M.read_lines(path)
    want = set(notes.get((code, q), []))
    return path, lines, [t for t in M.iter_tables(lines) if t["start"] in want]


# note tables located by the prototypes
NOTES = {}
for nm in ("p_lotte.json", "p_meritz.json", "kb_cands.json", "kb_cands_main4.json", "kb_cands_sib2.json"):
    p = M.MEASURE / nm
    if not p.exists():
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    for q, v in d.items():
        code = {"p_lotte.json": "KR0003", "p_meritz.json": "KR0001", "kb_cands.json": "KR0010", "kb_cands_main4.json": "KR0010", "kb_cands_sib2.json": "KR0010"}[nm]
        if nm == "p_lotte.json":
            NOTES[(code, q)] = v.get("tables_prior") or []
        elif nm == "p_meritz.json":
            NOTES[(code, q)] = [v["lines"][2]] if v.get("lines") and v["lines"][2] else []
        else:
            ln = (v.get("lob_note") or {}).get("table")
            NOTES[(code, q)] = [ln[0]] if ln else []
# KB 2023.1Q/2Q live in kb_cands_main4? (rerun wrote only the last call) -> fall back to the cands json 'lob' search below

for scn in sys.argv[1:]:
    d = json.loads((M.MEASURE / f"cands_{scn}.json").read_text(encoding="utf-8"))
    rows = []
    for c in d["pl_cells"]:
        code, q, it = c["code"], c["q"], c["item"]
        path, lines, tb = later_statement(code, q)
        cite, how = [], ""
        if it in DIRECT and tb is not None:
            hits = PL.cite_statement(lines, tb, c["new"])
            hits = [h for h in hits if h[4] == h[5] - 1] or hits
            pref = [h for h in hits if label_ok(it, h[0])] or hits
            cite = [(h[0][:28], h[1], h[2]) for h in pref[:2]]
            how = "statement prior-YTD cell" if cite else "no printed match (derived by identity)"
        elif it in (2, 3, 8) and tb is not None:
            comps = []
            for r in S.read_statement(lines, tb):
                nl = r["nlabel"]
                if nl in ("보험수익", "재보험수익", "발행한보험계약에서생기는보험서비스비용", "재보험비용", "보험서비스비용"):
                    pv = S.prior_ytd(r)
                    if pv:
                        comps.append((r["label"][:22], pv[1], pv[2]))
            cite, how = comps[:4], DERIVED_TXT.get(it, "")
        elif it in (4, 5, 6, 9, 10, 11, 13, 14, 2) and (code, q) in NOTES and NOTES[(code, q)]:
            path2, lines2, nt = note_tables(code, q, NOTES)
            found = []
            for t in nt:
                div = PL.unit_of(lines2, t)
                for r in t["rows"]:
                    for k, cc in enumerate(r["cells"][1:]):
                        if cc["val"] is not None and abs(abs(cc["val"]) / div - abs(c["new"])) < 0.6 and r["cells"]:
                            found.append((r["cells"][0]["text"][:30], cc["line"], cc["text"]))
            cite, how = found[:3], "note table (prior period) cell" if found else "derived from note legs"
        else:
            how = DERIVED_TXT.get(it, "derived")
        rows.append({"scenario": scn, "code": c["code"], "company": names.get(code), "quarter": q, "item": it, "item_name": inames.get(it, ""), "old": c["old"], "new": c["new"],
                     "delta": (None if c["old"] is None else round(c["new"] - c["old"], 6)), "gold_overlap_old_gold_value": c["gold"], "later_filing": M.rel(path),
                     "cite(label|line|text)": " ; ".join(f"{a}|L{b}|{t}" for a, b, t in cite), "how": how})
    with open(M.MEASURE / f"ready_cells_{scn}.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n_c = sum(1 for r in rows if r["cite(label|line|text)"])
    print(scn, "cells", len(rows), "with line cites", n_c)
