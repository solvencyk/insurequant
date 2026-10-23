# -*- coding: utf-8 -*-
"""KR0099 control (read-only): the CSM vector rules of csm_kblife applied to the CURRENT-period table of the ORIGINAL FY2023 Q1 / Q2 / Q3 / Q4 filings and of the FY2024 filings must
reproduce the live CSM master (V0 for FY2023 Q1-Q3 originals) -- proves the row / column rules are the master's definitions."""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife")
import e23_read as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
T, W, M, nl = X.T, X.W, X.M, X.nl
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
csm = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(ROOT + "/CSM_waterfall.json", encoding="utf-8").read()) if r["원보험사코드"] == "KR0099"}
RULES = {
    1: lambda x: x == "기초순장부금액",
    2: lambda x: x == "신계약효과",
    3: lambda x: x == "보험금융손익(PL)",
    4: lambda x: x == "보험계약마진을조정하는추정치변동",
    5: lambda x: x == "서비스제공에따른보험계약마진변동",
    6: lambda x: re.match(r"^(분기말|반기말|기말)순장부금액$", x) is not None,
}
CAP = "보험료배분접근법을적용하지않은보험계약부채(자산)의측정요소별변동내역"
for fy, q in (("FY2023_Q1", "2023.1Q"), ("FY2023_Q2", "2023.2Q"), ("FY2023_Q3", "2023.3Q"), ("FY2023_Q4", "2023.4Q"), ("FY2024_Q1", "2024.1Q"), ("FY2024_Q2", "2024.2Q"), ("FY2024_Q3", "2024.3Q"), ("FY2024_Q4", "2024.4Q")):
    path = T.main_path("KR0099", fy)
    lines, s0, tabs = X.tables_sep(path)
    hits = []
    for t, rows in tabs:
        cap = nl(t["caption"] or "")
        if CAP not in cap:
            continue
        hdr = nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        labs = [X.lab(r) for r in rows]
        if re.search(r"구분(당분기|당반기|당기)", hdr) and "신계약효과" in labs:
            hits.append((t, rows))
    out = []
    for t, rows in hits[:3]:
        unit = T.find_unit(lines, t, span=2500)
        vec = []
        for it in range(1, 7):
            h = [r for r in rows if RULES[it](X.lab(r))]
            if not h:
                vec.append(None)
                continue
            n = W.numeric_cells(h[0])
            vec.append(round(n[2][0] / 100.0 if unit == "백만원" else float("nan"), 2))
        out.append((t["start"], unit, vec))
    live = [csm.get(("KR0099", i, q)) for i in range(1, 7)]
    print(fy, q, "master", live)
    for st, unit, vec in out:
        print("    cur-table@L%d unit=%s %s" % (st, unit, vec))
