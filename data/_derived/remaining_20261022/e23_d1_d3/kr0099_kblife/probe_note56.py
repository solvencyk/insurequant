# -*- coding: utf-8 -*-
"""KR0099 probe (read-only): items 5 / 6 / 9 / 10 / 11 source rows of the KB라이프 prior-period 보험영업수익 note (FY2024 Q1/Q2/Q3 filings) vs the master."""
import json
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife")
import e23_read as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
T, W, M, nl = X.T, X.W, X.M, X.nl
master = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open("C:/Users/sangwook.cho/Desktop/insurequant/PL_breakdown.json", encoding="utf-8").read()) if r["원보험사코드"] == "KR0099"}
NEED = ["서비스제공에따른보험계약마진의변동", "위험해제에따른위험조정의변동", "예상보험금및예상보험서비스비용", "실제보험금및실제보험서비스비용", "제공받은서비스의재보험계약마진", "위험해제로인한위험조정의변동", "발생재보험금및재보험서비스비용회수액", "회수예상보험금및보험서비스비용", "총보험수익", "총보험서비스비용", "총재보험수익", "총재보험비용"]
for q in ("2023.1Q", "2023.2Q", "2023.3Q"):
    fy = M.later_fy(q)
    path = T.main_path("KR0099", fy)
    lines, s0, tabs = X.tables_sep(path)
    print("=" * 100)
    print(q, "master 4,5,6,9,10,11 =", [master.get(("KR0099", i, q)) for i in (4, 5, 6, 9, 10, 11)])
    for t, rows in tabs:
        cap = nl(t["caption"] or "")
        if "기타사업비용을제외한" not in cap or "보험영업수익" not in cap:
            continue
        hdr = nl(" ".join(c["text"] for r in rows[:3] for c in r["cells"]))
        which = "PRIOR" if re.search(r"구분(전분기|전반기|전기)", hdr) else "CUR"
        print("-- table@L%d %s" % (t["start"], which))
        for r in rows:
            lb = X.lab(r)
            if lb in NEED:
                cells = [c["text"] for c in r["cells"][1:]]
                print("    %-40s %s" % (lb, cells))
