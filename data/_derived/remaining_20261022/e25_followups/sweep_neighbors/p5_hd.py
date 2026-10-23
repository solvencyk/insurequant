import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
import e23_read as E, e21_t2 as T, e21_raw as W
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
res = []
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    fy = E.M.later_fy(q); path = T.main_path("KR0009", fy)
    lines, s0, tabs = E.tables_sep(path)
    for t, rows in tabs:
        cap = E.nl(t["caption"] or "")
        if not re.match(E.HD_PRIOR_CAP[q[5]], cap): continue
        hdr = E.nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        if not hdr.startswith("구분장기자동차일반합계"): continue
        unit = T.find_unit(lines, t, span=2500)
        sect = "dir"
        for r in rows:
            lab = E.lab(r)
            if lab in ("재보험수익", "재보험비용", "출재보험서비스수익", "출재보험서비스비용"): sect = "re"
            n = W.numeric_cells(r)
            for pat, item_d, item_r in (("보험계약마진상각", 4, 9), ("위험조정변동", 5, 10)):
                if lab == pat and n:
                    it = item_d if sect == "dir" else item_r
                    v = abs(n[0][0]) / T.UNIT_DIV[unit] * (1 if it in (4, 5) else -1)
                    m = pl.get(("KR0009", str(it), q))
                    res.append((q, it, sect, m, round(v, 3), None if m is None else round(v - m, 3), n[0][1], t["start"]))
for r in res: print(r)
json.dump(res, open("p5_hd.json", "w", encoding="utf-8"), ensure_ascii=False)
# second occurrence = reinsurance section
seen = {}
for q, it, sect, m, v, d, ln, ts in res:
    k = (q, it)
    seen[k] = seen.get(k, 0) + 1
    if seen[k] == 2:
        it2 = 9 if it == 4 else 10
        mm = pl.get(("KR0009", str(it2), q))
        print("RE", q, it2, mm, -abs(v), None if mm is None else round(-abs(v) - mm, 3), ln)
