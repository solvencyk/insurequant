# -*- coding: utf-8 -*-
"""KR0104 2023.3Q independent re-verification of plan_KR0104.json (READ-ONLY; writes only KR0104_verify.json / .txt in this folder).
Independent of KR0104_plan.py: own XML row reader, own label map, own FS-API read, own closure, build_root_masters._flow_dangi for the quarterly model."""
import json
import re
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
import build_root_masters as BRM   # import only: main() is guarded

plan = json.loads((HERE / "plan_KR0104.json").read_text(encoding="utf-8"))
live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
L = {}
for r in live:
    if r["원보험사코드"] == "KR0104":
        L[(r["공시분기"], r["항목번호"])] = r
out, res = [], {}


def say(s):
    out.append(s)


def num(s):
    s = s.strip().replace(",", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if not re.fullmatch(r"-?\d+(\.\d+)?", s):
        return None
    v = float(s)
    return -v if neg else v


_cache = {}


def lines_of(rel):
    if rel not in _cache:
        _cache[rel] = (ROOT / rel).read_text(encoding="utf-8").split("\n")
    return _cache[rel]


def stmt_range(rel, title_pat="4-2. 포괄손익계산서"):
    ls = lines_of(rel)
    st = [i for i, l in enumerate(ls) if "<TITLE" in l and title_pat in l]
    assert len(st) == 1, (rel, st)
    en = next(i for i in range(st[0] + 1, len(ls)) if "<TITLE" in ls[i])
    return st[0], en


def rows_in(rel, a, b):
    ls = lines_of(rel)
    rows, cur = [], None
    for i in range(a, b):
        l = ls[i]
        if l.startswith("<TR"):
            cur = []
        elif l.startswith("</TR>"):
            if cur is not None:
                rows.append(cur)
            cur = None
        elif cur is not None:
            m = re.match(r"<P[^>]*>(.*)</P>", l)
            if m:
                cur.append((i + 1, m.group(1).strip().replace("\u3000", "").replace(" ", "")))
    return rows


def stmt_rows(rel):
    a, b = stmt_range(rel)
    return a, b, rows_in(rel, a, b)


def get(rel, label, pos):
    """rows whose label (spaces / fullwidth spaces stripped) equals `label`; pos 1..4 = numeric column. -> list of (value, line, printed)"""
    a, b, rows = stmt_rows(rel)
    key = label.replace(" ", "")
    hits = []
    for r in rows:
        if r and r[0][1] == key:
            n = [(ln, t) for ln, t in r[1:] if num(t) is not None]
            if len(n) >= pos:
                ln, t = n[pos - 1]
                hits.append((num(t), ln, t))
    return hits


F3 = "data/dart/FY2024_Q3/raw/KR0104_농협생명보험/20241114000851.xml"
F2 = "data/dart/FY2024_Q2/raw/KR0104_농협생명보험/20240814002115.xml"
O3 = "data/dart/FY2023_Q3/raw/KR0104_농협생명보험/20231114001637.xml"

a, b, rows = stmt_rows(F3)
ls = lines_of(F3)
hdr = [t for i in range(a, a + 140) for t in re.findall(r"<P>(.*)</P>", ls[i]) if t.strip()][:14]
say("F3 statement range lines %d-%d; header P texts: %s" % (a + 1, b, hdr))
res["unit_header_F3"] = [h for h in hdr if "단위" in h]

LABEL = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 20: "영업이익(손실)", 21: "영업외손익", 22: "법인세차감전순이익",
         23: "법인세비용(수익)", 24: "분기순이익", 25: "기타포괄손익", 26: "기타포괄손익-공정가치측정금융자산관련손익",
         27: "보험계약자산(부채)순금융손익", 28: "현금흐름위험회피파생상품평가손익", 29: "기타포괄손익-공정가치측정금융자산평가손익",
         30: "재보험계약자산(부채)순금융손익", 31: "총포괄손익"}
mine = {}
dup = {}
for it, lab in LABEL.items():
    h = get(F3, lab, 4)
    dup[it] = len(h)
    if h:
        mine[it] = (h[0][0] / 1e6, h[0][1], h[0][2])
say("label hit counts (rows with that label in the 4-2 statement): %s" % dup)
res["label_hit_counts"] = dup
fe = get(F3, "보험금융비용", 4)
re_ = get(F3, "재보험금융비용", 4)
fi = get(F3, "보험금융수익", 4)
ri = get(F3, "재보험금융수익", 4)
say("expense hits %s ; reins expense hits %s ; finance income hits %s ; reins finance income hits %s" % (fe, re_, fi, ri))
v19 = -(fe[0][0] + re_[0][0]) / 1e6
mine[19] = (v19, (fe[0][1], re_[0][1]), "derived")
mine[18] = (mine[17][0] - v19, mine[17][1], "derived 17-19")
mine[32] = (mine[25][0] - sum(mine[i][0] for i in (26, 27, 28, 29, 30)), mine[25][1], "derived")

chk = []
for c in plan["cells"]:
    it, q = c["item"], c["quarter"]
    m = L[(q, it)]["값"]
    ln_mine = mine[it][1]
    if isinstance(ln_mine, tuple):
        line_ok = c["xml_line"] in ln_mine
    else:
        line_ok = c["xml_line"] == ln_mine
    chk.append({"item": it, "old_plan": c["old"], "old_live": m, "old_ok": m == c["old"], "new_plan": c["new"],
                "new_mine": mine[it][0], "new_ok": abs(mine[it][0] - c["new"]) < 5e-6, "line_plan": c["xml_line"], "line_mine": ln_mine,
                "line_ok": line_ok, "file_ok": c["xml_file"] == F3, "unit": c["unit"], "source_unit": c["source_unit"], "cls": c["cls"],
                "delta": round(c["new"] - c["old"], 6)})
res["cells_check"] = chk
bad = [r for r in chk if not (r["old_ok"] and r["new_ok"] and r["line_ok"] and r["file_ok"])]
say("V1/V2: %d plan cells, mismatches: %s" % (len(chk), bad))
planned = {c["item"] for c in plan["cells"]}
diff_items = []
for it in sorted(mine):
    old = L[("2023.3Q", it)]["값"]
    if abs(old - mine[it][0]) > 5e-4:
        diff_items.append((it, old, round(mine[it][0], 6)))
say("items where live master != later print (>5e-4 mn): %s ; not in plan: %s" % (diff_items, [d for d in diff_items if d[0] not in planned]))
res["diff_items_vs_later"] = diff_items
census8 = [17, 18, 20, 22, 23, 24, 28, 31]
res["census8_delta"] = {str(i): round(mine[i][0] - L[("2023.3Q", i)]["값"], 6) for i in census8}

ob, oc = stmt_range(O3)
ols = lines_of(O3)
ohdr = [t for i in range(ob, ob + 400) for t in re.findall(r"<P[^>]*>(.*)</P>", ols[i]) if "단위" in t or "제 12" in t or "제 11" in t or t in ("3개월", "누적")]
orig = {}
for it, lab in LABEL.items():
    h = get(O3, lab, 2)
    orig[it] = (h[0][0], h[0][1]) if h else None
fe0 = get(O3, "보험금융비용", 2)
re0 = get(O3, "재보험금융비용", 2)
orig[19] = (-(fe0[0][0] + re0[0][0]), None)
orig[18] = (orig[17][0] - orig[19][0], None)
orig[32] = (orig[25][0] - sum(orig[i][0] for i in (26, 27, 28, 29, 30)), None)
oc_bad = [(it, L[("2023.3Q", it)]["값"], orig[it][0]) for it in sorted(orig) if orig[it] and abs(L[("2023.3Q", it)]["값"] - orig[it][0]) > 1e-9]
say("V3: master 2023.3Q vs ORIGINAL FY2023_Q3 print (백만원) mismatches: %s ; orig unit header: %s" % (oc_bad, [h for h in ohdr if "단위" in h]))
res["master_eq_original_mismatches"] = oc_bad
res["orig_unit_header"] = [h for h in ohdr if "단위" in h]

fs = json.loads((ROOT / "data/dart/_fs_api_cache/00909349_2024_11014_OFS.json").read_text(encoding="utf-8"))
byname = {}
for a_ in fs["list"]:
    if a_.get("sj_div") in ("IS", "CIS"):
        byname.setdefault(a_["account_nm"], []).append(a_)
fsd = {}
for it, lab in LABEL.items():
    lst = byname.get(lab, [])
    if len(lst) == 1:
        fsd[it] = float(lst[0]["frmtrm_add_amount"]) / 1e6
    else:
        fsd[it] = ("COUNT", len(lst))
fs_bad = {it: (fsd[it], mine[it][0]) for it in fsd if isinstance(fsd[it], tuple) or abs(fsd[it] - mine[it][0]) > 5e-6}
say("V4: FS-API (OFS, FY2024 Q3, frmtrm_add) vs my XML read: mismatches/ambiguous: %s ; items covered %s" % (fs_bad, sorted(fsd)))
res["fsapi_mismatch"] = {str(k): v for k, v in fs_bad.items()}


def idn(v, tag):
    r = {
        "I1 20=1+17": v[20] - (v[1] + v[17]),
        "I2 |22-24|-|23|": abs(v[22] - v[24]) - abs(v[23]),
        "I2b 22=20+21": v[22] - (v[20] + v[21]),
        "I3 31=24+25": v[31] - (v[24] + v[25]),
        "I4 25=26..30+32": v[25] - sum(v[i] for i in (26, 27, 28, 29, 30, 32)),
        "I5 17=18+19": v[17] - (v[18] + v[19]),
        "I6 LOB 1=2+13+14+15-16": v[1] - (v[2] + v[13] + v[14] + v[15] - v[16]),
        "I7a 2=3+8": v[2] - (v[3] + v[8]),
        "I7b 3=4+5+6+7": v[3] - (v[4] + v[5] + v[6] + v[7]),
        "I7c 8=9+10+11+12": v[8] - (v[9] + v[10] + v[11] + v[12]),
    }
    say("closure %s: %s" % (tag, {k: round(x, 6) for k, x in r.items()}))
    return {k: round(x, 6) for k, x in r.items()}


old_v = {it: L[("2023.3Q", it)]["값"] for it in range(1, 33)}


def merged(items):
    v = dict(old_v)
    for c in plan["cells"]:
        if c["item"] in items:
            v[c["item"]] = c["new"]
    return v


res["closure_before"] = idn(old_v, "master-before")
res["closure_after_18"] = idn(merged(planned), "merged-after(18 cells)")
res["closure_after_census8"] = idn(merged(census8), "merged-after(census8)")
res["closure_after_restated7"] = idn(merged([17, 18, 20, 22, 23, 24, 31]), "merged-after(restated7)")

g = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
gold_hits = [x for x in g.get("set", []) if x.get("원보험사코드") == "KR0104"]
nd = [x for x in (g.get("null_dangi") or {}).get("cells", []) if x[0] == "KR0104"]
sd = [x for x in (g.get("set_dangi") or {}).get("cells", []) if x[0] == "KR0104"]
say("gold: set cells for KR0104 = %d ; null_dangi = %d ; set_dangi = %d" % (len(gold_hits), len(nd), len(sd)))
res["gold_KR0104"] = {"set": len(gold_hits), "null_dangi": len(nd), "set_dangi": len(sd)}

qs = sorted({q for (q, i) in L})
ytd_old = {i: {q: L[(q, i)]["값"] for q in qs if (q, i) in L} for i in range(1, 33)}
ytd_new = {i: dict(ytd_old[i]) for i in range(1, 33)}
for c in plan["cells"]:
    ytd_new[c["item"]][c["quarter"]] = c["new"]
chg = []
for i in range(1, 33):
    for q in qs:
        cur_old = L[(q, i)].get("값_당분기")
        fb = BRM._flow_dangi(ytd_old[i], q) if ytd_old[i].get(q) is not None else None
        fa = BRM._flow_dangi(ytd_new[i], q) if ytd_new[i].get(q) is not None else None
        if (fb != fa) or (fb != cur_old):
            chg.append({"quarter": q, "item": i, "live_dangi": cur_old, "fresh_before": fb, "fresh_after": fa})
res["dangi_diff_cells"] = chg
say("V6: quarterly cells where live != fresh_before or fresh_before != fresh_after: %d" % len(chg))
for x in chg:
    say("   %s i%2d live=%s fresh_before=%s fresh_after=%s" % (x["quarter"], x["item"], x["live_dangi"], x["fresh_before"], x["fresh_after"]))

seam = {}
for it in (16, 22, 23, 24):
    h3 = get(F3, LABEL[it], 3)
    h2 = get(F2, {23: "법인세비용", 24: "반기순이익"}.get(it, LABEL[it]), 4)
    seam[it] = {"three_month_mn": h3[0][0] / 1e6, "line": h3[0][1], "printed": h3[0][2], "six_month_prior_cum_F2_mn": h2[0][0] / 1e6, "line_F2": h2[0][1],
                "nine_minus_six": round(mine[it][0] - h2[0][0] / 1e6, 6), "ok": abs(mine[it][0] - h2[0][0] / 1e6 - h3[0][0] / 1e6) < 5e-5}
res["seam_3m"] = {str(k): v for k, v in seam.items()}
say("seam 3M: %s" % json.dumps(seam, ensure_ascii=False))
ps = {(s["quarter"], s["item"]): s for s in plan["seam_cells"]}
res["seam_vs_plan"] = {"%s|%s" % k: {"plan_value": s["proposed_value"], "mine": seam[k[1]]["three_month_mn"],
                                     "ok": abs(s["proposed_value"] - seam[k[1]]["three_month_mn"]) < 5e-6, "proposed": s["proposed"]} for k, s in ps.items()}
say("seam vs plan: %s" % res["seam_vs_plan"])
(HERE / "KR0104_verify.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")
(HERE / "KR0104_verify.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("done", len(out))
