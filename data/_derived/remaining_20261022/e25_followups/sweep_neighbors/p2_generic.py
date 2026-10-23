# -*- coding: utf-8 -*-
"""Phase 2 generic label-driven note reader (items 4, 5, 9, 10) with self-calibration: the SAME reader applied to the CURRENT column of the later filing must reproduce
the master at quarter+4 before its PRIOR-column reads are trusted.  Read-only.  Reuses e23 table reader (rows_full23)."""
import json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
import e23_read as E
import e21_t2 as T
import e21_raw as W
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
UD = {"원": 1e6, "천원": 1e3, "백만원": 1.0}
CSM = re.compile(r"보험계약마진.*(상각|해제|제공|이전|인식)|(상각|해제|제공|이전).*보험계약마진|^csm")
RA = re.compile(r"위험조정.*(변동|해제|상각|감소|환입)|위험조정의?변동|^ra")
def classify(lab):
    k = None
    if CSM.search(lab) and "추정" not in lab and "조정하는" not in lab and "처음" not in lab and "최초" not in lab and "신계약" not in lab: k = "csm"
    elif RA.search(lab) and "처음" not in lab and "최초" not in lab and "신계약" not in lab and "손실" not in lab: k = "ra"
    return k
def sections(rows):
    """yield (row, region) with region 'dir' before the first reinsurance-income/cost header, else 're'"""
    region = "dir"
    for r in rows:
        lab = E.lab(r)
        cells = [E.nl(c["text"]) for c in r["cells"][:2]]
        if any(re.match(r"^(재보험수익|재보험비용|출재보험서비스수익|출재보험서비스비용|출재보험수익|출재보험비용|재보험서비스수익|재보험서비스비용)$", c) for c in cells) or lab.startswith(("재보험수익", "재보험비용", "출재보험")):
            region = "re"
        yield r, region
def numcells(r):
    out = []
    for c in r["cells"]:
        if c["val"] is not None: out.append(c)
        elif c["text"].strip() in ("-", "−"): out.append(dict(c, val=0.0))
    return out
def read(code, fy, role, kind="cum", q_no=None):
    path = T.main_path(code, fy)
    lines, s0, tabs = E.tables_sep(path)
    cands = []
    for t, rows in tabs:
        labs = [E.lab(r) for r in rows]
        if not (any(classify(x) == "ra" for x in labs) and any(classify(x) == "csm" for x in labs)): continue
        cap = E.nl(t["caption"] or "")
        hdr = E.nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        cands.append((t, rows, cap, hdr))
    got = {}
    unit_by = {}
    for t, rows, cap, hdr in cands:
        unit = T.find_unit(lines, t, span=2500) or "?"
        for r, region in sections(rows):
            k = classify(E.lab(r))
            if not k: continue
            n = numcells(r)
            # label cell digits can leak in: take trailing numeric cells only
            if len(n) == 2: idx = 0 if role == "cur" else 1
            elif len(n) == 4: idx = {("cur", "cum"): 1, ("prior", "cum"): 3}[(role, kind)]
            elif len(n) == 1 and ("전기" in cap or "전분기" in cap or "전반기" in cap) and role == "prior": idx = 0
            elif len(n) == 1 and ("당기" in cap or "당분기" in cap or "당반기" in cap) and role == "cur": idx = 0
            else: continue
            item = {("csm", "dir"): 4, ("ra", "dir"): 5, ("csm", "re"): 9, ("ra", "re"): 10}[(k, region)]
            c = n[idx]
            val = c["val"] / UD.get(unit, float("nan"))
            got.setdefault(item, []).append(dict(val=val, line=c["line"], printed=c["text"], label=E.lab(r), table=t["start"], unit=unit, ncols=len(n)))
    return path, got
if __name__ == "__main__":
    t = json.load(open("s01_touched.json", encoding="utf-8"))
    cq = sorted({tuple(k.split("|")) for v in t.values() for k in v})
    pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
    out = {}
    for c, q in cq:
        fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
        rec = {}
        for role in ("prior", "cur"):
            try:
                path, got = read(c, fy, role)
                rec[role] = got; rec["file"] = str(path).replace("\\", "/").split("insurequant/")[-1]
            except Exception as e:
                rec[role + "_err"] = f"{type(e).__name__}: {str(e)[:160]}"
        out[f"{c}|{q}"] = rec
        pr = rec.get("prior", {})
        print(c, q, {i: [round(x["val"], 3) for x in v][:3] for i, v in pr.items()}, rec.get("prior_err", ""), flush=True)
    json.dump(out, open("p2_generic.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
