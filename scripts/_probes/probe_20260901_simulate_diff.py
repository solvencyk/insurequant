# -*- coding: utf-8 -*-
"""Read-only simulation: run _process in-memory (never writes JSON_PATH) and
report exactly which (code, quarter, item) rows would newly be inserted."""
import sys, io, json
sys.path.insert(0, "scripts")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fill_period_to_disclosure as F

fields = F._fields()
before = json.loads(F.JSON_PATH.read_text(encoding="utf-8"))
rows = list(before)
before_keys = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])) for r in rows}

periods = sorted(x.name for x in F.MD_INBOX.glob("FY*_Q?") if x.is_dir())
ins, upd, rem = F._process(rows, periods, True, fields, target_quarter=None)
print(f"ins={ins} upd={upd} rem={rem}")

after_keys = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])) for r in rows}
new_keys = after_keys - before_keys
print(f"\nnewly inserted keys: {len(new_keys)}")
for k in sorted(new_keys):
    r = next(rr for rr in rows if (rr["원보험사코드"], rr["공시분기"], str(rr["항목번호"])) == k)
    print(f"  {k}  값={r.get('값')!r}  항목명={r.get('항목명')!r}")
