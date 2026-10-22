"""ready_csm_cells: candidate CSM cells (READY scenarios R2 + R2b) with the printed source cells of the LATER filing (independent re-reads v1/v3/v4/c3) -> ready_csm_cells.csv
Also writes csm_vector_sources.csv: the same source lookup for every company x quarter that appears in a decision table (KB라이프, ABL, KDB, 현대, 롯데 2023.4Q).  READ-ONLY."""
import csv
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import csmvec as CV  # noqa: E402
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
H = M.MEASURE
pl, names, _ = M.load_pl()
csm_rows = M.jload(M.SNAP / "CSM_waterfall.json")
cnames = {int(r["항목번호"]): r["항목명"] for r in csm_rows}


def J(name):
    p = H / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


V1 = {}
for fn in ("v1_csm_verify_kblife2023.json", "v1_csm_verify_hanwha.json", "v1_csm_verify_abl_kdb_hd.json", "v1_csm_verify_kblife_lotte4Q.json", "v1_csm_verify_lotte.json"):
    for k, d in J(fn).items():
        if k in V1:
            continue
        good = [t for t in d.get("tables", []) if t["n_items"] >= 5 and t["open_close"]]
        if good:
            V1[k] = (good, d["vec"])
V3, V4, C3 = J("v3_mirae_wide.json"), J("v4_meritz_csm.json"), J("c3_KR0079_FY2025_Q1.json")


_SEP = {}


def sep_from(code, fy, fname):
    """first line of the separate-basis notes ('5. 재무제표 주석' TITLE) of the filing file; 0 when not found"""
    k = (code, fy, fname)
    if k not in _SEP:
        import re
        import stmtlib as S
        path = next((p for p in M.main_xmls(code, fy) if p.name == fname), None)
        v = 0
        if path is not None:
            lines = M.read_lines(path)
            for ln, tt in S.titles(lines):
                if re.match(r"^\d+\.재무제표주석$", re.sub(r"\s+", "", tt)):
                    v = ln
            del lines
        _SEP[k] = v
    return _SEP[k]


def cite_vec(code, q):
    """-> (vec, file, table_start, {item: cite-string}) or None"""
    key = f"{code}|{q}"
    fy = M.later_fy(q)
    if key in V1:
        tl, vec = V1[key]
        t = next((x for x in tl if x["table_start"] >= sep_from(code, fy, x["file"])), tl[0])
        cites = {int(i): f"{h[0].strip()}|L{h[1]}|{h[2]}" for i, h in t["hits"].items()}
        basis = "separate-basis table" if t["table_start"] >= sep_from(code, fy, t["file"]) else "table (basis not tagged)"
        return vec, t["file"], t["table_start"], cites, f"single {basis} prints the vector (unit-agnostic cell match)"
    if code == "KR0001":
        for ent in V4.get(fy, []):
            if abs(ent["vec"][0] - 96376.4) < 0.1:
                R = ent["rows"]
                keymap = {1: "open", 2: "new", 3: "int", 4: "adj", 5: "amort", 6: "close"}
                cites = {i: f"{k}|row L{R[k]['row_line']}|CSM 3 columns L{R[k]['cell_lines'][0]}..L{R[k]['cell_lines'][1]} = {R[k]['eok']:,.2f}eok" for i, k in keymap.items()}
                return ent["vec"], ent["file"], ent["table_start"], cites, "sum of the 3 CSM columns (수정소급법/공정가치법/그 외) of the 원수 일반모형 prior table"
    if code == "KR0079" and fy in V3:
        for ent in V3[fy]:
            if abs(ent["vec"][0] - 20214.5) < 0.1:
                R = ent["rows"]
                keymap = {1: "open", 2: "new", 3: "int", 5: "amort", 6: "close"}
                cites = {}
                for i, k in keymap.items():
                    ls = R[k][-1]
                    cites[i] = f"{k}|row L{ls['row_line']}|CSM columns of 5 products L{ls['cell_lines'][0]}..L{ls['cell_lines'][1]} = {ls['eok']:,.2f}eok"
                cites[4] = "derived: 기말 - (기초 + 신계약 + 이자 + 상각) (no printed cell)"
                return ent["vec"], ent["file"], ent["table_start"], cites, "wide roll-forward: sum of the CSM sub-columns of 5 product groups (issued contracts)"
    if code == "KR0079" and q == "2024.1Q" and C3:
        pr = C3["prior"]["by_table"]
        keymap = {1: "open", 2: "new", 3: "int", 5: "amort", 6: "close"}
        cites = {i: f"{k}|5 product tables: " + ", ".join(f"T{a}@L{c}={b:,.0f}mn" for a, b, c in pr[k]) for i, k in keymap.items()}
        cites[4] = "derived: 기말 - (기초 + 신계약 + 이자 + 상각)"
        return C3["prior"]["eok_1to6"], C3["file"], pr["open"][0][0], cites, "row-block layout: 전기 block of the 5 product tables, CSM 소계 column summed"
    return None


rows = []
for scn in ("R2", "R2b_Lotte_2023_1Q2Q"):
    d = json.loads((H / f"cands_{scn}.json").read_text(encoding="utf-8"))
    for c in d["csm_cells"]:
        info = cite_vec(c["code"], c["q"])
        if info:
            vec, f, ts, cites, how = info
            cite, tbl, flt = cites.get(c["item"], ""), f"T{ts}", f
        else:
            cite, tbl, flt, how = "", "", "", "NOT independently re-read (dry-run vector only)"
        rows.append({"scenario": scn, "sheet": "CSM", "code": c["code"], "company": names.get(c["code"]), "quarter": c["q"], "item": c["item"], "item_name": cnames.get(c["item"], ""),
                     "old": c["old"], "new": c["new"], "delta": round(c["new"] - c["old"], 4), "gold_overlap_old_gold_value": c.get("gold"), "later_filing": f"{M.later_fy(c['q'])}/{flt}",
                     "source_table": tbl, "cite(label|line|text)": cite, "how": how})
with open(H / "ready_csm_cells.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
n_cite = sum(1 for r in rows if r["cite(label|line|text)"])
print("ready_csm_cells.csv rows", len(rows), "with cite", n_cite)

# vector sources for the decision-table companies
src = []
TARGETS = ([("KR0099", f"{y}.{q}Q") for y in (2023, 2024) for q in (1, 2, 3, 4)] + [("KR0070", f"2023.{q}Q") for q in (1, 2, 3, 4)] + [("KR0072", f"2023.{q}Q") for q in (1, 2, 3, 4)]
           + [("KR0009", f"2023.{q}Q") for q in (1, 2, 3, 4)] + [("KR0003", "2023.4Q")])
for code, q in TARGETS:
    info = cite_vec(code, q)
    vec = CV.prior(code, q)
    if not info:
        src.append({"code": code, "company": names.get(code), "quarter": q, "later_filing": M.later_fy(q), "vector_eok": vec, "table": "", "how": "not independently re-read", "item_cites": ""})
        continue
    v, f, ts, cites, how = info
    src.append({"code": code, "company": names.get(code), "quarter": q, "later_filing": f"{M.later_fy(q)}/{f}", "vector_eok": v, "table": f"T{ts}", "how": how,
                "item_cites": " ; ".join(f"item{i}:{cites[i]}" for i in sorted(cites))})
with open(H / "csm_vector_sources.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(src[0].keys()))
    w.writeheader()
    w.writerows(src)
print("csm_vector_sources.csv rows", len(src), "re-read", sum(1 for s in src if s["table"]))
