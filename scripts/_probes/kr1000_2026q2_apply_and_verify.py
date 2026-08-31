# -*- coding: utf-8 -*-
import sys, io, json, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"C:\Users\sangwook.cho\Desktop\insurequant"
MASTER = ROOT + r"\kics_disclosure.json"
PATCH = ROOT + r"\data\_derived\_patch_2026q2_KR1000.json"
SCRATCH_DIR = r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad"
SCRATCH = SCRATCH_DIR + r"\kics_disclosure_KR1000_2026Q2_scratch.json"

with open(MASTER, "r", encoding="utf-8") as f:
    rows = json.load(f)
with open(PATCH, "r", encoding="utf-8") as f:
    patch = json.load(f)

code, quarter = patch["company_code"], patch["quarter"]

# template for brand-new rows (36-46): copy identity fields from an existing row of this company/quarter
template = next(r for r in rows if r.get("원보험사코드") == code and r.get("공시분기") == quarter and int(r.get("항목번호", -1)) == 1)
print("template identity fields:", {k: template[k] for k in ["원보험사코드","원수사명","티커","생손보여부"]})

scratch_rows = copy.deepcopy(rows)
by_key = {}
for idx, r in enumerate(scratch_rows):
    if r.get("원보험사코드") == code and r.get("공시분기") == quarter:
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        by_key[it] = idx

updated, created = [], []
for cell in patch["cells"]:
    it = cell["항목번호"]
    if it in by_key:
        idx = by_key[it]
        scratch_rows[idx]["항목명"] = cell["항목명"]
        scratch_rows[idx]["값"] = cell["값"]
        scratch_rows[idx]["값_적용후"] = cell["값_적용후"]
        updated.append(it)
    else:
        new_row = {
            "원보험사코드": template["원보험사코드"],
            "원수사명": template["원수사명"],
            "티커": template["티커"],
            "생손보여부": template["생손보여부"],
            "항목번호": it,
            "항목명": cell["항목명"],
            "공시분기": quarter,
            "값": cell["값"],
            "값_적용후": cell["값_적용후"],
        }
        scratch_rows.append(new_row)
        created.append(it)

print(f"updated existing rows: {updated}")
print(f"created new rows: {created}")
print(f"scratch total rows: {len(scratch_rows)} (orig {len(rows)}, +{len(scratch_rows)-len(rows)})")

with open(SCRATCH, "w", encoding="utf-8") as f:
    json.dump(scratch_rows, f, ensure_ascii=False, indent=2)
print(f"wrote scratch master: {SCRATCH}")
