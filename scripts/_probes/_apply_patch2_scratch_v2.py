# -*- coding: utf-8 -*-
import json, io, sys, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MASTER = "kics_disclosure.json"
PATCH = "data/_derived/_patch2_2026q2_KR0049.json"
SCRATCH = r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kics_disclosure.scratch_kr0049_47census_v2.json"

with open(MASTER, "r", encoding="utf-8") as f:
    data = json.load(f)
with open(PATCH, "r", encoding="utf-8") as f:
    patch = json.load(f)

code, quarter = patch["company_code"], patch["quarter"]
meta = None
for r in data:
    if r.get("원보험사코드") == code and r.get("공시분기") == quarter:
        meta = {k: r[k] for k in ("원보험사코드","원수사명","티커","생손보여부")}
        break
assert meta is not None

n_updated, n_inserted = 0, 0
scratch = copy.deepcopy(data)
for cell in patch["cells"]:
    item_no = cell["항목번호"]
    found = None
    for r in scratch:
        if r.get("원보험사코드") == code and r.get("공시분기") == quarter and r.get("항목번호") == item_no:
            found = r
            break
    if found is not None:
        before = dict(found)
        found["값"] = cell["값"]
        if cell.get("값_적용후") is not None:
            found["값_적용후"] = cell["값_적용후"]
        n_updated += 1
        print(f"UPDATED item{item_no}: {before} -> 값={cell['값']!r} 값_적용후={cell.get('값_적용후')!r}")
    else:
        new_row = {**meta, "항목번호": item_no, "항목명": cell["항목명"], "공시분기": quarter, "값": cell["값"]}
        if cell.get("값_적용후") is not None:
            new_row["값_적용후"] = cell["값_적용후"]
        scratch.append(new_row)
        n_inserted += 1
        print(f"INSERTED item{item_no}: {new_row}")

print(f"\nupdated={n_updated} inserted={n_inserted}")
with open(SCRATCH, "w", encoding="utf-8") as f:
    json.dump(scratch, f, ensure_ascii=False)
print("wrote scratch:", SCRATCH, "rows:", len(scratch), "(orig", len(data), ")")
