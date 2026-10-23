# -*- coding: utf-8 -*-
"""Custom reader KR0079 for 2024.2Q-2024.4Q (FY2025_Q2..Q4 filings, amounts in won, 5 products x 5 component columns in ONE table; twin tables cur/prior).
item 4 = |sum of all columns of the row '...보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진'| (issued contracts table), 5 = |sum of the row '위험조정 변동분'|;
9 / 10 = same two rows in the 보유 재보험계약 table, negative sign.  Calibration: the current table must reproduce the master of quarter+4 (sum within 1.5 mn)."""
import json, sys, re
sys.argv = [sys.argv[0], "__lib__"]
from n00_lib import *

CSM_P = "서비스의이전으로당기손익에인식한보험계약마진"
RA_P = "위험조정변동분"


def find(path):
    lines, s0, tabs = s2lib.tables_sep2(path)
    res = {"dir": [], "re": []}
    for t, rows in tabs:
        hdr = E.nl(" ".join(c["text"] for r in rows[:6] for c in r["cells"]))
        csm = ra = None
        for r in rows:
            lab, nums = split_row(r)
            if len(nums) < 20:
                continue
            if CSM_P in lab and csm is None:
                csm = (nums, r["tr_line"])
            if lab.startswith(RA_P) and ra is None:
                ra = (nums, r["tr_line"])
        if csm is None and ra is None:
            continue
        kind = "re" if "보유재보험계약" in hdr[:80] else ("dir" if "발행한보험계약" in hdr[:80] else None)
        if kind:
            res[kind].append(dict(start=t["start"], csm=csm, ra=ra, unit=T.find_unit(lines, t, span=2500)))
    return res


UDIV = {"원": 1e6, "천원": 1e3, "백만원": 1.0}
cells = []
for q in ("2024.2Q", "2024.3Q", "2024.4Q"):
    c = "KR0079"
    fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
    mq = f"{int(q[:4]) + 1}.{q[5:]}"
    path = T.main_path(c, fy)
    filing = str(path).replace("\\", "/").split("insurequant/")[-1]
    res = find(path)
    print(q, {k: [(x["start"], x["unit"], bool(x["csm"]), bool(x["ra"])) for x in v] for k, v in res.items()})
    for kind, item_csm, item_ra, sg in (("dir", "4", "5", 1), ("re", "9", "10", -1)):
        tl = res[kind]
        for it, key in ((item_csm, "csm"), (item_ra, "ra")):
            vals = []
            for x in tl:
                if x[key] is None:
                    vals.append(None)
                    continue
                vals.append((sum(n[0] for n in x[key][0]) / UDIV.get(x["unit"], float("nan")), x[key][0][0][1], x[key][1], x["start"]))
            vv = [v for v in vals if v]
            m_cur = pl.get((c, it, mq))
            ok_idx = [i for i, v in enumerate(vv) if m_cur is not None and abs(abs(v[0]) - abs(m_cur)) <= 1.5]
            print("   ", it, "values", [round(v[0], 1) for v in vv], "master q+4", m_cur, "cal idx", ok_idx)
            if ok_idx and ok_idx[0] + 1 < len(vv):
                p = vv[ok_idx[0] + 1]
                cells.append(dict(company=c, quarter=q, item=it, master=pl.get((c, it, q)), latest=sg * abs(p[0]), filing=filing, line=f"cells of row at tr L{p[2]} (first cell L{p[1]}), table@L{p[3]}",
                                  source="custom_kr0079b", confidence=("high" if it == "4" else "low"),
                                  note=f"sum of all 25 columns of the row; current table@L{vv[ok_idx[0]][3]} reproduces master {mq} = {m_cur}" + ("" if it == "4" else "; LOW: the same one-row RA definition fails calibration for 2025.4Q (reader 37,616 vs master 43,953), so a second RA row may exist")))
json.dump(dict(cells=cells), open(S2 + "x05_kr0079.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for x in cells:
    print(x["quarter"], x["item"], x["master"], round(x["latest"], 1))
