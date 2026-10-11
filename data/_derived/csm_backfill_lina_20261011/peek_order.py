# -*- coding: utf-8 -*-
"""Read-only: byte round-trip of the three masters, ordering convention, position of the KR0074 block."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")


def dump(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


for fn in ["CSM_waterfall.json", "CSM_waterfall_provenance.json", "CSM_amortization.json"]:
    raw = (ROOT / fn).read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    print(fn, "bytes", len(raw), "round-trip:", dump(obj) == raw, "| starts", raw[:3], "| CRLF count", raw.count(b"\r\n"), "LF-only", raw.count(b"\n") - raw.count(b"\r\n"))

wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
idx = [i for i, r in enumerate(wf) if r["원보험사코드"] == "KR0074"]
print("waterfall KR0074 row positions", idx[0], "..", idx[-1], "contiguous:", idx == list(range(idx[0], idx[-1] + 1)), "n", len(idx))
print("neighbours: before", wf[idx[0] - 1]["원보험사코드"], wf[idx[0] - 1]["공시분기"], wf[idx[0] - 1]["항목번호"], "| after", wf[idx[-1] + 1]["원보험사코드"], wf[idx[-1] + 1]["공시분기"], wf[idx[-1] + 1]["항목번호"])
print("KR0074 meta:", {k: wf[idx[0]][k] for k in ("원보험사코드", "원수사명", "티커", "생손보여부")})
# is the file sorted by (code, quarter, item)?
keys = [(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in wf]
print("sorted by (code, quarter, item):", keys == sorted(keys))
codes_order = []
for r in wf:
    if not codes_order or codes_order[-1] != r["원보험사코드"]:
        codes_order.append(r["원보험사코드"])
print("code blocks:", len(codes_order), "unique", len(set(codes_order)), "| sorted:", codes_order == sorted(codes_order))
print(codes_order)

am = json.loads((ROOT / "CSM_amortization.json").read_text(encoding="utf-8"))
ia = [i for i, r in enumerate(am) if r["원보험사코드"] == "KR0074"]
print("amort KR0074 positions", ia[0], "..", ia[-1], "n", len(ia), "contiguous:", ia == list(range(ia[0], ia[-1] + 1)))
print("amort sorted by (code, quarter, 경과차년):", [(r["원보험사코드"], r["공시분기"], r["경과차년"]) for r in am] == sorted((r["원보험사코드"], r["공시분기"], r["경과차년"]) for r in am))
print("amort KR0074 meta:", {k: am[ia[0]][k] for k in ("원보험사코드", "원수사명", "티커", "생손보여부")})

pv = json.loads((ROOT / "CSM_waterfall_provenance.json").read_text(encoding="utf-8"))
c = pv["cells"]
print("sidecar cells", len(c), "| order of codes:", [x["company_code"] for x in c][:5], "...", [x["company_code"] for x in c][-3:])
ik = [i for i, x in enumerate(c) if x["company_code"] == "KR0074"]
print("sidecar KR0074 positions", ik, "| neighbours", c[ik[0] - 1], c[ik[-1] + 1])
