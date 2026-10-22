"""c2: sum the per-product CSM roll-forward tables (유배당/무배당/변액 ...) of a filing's SEPARATE section for the CURRENT and PRIOR period.
usage: c2_csm_product_tables.py <code> <FY_Q> <start_line> <end_line> [unit_div=100]   (separate-section line range from c1)
Reads the 보험계약마진 columns (공정가치법 + 그 외 계약) of each table: opening, 신계약, 이자(당기손익 인식분 inside 보험금융손익), 상각, closing. READ-ONLY.
Output (억원 = 백만원/100) -> c2_<code>_<fy>.txt/.json"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M

sys.stdout.reconfigure(encoding="utf-8")
code, fy = sys.argv[1], sys.argv[2]
s0, e0 = int(sys.argv[3]), int(sys.argv[4])
div = float(sys.argv[5]) if len(sys.argv) > 5 else 100.0
path = [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
lines = M.read_lines(path)
res = []
txt = [f"##### {M.rel(path)} separate range L{s0}-L{e0}"]
for t in M.iter_tables(lines):
    if not (s0 <= t["start"] <= e0):
        continue
    labels = [M.norm_label(r["cells"][0]["text"]) for r in t["rows"] if r["cells"]]
    if not (any(l.startswith("기초") for l in labels) and any(l.startswith("기말") for l in labels) and "보험계약마진" in " ".join(labels) + t["caption"]):
        # header row is inside table; look for 보험계약마진 in any cell text
        blob = " ".join(c["text"] for r in t["rows"][:3] for c in r["cells"])
        if "보험계약마진" not in blob:
            continue
    rec = {"start": t["start"], "end": t["end"], "caption": t["caption"], "rows": {}}
    for r in t["rows"]:
        if not r["cells"]:
            continue
        lab = M.norm_label(r["cells"][0]["text"])
        nums = r["cells"][1:]            # positional: '-' placeholders stay (val None -> 0)
        if len(nums) == 7:
            csm = (nums[4]["val"] or 0) + (nums[5]["val"] or 0)
            rec["rows"].setdefault(lab, []).append({"tr": r["tr_line"], "csm_fv": nums[4]["val"], "csm_oth": nums[5]["val"], "csm": csm,
                                                   "line_fv": nums[4]["line"], "line_oth": nums[5]["line"], "total": nums[6]["val"]})
    res.append(rec)
    txt.append(f"--- L{t['start']}-L{t['end']} caption[{t['caption_line']}]={t['caption'][:60]!r}")
    for lab, items in rec["rows"].items():
        for it in items:
            txt.append(f"    R{it['tr']} {lab[:34]:<36} CSM-FV={it['csm_fv']} CSM-oth={it['csm_oth']} sum={it['csm']}  @L{it['line_fv']},L{it['line_oth']}")
M.MEASURE.joinpath(f"c2_{code}_{fy}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath(f"c2_{code}_{fy}.txt").write_text("\n".join(txt), encoding="utf-8")
print(len(res), "tables")
