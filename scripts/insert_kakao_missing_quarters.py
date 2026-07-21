#!/usr/bin/env python3
"""Insert owner-filled 카카오페이손해보험(KR1098) 2023.4Q & 2024.4Q whole-quarter rows from
insurequant_master_tables.xlsx (K-ICS공시 sheet) into kics_disclosure.json as NEW rows.
sync_owner_fills_to_json.py only UPDATES existing rows — it can't create a missing filer-quarter,
so the owner's full 1~46 item fill never landed. This inserts them (schema-matched: 값 as string,
항목번호 int, 적용분류 null, no 값_당분기). Skips xlsx cells left blank (None) per existing
omit-undisclosed convention. Backs up to .pre_kakao.bak. Durable diag reflection = parser 0811Z."""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import json
import shutil
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "insurequant_master_tables.xlsx"
JSONP = ROOT / "kics_disclosure.json"
SHEET = "K-ICS공시"
CODE = "KR1098"
TARGET_Q = {"2023.4Q", "2024.4Q"}
KCODE, KNM, KTK, KCL, KIID, KITEM, KQ, KV = (
    "원보험사코드", "원수사명", "티커", "적용분류", "항목번호", "항목명", "공시분기", "값")


def vstr(v):
    """match existing JSON repr: integers w/o decimal, floats as-is."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


# ---- read xlsx rows for the two quarters ----
wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
ws = wb[SHEET]
it = ws.iter_rows(values_only=True)
hdr = list(next(it))


def hi(name):
    return next((i for i, h in enumerate(hdr) if h and str(h).strip() == name), None)


ci, cnm, ctk, cii, cit, cq, cv = (
    hi(KCODE), hi(KNM), hi(KTK), hi(KIID), hi(KITEM), hi(KQ), hi(KV))
assert None not in (ci, cnm, cii, cit, cq, cv), f"header detect fail: {hdr}"

new_rows = []
for r in it:
    if max(ci, cq, cii, cv) >= len(r):
        continue
    if str(r[ci]).strip() != CODE or str(r[cq]).strip() not in TARGET_Q:
        continue
    val = r[cv]
    if val is None or (isinstance(val, str) and val.strip() == ""):
        continue  # undisclosed blank → omit (existing convention)
    new_rows.append({
        KCODE: CODE,
        KNM: str(r[cnm]).strip() if cnm is not None and r[cnm] is not None else "카카오페이손해보험",
        KTK: str(r[ctk]).strip() if ctk is not None and r[ctk] is not None else "X",
        KCL: None,                      # JSON universally null
        KIID: int(r[cii]),
        KITEM: str(r[cit]).strip(),
        KQ: str(r[cq]).strip(),
        KV: vstr(val),
    })

# ---- guard: make sure these quarters are truly absent in JSON ----
data = json.loads(JSONP.read_text(encoding="utf-8"))
existing = {(str(x.get(KCODE)), str(x.get(KQ))) for x in data}
for q in TARGET_Q:
    if (CODE, q) in existing:
        print(f"!! {CODE} {q} already present in JSON — aborting to avoid dup.")
        sys.exit(1)

from collections import Counter
by_q = Counter(x[KQ] for x in new_rows)
print(f"xlsx → {len(new_rows)} rows to insert: {dict(by_q)}")
for q in sorted(TARGET_Q):
    items = sorted(x[KIID] for x in new_rows if x[KQ] == q)
    print(f"  {q}: items {items}")

shutil.copy2(JSONP, str(JSONP) + ".pre_kakao.bak")
data.extend(new_rows)
JSONP.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\ninserted {len(new_rows)} rows → kics_disclosure.json (backup: .pre_kakao.bak)")
