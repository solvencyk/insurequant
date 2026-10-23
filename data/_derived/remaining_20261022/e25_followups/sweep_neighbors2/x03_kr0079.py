# -*- coding: utf-8 -*-
"""Custom reader KR0079 (미래에셋생명): product tables (i)사망 ... v)기타 / re: i)사망, ii)사망외) of the 보험수익 / 재보험서비스비용 notes; each table stacks a CURRENT section and a PRIOR section.
Item 4 = sum over product tables of '해당 기간에 서비스의 이전으로 당기손익에 인식한 ...' (합계 = last numeric cell), 5 = '비금융위험에 대한 위험조정의 변동분' (rev tables);
9 / 10 = same two rows of the 재보험서비스비용 tables, sign negative.  Calibration: the current-section sums must reproduce the master of quarter+4."""
import json, sys, re, collections
sys.argv = [sys.argv[0], "__lib__"]
from n00_lib import *

CSM_L = "해당기간에서비스의이전으로당기손익에인식한"
RA_L = "비금융위험에대한위험조정의변동분"


def groups(path):
    lines, s0, tabs = s2lib.tables_sep2(path)
    g = {"rev": [], "re": []}
    for t, rows in tabs:
        hdr = [E.nl(c["text"]) for r in rows[:3] for c in r["cells"]]
        if "구분" in hdr and "보험수익" in hdr and "합계" in hdr and any(E.lab(r).startswith(RA_L) for r in rows):
            g["rev"].append((t, rows))
        elif "구분" in hdr and "재보험서비스비용" in hdr and "합계" in hdr and any(E.lab(r).startswith(RA_L) for r in rows):
            g["re"].append((t, rows))
    return g


def secvals(rows, lab_prefix):
    out = []
    for r in rows:
        if E.lab(r).startswith(lab_prefix):
            cells = [c for c in r["cells"] if isnum(c)]
            if cells:
                c = cells[-1]
                out.append((c["val"] if c["val"] is not None else 0.0, c["line"], r["tr_line"]))
    return out


cells = []
log = []
for q in ("2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"):
    c = "KR0079"
    fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
    mq = f"{int(q[:4]) + 1}.{q[5:]}"
    path = T.main_path(c, fy)
    filing = str(path).replace("\\", "/").split("insurequant/")[-1]
    g = groups(path)
    res = {}
    for kind, lab_items in (("rev", (("4", CSM_L, 1), ("5", RA_L, 1))), ("re", (("9", CSM_L, -1), ("10", RA_L, -1)))):
        for item, pref, sg in lab_items:
            per_table = [secvals(rows, pref) for t, rows in g[kind]]
            nsec = collections.Counter(len(x) for x in per_table)
            res[item] = (per_table, nsec, sg)
    for item, (per_table, nsec, sg) in res.items():
        ns = max(nsec) if nsec else 0
        log.append((q, item, "tables", len(per_table), "sections per table", dict(nsec)))
        if ns < 2:
            continue
        # sections: [cur, prior] when 2 ; [cur3m?, ..] unknown otherwise -> take first = current, last = prior only when ns == 2
        if ns != 2 or len(nsec) != 1:
            continue
        cur = sg * sum(abs(x[0][0]) for x in per_table)
        pri = sg * sum(abs(x[1][0]) for x in per_table)
        m_cur = pl.get((c, item, mq))
        ok = m_cur is not None and abs(abs(cur) - abs(m_cur)) <= 1.5
        log.append((q, item, "cur sum", cur, "master q+4", m_cur, "OK" if ok else "NO_CAL", "prior sum", pri, "master q", pl.get((c, item, q))))
        if ok:
            ln = ",".join(str(x[1][1]) for x in per_table)
            cells.append(dict(company=c, quarter=q, item=item, master=pl.get((c, item, q)), latest=pri, filing=filing, line=ln, source="custom_kr0079", confidence="high",
                              note=f"sum over {len(per_table)} product tables of the prior section (last numeric cell); current sections reproduce master {mq} = {m_cur}"))
for l in log:
    print(*l)
json.dump(dict(cells=cells), open(S2 + "x03_kr0079.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("cells", len(cells))
