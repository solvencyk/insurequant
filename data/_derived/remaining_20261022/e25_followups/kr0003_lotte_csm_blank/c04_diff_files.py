# -*- coding: utf-8 -*-
"""READ-ONLY structural diff of CSM_waterfall.json and data/_gold/user_csm_cells.json: backup_before_apply (OLD) vs the repo (NEW)."""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
R = Path("C:/Users/sangwook.cho/Desktop/insurequant")
B = R / "data/_derived/remaining_20261022/e25_followups/backup_before_apply"
fails = []
def chk(c, m):
    print(("PASS  " if c else "FAIL  ") + m)
    if not c: fails.append(m)
o = json.loads((B / "CSM_waterfall.json").read_text(encoding="utf-8")); n = json.loads((R / "CSM_waterfall.json").read_text(encoding="utf-8"))
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
chk([key(r) for r in o] == [key(r) for r in n], f"CSM_waterfall.json: same {len(o)} rows in the same order")
fld = [(key(a), k) for a, b in zip(o, n) for k in set(a) | set(b) if k != "값_당분기" and a.get(k) != b.get(k)]
chk(not fld, f"CSM_waterfall.json: no field other than 값_당분기 changed ({fld[:3]})")
ch = [(key(a), a.get("값_당분기"), b.get("값_당분기")) for a, b in zip(o, n) if a.get("값_당분기") != b.get("값_당분기")]
chk(sorted(k for k, _, _ in ch) == [("KR0003", 3, "2023.4Q"), ("KR0003", 4, "2023.4Q"), ("KR0003", 5, "2023.4Q")], f"CSM_waterfall.json: 값_당분기 changed on exactly the three planned cells: {ch}")
chk(all(b is None and a is not None for _, a, b in ch), "CSM_waterfall.json: numeric -> None on each")
go = json.loads((B / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8")); gn = json.loads((R / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
chk([k for k in gn if k != "null_dangi"] == list(go.keys()), f"user_csm_cells.json: old keys in the same order {list(go.keys())}")
chk(all(go[k] == gn[k] for k in go if k != "_doc"), "user_csm_cells.json: every old key's content identical (set, exclude_companies, _doc_e23_*)")
chk(gn["_doc"].startswith(go["_doc"]) and "null_dangi.cells" in gn["_doc"][len(go["_doc"]):], "user_csm_cells.json: the top-level _doc only gained the appended null_dangi sentence")
chk(gn["null_dangi"]["cells"] == [["KR0003", "2023.4Q", 3], ["KR0003", "2023.4Q", 4], ["KR0003", "2023.4Q", 5]], "user_csm_cells.json: null_dangi.cells = the three planned cells")
chk(len(gn["set"]) == len(go["set"]) == 417, "user_csm_cells.json: set unchanged (417)")
print("RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL")
sys.exit(1 if fails else 0)
