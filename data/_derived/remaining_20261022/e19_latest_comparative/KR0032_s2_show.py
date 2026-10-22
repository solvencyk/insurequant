# -*- coding: utf-8 -*-
import json
from pathlib import Path
H = Path(__file__).resolve().parent
p = json.loads((H / "plan_KR0032.json").read_text(encoding="utf-8"))
v = p["verification"]
L = []
L.append(json.dumps(v["fy2023_ytd_master_vs_fy2024_filings_prior"]["summary"], ensure_ascii=False, indent=1))
for r in v["fy2023_ytd_master_vs_fy2024_filings_prior"]["rows"]:
    L.append(f"{r['quarter']} i{r['item']:>2} master={r['master']} later_print={r['later_print']} diff={r.get('diff')} L{r['xml_line']} {r['filing']}")
L.append("--- statements")
for fy, s in v["statements"].items():
    L.append(f"{fy} {s['file']} title L{s['title_line']} end L{s['end_line']} unit {s['unit']} ctx {s['contexts']} hdr={s.get('col_header_row')} per={s.get('period_header_row')}")
L.append("--- preexisting mismatch " + json.dumps(v["dangi_model_mismatch_vs_live_master"]))
(H / "KR0032_s2_show.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
