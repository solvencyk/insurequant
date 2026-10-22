# -*- coding: utf-8 -*-
"""v30: independent headline read (separate statement, next-year filing prior columns) for 9 companies x 8 quarters.
Compares master cumulative + stored single-quarter with printed prior cum / prior 3-month."""
import sys, json, re, glob, os, collections
sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R = "C:/Users/sangwook.cho/Desktop/insurequant/"; HERE = R + "data/_derived/remaining_20261022/e21_ready25/verify/"
NINE = ["KR0104","KR0083","KR0070","KR0079","KR0010","KR0099","KR0003","KR0001","KR0068"]
QS = ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q"]
def load(p):
    d = {}
    for r in json.load(open(p, encoding="utf-8")): d[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
    return d
new = load(R + "PL_breakdown.json"); old = load(HERE + "head/PL_breakdown.json")
LAB = {  # item -> regex on normalized label (first match inside separate statement table)
 1: r"^(Ⅰ\.|I\.)?(보험손익|보험서비스손익|보험영업손익)$",
 17: r"^(Ⅱ\.|II\.)?(투자손익|투자서비스손익)$",
 20: r"^(Ⅲ\.|III\.)?영업이익(\(손실\))?$",
 22: r"^(Ⅴ\.|V\.|VII\.|Ⅶ\.)?법인세(비용)?차감전(순)?이익(\(손실\))?$",
 24: r"^(Ⅶ\.|VII\.|Ⅷ\.|VIII\.|Ⅸ\.|IX\.)?(당기|분기|반기)순(이익|손익)(\(손실\))?$",
 25: r"^(Ⅷ\.|VIII\.|Ⅸ\.|IX\.)?기타포괄(손익|이익)(\(손실\))?$",
 31: r"^(Ⅸ\.|IX\.|Ⅹ\.)?((당기|분기|반기)\s*)?총포괄(손익|이익)(\(손실\))?$",
}
def nlab(s): return re.sub(r"\s+", "", s)
def main_file(code, fy, q):
    d = glob.glob(R + f"data/dart/FY{fy}_Q{q}/raw/{code}*")
    fs = []
    for dd in d:
        fs += glob.glob(dd + "/*.xml") + glob.glob(dd + "/xml/*.xml")
    fs = [f for f in fs if not f.endswith("_00760.xml")]
    if not fs: return None
    return max(fs, key=os.path.getsize)
def sep_statement_tables(doc):
    out = []
    for t in doc.tables:
        labs = [nlab(r["cells"][0]["t"]) for r in t["rows"] if r["cells"]]
        if sum(1 for l in labs if re.search(r"보험손익|투자손익|영업이익|순이익|순손익|보험서비스손익|보험영업손익", l)) >= 3 and len(t["rows"]) > 15:
            bt = None
            for pos, ln, txt in reversed([x for x in doc.titles if x[0] < t["pos"]]):
                if "재무제표" in txt and "요약" not in txt: bt = txt; break
            if bt and "연결" not in bt and "주석" not in bt:
                out.append(t)
    return out
def header_info(t):
    hdr = " ".join(c["t"] for r in t["rows"][:5] for c in r["cells"])
    per = len(set(re.findall(r"제\s*\d+\s*\(?[당전]?\)?\s*기", hdr)))
    has_cum = "누적" in hdr.replace(" ", "") or "누 적" in hdr
    return per, has_cum
res = {}
for code in NINE:
    for q in QS:
        y, qq = int(q[:4]), int(q[5])
        f = main_file(code, y + 1, qq)
        if not f: res[(code, q)] = {"err": "no next-year filing"}; continue
        doc = xmlrd.get(f)
        tabs = sep_statement_tables(doc)
        if not tabs: res[(code, q)] = {"err": "no separate statement table", "file": f}; continue
        t = tabs[0]
        per, has_cum = header_info(t)
        unit = xmlrd.unit_div(doc.unit_before(t))
        rec = {"file": f.split("/")[-1], "table": t["start"], "unit": doc.unit_before(t), "per": per, "has_cum": has_cum, "items": {}}
        for it, rx in LAB.items():
            for r in t["rows"]:
                cs = [c["t"] for c in r["cells"]]
                if cs and re.search(rx, nlab(cs[0])):
                    nums = [xmlrd.parse_num(x) for x in cs[1:]]
                    nums = [(v if v is not None else (0.0 if x.strip() in ("-","0") else None)) for v, x in zip(nums, cs[1:])]
                    nums = [v for v, x in zip(nums, cs[1:]) if v is not None and not re.fullmatch(r"\d{1,2}", x.strip())]  # drop 주석 numbers
                    if has_cum and len(nums) >= 4:
                        n4 = nums[-4:]; rec["items"][it] = {"cur3m": n4[0], "curcum": n4[1], "pri3m": n4[2], "pricum": n4[3], "line": r["line"]}
                    elif per >= 2 and len(nums) >= per:
                        n = nums[-per:]
                        rec["items"][it] = {"cur3m": None, "curcum": n[0], "pri3m": None, "pricum": n[1], "line": r["line"]}
                    break
        for it, v in rec["items"].items():
            for k in ("cur3m","curcum","pri3m","pricum"):
                if v[k] is not None and unit: v[k] = v[k] / unit
        res[(code, q)] = rec
json.dump({f"{k[0]}|{k[1]}": v for k, v in res.items()}, open(HERE + "v30_headline.json", "w", encoding="utf-8"), ensure_ascii=False)
# compare
rows = []
for (code, q), rec in sorted(res.items()):
    if "err" in rec:
        print(code, q, rec["err"]); continue
    for it, v in sorted(rec["items"].items()):
        m = new.get((code, q, it)); h = old.get((code, q, it))
        mv = None if m is None else m["값"]; hv = None if h is None else h["값"]
        pv = v["pricum"]
        ok = mv is not None and pv is not None and abs(mv - pv) <= max(1.001, 1e-6 * abs(pv))
        ok_old = hv is not None and pv is not None and abs(hv - pv) <= max(1.001, 1e-6 * abs(pv))
        rows.append((code, q, it, mv, hv, pv, ok, ok_old))
bad = [r for r in rows if not r[6]]
print("headline cells compared:", len(rows), "master==printed prior cum:", sum(1 for r in rows if r[6]), "NOT:", len(bad))
for r in bad: print("  NOT-EQ", r)
json.dump(rows, open(HERE + "v30_rows.json", "w", encoding="utf-8"), ensure_ascii=False)
