# -*- coding: utf-8 -*-
"""Part 2, CSM roll-forward (items 1-6) of the issued-contract tables in the separate notes of the LATER filing, summed over product-group tables (ABL / KDB / KB라이프).
Group = a first table (caption not starting with a circled digit 2..9) plus the following tables whose caption starts with a circled digit (product segmentation, e.g. 1)당기 ① 유배당 ② 무배당 ...).
Calibration: the group whose CSM vector reproduces the master of quarter+4 (|diff| <= 0.06 eok on items 5 and 6) is the current period; the next group of the same shape is the prior period.
Closure check on every group: 1+2+3+4+5 = 6 (eok, tolerance 0.06)."""
import json, sys, re, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e23_read as E
import s2lib
import e21_t2 as T
import e21_raw as W
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
S2 = ROOT + "/data/_derived/remaining_20261022/e25_followups/sweep_neighbors2/"
csm = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/CSM_waterfall.json", encoding="utf-8"))}
unc = sorted({tuple(x) for x in json.load(open(S2 + "uncovered.json", encoding="utf-8"))})
DIV_EOK = {"백만원": 100.0, "원": 1e8, "천원": 1e5}
RULES = {
    "KR0070": {1: lambda x: x.startswith("I.기초보험계약순부채"), 2: lambda x: x.startswith("(3)해당기간에처음인식한계약의효과"), 3: lambda x: x.startswith("VI.보험금융비용"),
               4: lambda x: x.startswith("(1)보험계약마진을조정하는추정치의변동분"), 5: lambda x: x.startswith("(1)서비스제공으로당기손익으로인식된보험계약마진"),
               6: lambda x: re.match(r"^X\.(분기말|반기말|기말)보험계약순부채", x) is not None},
    "KR0072": {1: lambda x: x.startswith("1.기초보험계약자산및부채"), 2: lambda x: x.startswith("(3)최초인식한계약의효과"), 3: lambda x: x.startswith("6.보험금융손익"),
               4: lambda x: x.startswith("(1)보험계약마진을조정하는추정치의변동분") or x.startswith("(1)보험계약마진을조정하는추"), 5: lambda x: x.startswith("(1)서비스이전을반영하기위"),
               6: lambda x: re.match(r"^(8|9)\.(당기말|전분기말|전반기말|전기말|분기말|반기말|기말)보험계약자산및부채", x) is not None},
    "KR0099": {1: lambda x: x == "기초순장부금액", 2: lambda x: x == "신계약효과", 3: lambda x: x.startswith("보험금융손익(PL)"),
               4: lambda x: x == "보험계약마진을조정하는추정치변동", 5: lambda x: x == "서비스제공에따른보험계약마진변동",
               6: lambda x: re.match(r"^(분기말|반기말|기말)순장부금액$", x) is not None},
}
CIRC = re.compile(r"^[②③④⑤⑥⑦⑧⑨]")


def csm_col(rows):
    for r in rows[:4]:
        labs = [E.nl(c["text"]) for c in r["cells"]]
        for k, x in enumerate(labs):
            if "보험계약마진" in x:
                has_label = labs[0] in ("구분", "") if labs else False
                return (k - 1) if has_label else k   # numeric index among the numeric cells after the label cell
    return None


def read_groups(code, fy):
    path = T.main_path(code, fy)
    lines, s0, tabs = s2lib.tables_sep2(path)
    rules = RULES[code]
    gl = []
    for t, rows in tabs:
        labs = [E.lab(r) for r in rows]
        if not (any(rules[1](x) for x in labs) and any(rules[5](x) for x in labs) and any(rules[6](x) for x in labs)):
            continue
        hdr = E.nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        if "보험계약마진" not in hdr:
            continue
        cap = E.nl(t["caption"] or "")
        if code == "KR0099" and not ("적용하지않은" in cap and "재보험" not in cap):
            continue
        if code == "KR0072" and ("배당" in cap or "(7)" in cap):
            continue
        try:
            unit = T.find_unit(lines, t, span=2500)
        except Exception:
            unit = "?"
        col = csm_col(rows)
        vec, cites = {}, {}
        ok = True
        for it, pred in rules.items():
            h = [r for r in rows if pred(E.lab(r))]
            if not h:
                ok = False
                break
            n = W.numeric_cells(h[0])
            if col is None or len(n) <= col:
                ok = False
                break
            vec[it] = n[col][0] / DIV_EOK.get(unit, float("nan"))
            cites[it] = (n[col][1], n[col][2], h[0]["tr_line"])
        if not ok:
            continue
        gl.append(dict(start=t["start"], end=t["end"], cap=cap, hdr=hdr[:80], unit=unit, vec=vec, cites=cites, col=col))
    groups = []
    for t in gl:
        if groups and CIRC.match(t["cap"]):
            groups[-1].append(t)
        else:
            groups.append([t])
    return path, groups


def gsum(g):
    v = {i: sum(t["vec"][i] for t in g) for i in range(1, 7)}
    return v


out = {}
targets = sorted({(c, q) for c, q, i in unc if i.startswith("CSM") and c in RULES and q != "2025.3Q"})
for c, q in targets:
    fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
    mq = f"{int(q[:4]) + 1}.{q[5:]}"
    rec = dict(file=None, err=None, status=None)
    try:
        path, groups = read_groups(c, fy)
        rec["file"] = str(path).replace("\\", "/").split("insurequant/")[-1]
        rec["ngroups"] = [(len(g), g[0]["start"], g[0]["cap"][:20]) for g in groups]
        mcur = {i: csm.get((c, str(i), mq)) for i in range(1, 7)}
        pick = None
        for gi, g in enumerate(groups):
            s = gsum(g)
            if mcur[5] is not None and mcur[6] is not None and abs(s[5] - mcur[5]) <= 0.06 and abs(s[6] - mcur[6]) <= 0.06:
                pick = gi
                break
        if pick is None:
            rec["status"] = "UNCAL"
            rec["cur_sums"] = [gsum(g) for g in groups]
            rec["master_cur"] = mcur
        else:
            if pick + 1 >= len(groups):
                rec["status"] = "NOPRIOR"
            else:
                pg = groups[pick + 1]
                s = gsum(pg)
                clos = s[1] + s[2] + s[3] + s[4] + s[5] - s[6]
                rec["status"] = "OK"
                rec["closure_eok"] = round(clos, 3)
                rec["prior"] = {str(i): round(s[i], 4) for i in range(1, 7)}
                rec["cites"] = [{str(i): t["cites"][i] for i in range(1, 7)} for t in pg]
                rec["tables"] = [(t["start"], t["cap"]) for t in pg]
                rec["cur_check"] = {str(i): round(gsum(groups[pick])[i], 4) for i in range(1, 7)}
                rec["master_cur"] = mcur
    except Exception as e:
        rec["status"] = "ERR"
        rec["err"] = f"{type(e).__name__}: {str(e)[:200]}"
    out[f"{c}|{q}"] = rec
    print(c, q, rec["status"], rec.get("closure_eok", ""), rec["err"] or "", rec.get("ngroups", ""), flush=True)
json.dump(out, open(S2 + "c01_csm.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
