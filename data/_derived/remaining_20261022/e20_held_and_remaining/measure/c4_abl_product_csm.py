"""c4: ABL-style per-product CSM tables (cols: PV-FCF | RA | CSM | 합계; rows I.기초 / II.(3) 처음 인식 / III.(1) 서비스 제공 CSM 상각 / VI.(1) 당기손익인식 보험금융 /
closing = the unlabeled row before '(1) 보험계약자산').  Sum of the product tables of one period block.  READ-ONLY.
usage: c4_abl_product_csm.py <code> <FY_Q> <file_suffix> <cur_starts_csv> <prior_starts_csv> -> c4_<code>_<fy>.json/.txt (억원)"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M

sys.stdout.reconfigure(encoding="utf-8")
code, fy, suffix = sys.argv[1], sys.argv[2], sys.argv[3]
blocks = {"cur": [int(x) for x in sys.argv[4].split(",")], "prior": [int(x) for x in sys.argv[5].split(",")]}
path = [p for p in M.main_xmls(code, fy) if p.name.endswith(suffix)][0]
lines = M.read_lines(path)
tabs = {t["start"]: t for t in M.iter_tables(lines)}
res, txt = {"file": M.rel(path)}, [f"##### {M.rel(path)}"]
for per, starts in blocks.items():
    tot, cites = {}, {}
    for s in starts:
        t = tabs[s]
        rows = t["rows"]
        def val(r):
            nums = r["cells"][1:]
            return (nums[2]["val"] or 0.0, nums[2]["line"]) if len(nums) >= 3 else (0.0, None)
        close_idx = max(i for i, r in enumerate(rows) if r["cells"] and M.norm_label(r["cells"][0]["text"]).startswith(("(1)보험계약자산", "(1)재보험계약자산")))
        for i, r in enumerate(rows):
            lab = M.norm_label(r["cells"][0]["text"]) if r["cells"] else ""
            key = None
            if lab.startswith("I.기초"):
                key = "open"
            elif lab.startswith("(3)해당기간에처음인식한계약의효과") or lab.startswith("(3)해당기간에처음인식"):
                key = "new"
            elif lab.startswith("(1)서비스제공으로당기손익으로인식된보험"):
                key = "amort"
            elif lab.startswith("(1)당기손익인식보험금융"):
                key = "int"
            elif i == close_idx - 1:
                key = "close"
            if key:
                v, ln = val(r)
                tot[key] = tot.get(key, 0.0) + v
                cites.setdefault(key, []).append((s, v, ln))
    s = tot
    s["assump"] = s["close"] - (s["open"] + s["new"] + s["int"] + s["amort"])
    # sign: 보험금융비용 rows are expenses printed positive -> interest accretion on CSM = + (CSM grows)
    eok = [round(s[k] / 100, 1) for k in ("open", "new", "int", "assump", "amort", "close")]
    res[per] = {"sum_mn": s, "eok_1to6": eok, "cites": cites}
    txt.append(f"  {per}: sum(백만원)={ {k: round(v, 1) for k, v in s.items()} } -> 억원 [기초,신계약,이자,가정,상각,기말]={eok}")
    for k in ("open", "new", "int", "amort", "close"):
        txt.append(f"      {k}: " + ", ".join(f"T{a}:{b:,.0f}@L{c}" for a, b, c in cites.get(k, [])))
M.MEASURE.joinpath(f"c4_{code}_{fy}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath(f"c4_{code}_{fy}.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt))
