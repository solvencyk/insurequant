"""c3: 미래에셋생명-style per-product CSM tables where 당기 and 전기 are ROW BLOCKS inside one table (marker rows '당기' / '전기'):
sum the CSM 소계 column over the issued-contract product tables for the chosen period block.  READ-ONLY.
usage: c3_mirae_product_csm.py <code> <FY_Q> [issued_tables=5]  -> c3_<code>_<fy>.json/.txt  (억원 = 백만원/100)"""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
import stmtlib as S

sys.stdout.reconfigure(encoding="utf-8")
code, fy = sys.argv[1], sys.argv[2]
n_issued = int(sys.argv[3]) if len(sys.argv) > 3 else 5
path = [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
lines = M.read_lines(path)
note_from = None
for ln, tt in S.titles(lines):
    if re.match(r"^\d+\.재무제표주석$", re.sub(r"\s+", "", tt)):
        note_from = ln
tabs = []
for t in M.iter_tables(lines):
    if note_from and t["start"] < note_from:
        continue
    labs = [M.norm_label(r["cells"][0]["text"]) for r in t["rows"] if r["cells"]]
    hdr = " ".join(c["text"] for r in t["rows"][:6] for c in r["cells"])
    if len(t["rows"]) >= 38 and "보험계약마진" in hdr and "수정소급법" in hdr and any(l.startswith("기초잔액") for l in labs) and any(l.startswith("기말잔액") for l in labs) \
            and any(l in ("당기", "당분기", "당반기") for l in labs) and any(l in ("전기", "전분기", "전반기") for l in labs):
        tabs.append(t)
issued = tabs[:n_issued]
res = {"file": M.rel(path), "tables": [(t["start"], t["end"], t["caption"][:30]) for t in tabs]}
txt = [f"##### {M.rel(path)}  note_from={note_from}  tables found={len(tabs)} issued used={[t['start'] for t in issued]}"]
tot = {"cur": {}, "prior": {}}
for period, marks in (("cur", ("당기", "당분기", "당반기")), ("prior", ("전기", "전분기", "전반기"))):
    for t in issued:
        blk = None
        out = {}
        for r in t["rows"]:
            c0 = M.norm_label(r["cells"][0]["text"]) if r["cells"] else ""
            if c0 in ("당기", "당분기", "당반기"):
                blk = "cur"
            elif c0 in ("전기", "전분기", "전반기"):
                blk = "prior"
            if blk != period:
                continue
            cells = r["cells"]
            lab = " ".join(M.norm_label(c["text"]) for c in cells[:3])
            nums = cells[-7:]
            if len(cells) < 7:
                continue
            def csm(c):
                return nums[5]["val"] or 0.0
            key = None
            if "기초잔액" in lab:
                key = "open"
            elif "처음인식한계약의효과" in lab:
                key = "new"
            elif "당기손익인식보험금융손익" in lab:
                key = "int"
            elif "보험계약마진의당기인식분" in lab:
                key = "amort"
            elif "기말잔액" in lab:
                key = "close"
            if key and key not in out:
                out[key] = (nums[5]["val"] or 0.0, nums[5]["line"])
        for k, (v, ln) in out.items():
            tot[period].setdefault(k, []).append((t["start"], v, ln))
for period in ("cur", "prior"):
    d = tot[period]
    s = {k: sum(x[1] for x in v) for k, v in d.items()}
    if all(k in s for k in ("open", "new", "int", "amort", "close")):
        s["assump"] = s["close"] - (s["open"] + s["new"] + s["int"] + s["amort"])
        eok = [round(s[k] / 100, 1) for k in ("open", "new", "int", "assump", "amort", "close")]
    else:
        eok = None
    res[period] = {"sum_mn": s, "eok_1to6": eok, "by_table": {k: v for k, v in d.items()}}
    txt.append(f"  {period}: sum(백만원)={s}  -> 억원 [기초,신계약,이자,가정,상각,기말]={eok}")
    for k in ("open", "new", "int", "amort", "close"):
        txt.append(f"      {k}: " + ", ".join(f"T{a}:{b:,.0f}@L{c}" for a, b, c in d.get(k, [])))
M.MEASURE.joinpath(f"c3_{code}_{fy}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath(f"c3_{code}_{fy}.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt))
