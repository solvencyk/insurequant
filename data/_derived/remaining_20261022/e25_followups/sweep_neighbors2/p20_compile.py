# -*- coding: utf-8 -*-
"""Compile every Part-2 read into mismatches_part2.csv + coverage numbers.  Read-only on masters."""
import json, csv, sys, collections, os
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
S2 = ROOT + "/data/_derived/remaining_20261022/e25_followups/sweep_neighbors2/"
pl = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
csm = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r.get("값") for r in json.load(open(f"{ROOT}/CSM_waterfall.json", encoding="utf-8"))}
unc = {tuple(x) for x in json.load(open(S2 + "uncovered.json", encoding="utf-8"))}


def J(name):
    p = S2 + name
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


b01 = J("b01_stmt.json")
n10 = J("n10_terms.json")
n01 = J("n01_notes.json")
c01 = J("c01_csm.json")
x01 = dict(cells=[])
for _n in ("x02_kr0082.json", "x03_kr0079.json", "b04_life_is.json", "x05_kr0079.json"):
    x01["cells"] += J(_n).get("cells", [])
S1 = ROOT + "/data/_derived/remaining_20261022/e25_followups/sweep_neighbors/"
p1 = json.load(open(S1 + "p1_stmt.json", encoding="utf-8"))
OVR = {("KR0099", "2023.1Q", "17"): (119675.0, "L25618 (투자영업손익 583,923) + L25904 (보험금융손익 (464,248)) = 119,675", "reader fix: 17 = 투자영업손익 + 보험금융손익 in the FY2024 KB라이프 statement layout"),
       ("KR0099", "2023.1Q", "18"): (583923.0, "L25618 + L25904 (18 = 17 - 19 = 119,675 + 464,248)", "reader fix, see item 17")}

rows = []
compared = {}    # (c,q,i) -> source


def later_file(c, q, i=None):
    return ""


def add(c, q, i, master, new, unit_div, filing, line, src, conf="high", note="", force_cls=None, sheet="PL"):
    """master/new in million won (PL) ; CSM converted by the caller"""
    key = (c, q, i)
    compared[key] = src
    if master is None:
        if new is not None and abs(new) >= 0.5:
            rows.append(dict(company=c, quarter=q, item=i, master=None, latest=round(new, 3), diff_mn=None, cls="MASTER_BLANK_PRINTED", confidence=conf, filing=filing, line=line, source=src, note=note))
        return
    d = new - master
    if abs(d) < 1e-6:
        return
    if abs(d) <= (3.5 if src.startswith('derived') else 1.0 + 1e-6):
        cls = "ROUNDING_PM1"
    elif force_cls:
        cls = force_cls
    elif abs(abs(new) - abs(master)) <= 1.0 and (new * master) < 0:
        cls = "SIGN"
    elif abs(d) <= 10 and master == round(master) and master % 100 == 0:
        cls = "OTHER_COARSE_ROUNDING"
    else:
        cls = {"stmt": "VINTAGE_STATEMENT", "note": "VINTAGE_NOTE", "csm": "VINTAGE_CSM", "derived": "VINTAGE_DERIVED"}[src.split(":")[0]]
    if c == "KR0072":
        cls = "HELD_KDB(" + cls + ")"
    rows.append(dict(company=c, quarter=q, item=i, master=round(master, 3), latest=round(new, 3), diff_mn=round(d, 3), cls=cls, confidence=conf, filing=filing, line=line, source=src, note=note))


# ---------- statement items
latest_pl = collections.defaultdict(dict)    # (c,q) -> {item: value}
for k, rec in b01.items():
    c, q = k.split("|")
    if rec["err"]:
        continue
    for i, v in rec["items"].items():
        if (c, q, i) not in unc:
            # master present items only; still record the latest value for derived checks
            latest_pl[(c, q)][i] = v["val"]
            continue
        if v.get("ambiguous"):
            rows.append(dict(company=c, quarter=q, item=i, master=pl.get((c, q, i)), latest=round(v["val"], 3), diff_mn=None, cls="UNREADABLE_LAYOUT", confidence="none", filing=rec["file"],
                             line=",".join(str(x) for x in v["line"]), source="stmt:b01", note="statement row prints 3 value cells in a 4-column (3M/cumulative x current/prior) layout: empty cell dropped, column ambiguous; not compared"))
            continue
        latest_pl[(c, q)][i] = v["val"]
        m = pl.get((c, q, i))
        if (c, q, i) in OVR:
            v = dict(v, val=OVR[(c, q, i)][0], line=[OVR[(c, q, i)][1]])
        note = f"calib {rec.get('calib')}; blank cells in prior col: {rec.get('blank_cells')}" + ("; absent line=builder default" if v.get("absent") else "")
        add(c, q, i, m, v["val"], 1, rec["file"], ",".join(str(x) for x in v["line"]), "stmt:b01", note=note)

# ---------- notes: v2 (term based) preferred, v1 as fallback
for src_name, nd in (("note:n10", n10), ("note:n01", n01)):
    for k, rec in nd.items():
        c, q = k.split("|")
        if rec["err"]:
            continue
        for i, v in rec["items"].items():
            if v["status"] != "OK" or (c, q, i) not in unc or (c, q, i) in compared:
                continue
            if src_name == "note:n10":
                lines_ = ",".join(str(x["line"]) for x in v["cites"])
                conf = "high" if v["ncand"] == 1 else "medium"
                note = f"{v['how']}; cal cur={round(v['cur_val'],1)} vs master(q+4)={v['master_cur']}; label={v['cites'][0]['label']}; unit={v['cites'][0]['unit']}"
                val = v["val"]
                if v["master_cur"] is not None and v["cur_val"] * v["master_cur"] < 0:
                    val = -val
                    note += "; company sign convention: master stores the opposite sign (verified on the current column), prior flipped to the master convention"
            else:
                lines_ = ",".join(str(x[0]) for x in v["cells"])
                conf = "high" if v["cal"] == "SELF" else "low"
                note = f"v1 {v['how']}; cal={v['cal']} items={v['cal_items']}; cur={round(v['cur_val'],1)} vs master(q+4)={v['master_cur']}"
                val = v["val"]
            latest_pl[(c, q)][i] = val
            add(c, q, i, v["master"], val, 1, rec["file"], lines_, src_name, conf=conf, note=note)

# ---------- custom readers (list of dict rows with the same fields)
for r in x01.get("cells", []):
    c, q, i = r["company"], r["quarter"], r["item"]
    if (c, q, i) not in unc or (c, q, i) in compared:
        continue
    latest_pl[(c, q)][i] = r["latest"]
    add(c, q, i, r["master"], r["latest"], 1, r["filing"], r["line"], ("stmt:" if r["source"].startswith("stmt") else "note:") + r["source"], conf=r.get("confidence", "high"), note=r.get("note", ""))

# ---------- supplementary legs from the first sweep (not counted as compared)
for k, v in p1.items():
    c, q = k.split("|")
    for i in ("2", "3", "8"):
        d = v.get("prior", {}).get(i) if v.get("prior") else None
        if isinstance(d, dict) and i not in latest_pl[(c, q)]:
            latest_pl[(c, q)][i] = d["val"]
# ---------- derived items 2 / 7 / 12 from the latest legs (production definitions)
for (c, q), L in sorted(latest_pl.items()):
    cand = {}
    if "3" in L and "8" in L:
        cand["2"] = (L["3"] + L["8"], "2 = 3 + 8")
    if all(x in L for x in ("3", "4", "5", "6")):
        cand["7"] = (L["3"] - (L["4"] + L["5"] + L["6"]), "7 = 3 - (4+5+6)")
    if all(x in L for x in ("8", "9", "10", "11")):
        cand["12"] = (L["8"] - (L["9"] + L["10"] + L["11"]), "12 = 8 - (9+10+11)")
    for i, (val, f) in cand.items():
        if (c, q, i) in unc and (c, q, i) not in compared:
            add(c, q, i, pl.get((c, q, i)), val, 1, "derived from the latest legs of this sweep", "-", "derived:" + f, conf="medium", note=f"{f}; legs " + ", ".join(f"{x}={round(L[x], 1)}" for x in sorted(L, key=int) if x in f.replace("(", " ").replace(")", " ").replace("+", " ").replace("-", " ").replace("=", " ").split()))
# ---------- CSM
for k, rec in c01.items():
    c, q = k.split("|")
    if rec["status"] != "OK":
        continue
    for i in range(1, 7):
        key = (c, q, "CSM" + str(i))
        if key not in unc:
            continue
        m = csm.get((c, str(i), q)) if False else csm.get((c, q, str(i)))
        new = rec["prior"][str(i)]
        if m is None:
            continue
        compared[key] = "csm:c01"
        d = new - m
        if abs(d) <= 0.06:
            if abs(d) > 1e-9:
                rows.append(dict(company=c, quarter=q, item="CSM" + str(i), master=round(m * 100, 1), latest=round(new * 100, 1), diff_mn=round(d * 100, 1), cls="ROUNDING_PM1", confidence="high",
                                 filing=rec["file"], line=",".join(str(x[str(i)][2]) for x in rec["cites"]), source="csm:c01", note="eok printed rounding (<=0.06 eok)"))
            continue
        cls = "VINTAGE_CSM"
        if c == "KR0072":
            cls = "HELD_KDB(VINTAGE_CSM)"
        rows.append(dict(company=c, quarter=q, item="CSM" + str(i), master=round(m * 100, 1), latest=round(new * 100, 1), diff_mn=round(d * 100, 1), cls=cls, confidence="high",
                         filing=rec["file"], line="; ".join(f"cell L{x[str(i)][0]} '{x[str(i)][1]}' (tr L{x[str(i)][2]})" for x in rec["cites"]), source="csm:c01",
                         note=f"summed over {len(rec['tables'])} product-group table(s) {rec['tables']}; closure {rec['closure_eok']} eok; eok converted to mn"))

# ---------- master holds a single-quarter (3-month) figure instead of the cumulative one
def prevq(q):
    return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"
for r in rows:
    if r["cls"] in ("VINTAGE_NOTE", "VINTAGE_STATEMENT") and r["master"] is not None and r["item"].isdigit():
        pq = prevq(r["quarter"])
        if pq:
            pms = [x for x in (pl.get((r["company"], pq, r["item"])), latest_pl.get((r["company"], pq), {}).get(r["item"])) if x is not None]
            pm = next((x for x in pms if abs((r["latest"] - x) - r["master"]) <= 1.5 and abs(x) > 5), None)
            if pm is not None:
                r["cls"] = "OTHER_MASTER_HOLDS_3M"
                r["note"] += f"; master = latest cumulative - master of {pq} ({pm}) = single-quarter figure, not cumulative"
# ---------- WRONG_LEG detection: master equals (or sits within 2%+1 of) the paired reinsurance/direct latest value
PAIR = {"4": "9", "5": "10", "6": "11", "9": "4", "10": "5", "11": "6"}
g2 = json.load(open(S1 + "p2_generic.json", encoding="utf-8"))
for r in rows:
    if r["cls"].startswith(("VINTAGE", "SIGN", "HELD")) and r["item"] in PAIR and r["master"] is not None:
        c, q = r["company"], r["quarter"]
        cands = []
        lv = latest_pl[(c, q)].get(PAIR[r["item"]])
        if lv is not None:
            cands.append((lv, "this sweep"))
        for x in (g2.get(f"{c}|{q}", {}).get("prior", {}) or {}).get(PAIR[r["item"]], []) or []:
            cands.append((x["val"], f"first sweep p2_generic L{x['line']}"))
        for lv, srcn in cands:
            if abs(abs(lv) - abs(r["master"])) <= 0.02 * abs(lv) + 1.0 and abs(r["master"]) > 5 and abs(abs(r["latest"]) - abs(r["master"])) > 0.05 * abs(r["latest"]):
                r["cls"] = r["cls"].replace("VINTAGE_NOTE", "WRONG_LEG").replace("VINTAGE_STATEMENT", "WRONG_LEG")
                r["note"] += f"; master {r['master']} is within 2% of the paired item {PAIR[r['item']]} printed {lv} ({srcn})"
                break
# extra (outside the 3,703 denominator): CSM blocks that the loads did not touch but whose latest comparative was readable
c03 = J("c03_csm_extra.json")
for k, rec in c03.items():
    c, q = k.split("|")
    if rec["status"] != "OK":
        continue
    for i in range(1, 7):
        m = csm.get((c, q, str(i)))
        if m is None:
            continue
        new = rec["prior"][str(i)]
        if abs(new - m) > 0.06:
            rows.append(dict(company=c, quarter=q, item="CSM" + str(i), master=round(m * 100, 1), latest=round(new * 100, 1), diff_mn=round((new - m) * 100, 1), cls="VINTAGE_CSM(extra, not in denominator)", confidence="high",
                             filing=rec["file"], line="; ".join(f"cell L{x[str(i)][0]} '{x[str(i)][1]}'" for x in rec["cites"]), source="csm:c03_extra", note=f"closure {rec['closure_eok']} eok; table(s) {rec['tables']}"))
rows.sort(key=lambda r: -abs(r["diff_mn"] or 0))
cols = ["company", "quarter", "item", "master", "latest", "diff_mn", "cls", "confidence", "filing", "line", "source", "note"]
with open(S2 + "mismatches_part2.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, cols)
    w.writeheader()
    for r in rows:
        w.writerow(r)

# ---------- structural (not source-read): life companies carry 0 in items 13 and 14 by construction of assemble()
LIFE = {"KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0079", "KR0082", "KR0083", "KR0087", "KR0094", "KR0099", "KR0104"}
structural = {k for k in unc if k[0] in LIFE and k[2] in ("13", "14") and k not in compared}
struct_bad = [k for k in structural if pl.get((k[0], k[1], k[2])) not in (0, 0.0)]
print("structural life 13/14 cells", len(structural), "non-zero in master:", struct_bad)
# ---------- coverage
comp_u = {k for k in compared if k in unc}
n25_3 = {k for k in unc if k[1] == "2025.3Q"}
print("structural (not counted):", len(structural))
print("uncovered cells (first sweep)", len(unc), "| now compared", len(comp_u), "| still unchecked", len(unc - comp_u))
print("of the unchecked: 2025.3Q (no later filing)", len(n25_3), "| other", len(unc - comp_u - n25_3))
tot = 3703
print(f"coverage overall: {(2038 + len(comp_u))}/{tot} = {100 * (2038 + len(comp_u)) / tot:.1f}%   excluding 2025.3Q from denominator: {(2038 + len(comp_u))}/{tot - len(n25_3)} = {100 * (2038 + len(comp_u)) / (tot - len(n25_3)):.1f}%")
byc = collections.defaultdict(lambda: [0, 0, 0])
for k in unc:
    byc[k[0]][0] += 1
for k in comp_u:
    byc[k[0]][1] += 1
for k in n25_3 - comp_u:
    byc[k[0]][2] += 1
print("per company: uncovered / now compared / of which unreadable 2025.3Q")
for c in sorted(byc):
    print(" ", c, byc[c])
real = [r for r in rows if r["cls"] != "ROUNDING_PM1"]
print("rows", len(rows), "non-rounding", len(real))
cnt = collections.defaultdict(collections.Counter)
for r in real:
    cnt[r["company"]][r["cls"]] += 1
for c in sorted(cnt):
    print(" ", c, dict(cnt[c]))
print("top15 by |diff|")
for r in real[:15]:
    print(" ", r["company"], r["quarter"], r["item"], r["master"], r["latest"], r["diff_mn"], r["cls"], r["confidence"])
json.dump(sorted([list(k) for k in comp_u]), open(S2 + "compared_part2.json", "w"))
unchecked = sorted(unc - comp_u)
json.dump([list(k) for k in unchecked], open(S2 + "unchecked_part2.json", "w"))
# unchecked breakdown by item class
ic = collections.Counter()
for c, q, i in unchecked:
    ic[(c, "CSM" if i.startswith("CSM") else ("stmt" if i in {"1", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32"} else ("note" if i in {"4", "5", "6", "9", "10", "11"} else "derived/LOB(2,3,7,8,12,13,14)")))] += 1
print("unchecked by (company, kind):")
for k, v in sorted(ic.items()):
    print("  ", k, v)
