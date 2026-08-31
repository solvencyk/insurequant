# -*- coding: utf-8 -*-
"""Final: (1) byte-verify patch 항목명 against master's own historical KR0032 labels,
(2) rebuild scratch master + apply patch, (3) run CLI gate, (4) print KR0032 2026.2Q lines."""
import sys, io, json, copy, subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

with open(ROOT / "kics_disclosure.json", "r", encoding="utf-8") as f:
    live = json.load(f)
with open(ROOT / "data" / "_derived" / "_patch_2026q2_KR0032.json", "r", encoding="utf-8") as f:
    patch = json.load(f)

kr_rows = [r for r in live if r.get("원보험사코드") == "KR0032"]

print("=== label byte-match check ===")
all_ok = True
for cell in patch["cells"]:
    item = cell["항목번호"]
    label = cell["항목명"]
    historical = {r["항목명"] for r in kr_rows if r["항목번호"] == item}
    if not historical:
        print(f"item{item}: NO historical label to compare (first-ever row) -- label={label!r}")
        continue
    ok = label in historical
    all_ok = all_ok and ok
    codepoints = [hex(ord(c)) for c in label if not c.isascii()]
    print(f"item{item}: match={ok}  label={label!r}")
    if not ok:
        print(f"    MISMATCH! historical set = {historical!r}")
print(f"\nALL LABELS MATCH: {all_ok}")

# ---- rebuild scratch + apply ----
SCRATCH = ROOT / "scripts" / "_probes" / "_scratch_kr0032_final.json"
records = copy.deepcopy(live)


def find_row(recs, code, quarter, item):
    for r in recs:
        if r.get("원보험사코드") == code and r.get("공시분기") == quarter and r.get("항목번호") == item:
            return r
    return None


for cell in patch["cells"]:
    item = cell["항목번호"]
    row = find_row(records, "KR0032", "2026.2Q", item)
    if row is None:
        new_row = {
            "원보험사코드": "KR0032", "원수사명": "NH농협손해보험", "티커": "X",
            "생손보여부": "손해보험", "항목번호": item, "항목명": cell["항목명"],
            "공시분기": "2026.2Q", "값": cell["값"],
        }
        if cell["값_적용후"] is not None:
            new_row["값_적용후"] = cell["값_적용후"]
        records.append(new_row)
    else:
        row["값"] = cell["값"]
        if cell["값_적용후"] is not None:
            row["값_적용후"] = cell["값_적용후"]

with open(SCRATCH, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False)
print(f"\nwrote {SCRATCH}")
