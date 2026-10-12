"""Read-only independent re-derivation of the Meritz KR0001 2023.3Q PL leg items 2..14 from the PRINTED 별도 prior-period '(4) 보험손익 상세내역' table (FY2024_Q3 filing).
Own positional parse ('-' = 0). 별도 table = the LAST table with that caption whose header has no 해외 column and whose sub-caption is <전분기>."""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xmltab as X
ROOT = X.ROOT
xp = ROOT / "data/dart/FY2024_Q3/raw/KR0001_메리츠화재해상보험/20241114001986.xml"
tabs = X.load_tables(str(xp))
def norm(s): return re.sub(r"\s+", "", s or "")
def num(c):
    v = X.printed_to_float(c); return 0.0 if v is None else v
cands = []
for t in tabs:
    cap = " ".join(t.captions)
    h = [norm(c) for c in t.rows[0].cells] if t.rows and t.rows[0].cells else []
    if "(4)보험손익상세내역" in norm(cap) and h[:1] == ["구분"] and "국내" in h:
        cands.append(t)
print("candidates:", [(t.index, t.line, [norm(c) for c in t.rows[0].cells], t.captions[-1][:12]) for t in cands])
prior = [t for t in cands if "전" in norm(t.captions[-1]) and "당" not in norm(t.captions[-1])]
print("prior:", [(t.index, t.line) for t in prior])
t = [x for x in prior if "해외" not in "".join(norm(c) for c in x.rows[0].cells)][-1]       # separate basis = no overseas column
print("selected separate prior table", t.index, "line", t.line, "hdr", t.rows[0].cells)
rows = [(norm(r.cells[0]), r.cells, r.line) for r in t.rows if r.cells]
def sect(name_start, name_end):
    ks = [i for i, (lab, c, l) in enumerate(rows) if lab == name_start]
    ke = [i for i, (lab, c, l) in enumerate(rows) if lab == name_end] if name_end else [len(rows)]
    return rows[ks[0]: (ke[0] if ke else len(rows))]
rev = sect("보험수익", "보험서비스비용"); cost = sect("보험서비스비용", "재보험수익"); rerev = sect("재보험수익", "재보험비용"); recost = sect("재보험비용", "총보험서비스결과")
J = 2   # 장기 누적 = second value cell (3개월, 누적)
def pick(rs, *names):
    for lab, cells, line in rs:
        if any(norm(n) == lab for n in names):
            return num(cells[J]), cells[J], line
    return None
csm = pick(rev, "당기손익으로 인식한 보험계약마진 금액"); ra = pick(rev, "위험해제에 따른 위험조정 변동"); rev_exp = pick(rev, "예상보험금 및 보험서비스비용")
cost_act = pick(cost, "보험금 및 보험서비스비용"); re_rev = pick(rerev, "회수가능 보험금 및 보험서비스비용")
re_exp = pick(recost, "회수예상 보험금 및 보험서비스비용"); re_csm = pick(recost, "당기손익으로 인식한 보험계약마진 금액"); re_ra = pick(recost, "위험해제에 따른 위험조정 변동")
tot = {k: pick(rows, v) for k, v in (("rev", "총 보험수익"), ("cost", "총 보험서비스비용"), ("rerev", "총 재보험수익"), ("recost", "총 재보험비용"))}
res = [r for r in rows if r[0] == "총보험서비스결과"][0]
it = {4: abs(csm[0]), 5: abs(ra[0]), 6: abs(rev_exp[0]) - abs(cost_act[0]), 9: -abs(re_csm[0]), 10: -abs(re_ra[0]), 11: abs(re_rev[0]) - abs(re_exp[0])}
it[3] = tot["rev"][0] - tot["cost"][0]; it[8] = tot["rerev"][0] - tot["recost"][0]; it[2] = it[3] + it[8]
it[7] = it[3] - (it[4] + it[5] + it[6]); it[12] = it[8] - (it[9] + it[10] + it[11])
cells = res[1]
it[13] = num(cells[6]); it[14] = num(cells[8]) - num(cells[2]) - it[13]
plan = json.load(open(HERE / "plan_diff.json", encoding="utf-8"))
pb = {c["item"]: c for c in plan["PL"] if c["block"] == "KR0001|2023.3Q"}
live = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in json.load(open(ROOT / "PL_breakdown.json", encoding="utf-8"))}
for n in sorted(it):
    p = pb.get(n)
    lv = live.get(("KR0001", "2023.3Q", n))
    print(f"item {n:>2} derived {it[n]:>12,.1f} | plan new {p['new'] if p else '-':>12} {'OK' if p and abs(it[n]-p['new'])<=1.01 else ('(not in plan; live %s %s)' % (lv, 'same' if lv is not None and abs(it[n]-lv)<=1.01 else 'DIFF')) if not p else 'DIFF'}")
print("tokens:", {"csm": csm, "ra": ra, "rev_exp": rev_exp, "cost_act": cost_act, "re_rev": re_rev, "re_exp": re_exp, "re_csm": re_csm, "re_ra": re_ra, **{f'tot_{k}': v for k, v in tot.items()}, "result_row_line": res[2]})

import json as _json
_out = {"xml": str(xp.relative_to(ROOT)).replace(chr(92), "/"), "table": t.index, "tline": t.line,
        "items": {str(k): v for k, v in it.items()},
        "tokens": {"csm": csm, "ra": ra, "rev_exp": rev_exp, "cost_act": cost_act, "re_rev": re_rev, "re_exp": re_exp, "re_csm": re_csm, "re_ra": re_ra,
                   **{f"tot_{k}": v for k, v in tot.items()}, "result_row_line": res[2]}}
(HERE / "evidence_pl_meritz.json").write_text(_json.dumps(_out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
