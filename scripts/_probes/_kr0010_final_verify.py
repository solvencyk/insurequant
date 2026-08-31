# -*- coding: utf-8 -*-
import json, io, sys, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MASTER = "kics_disclosure.json"
SCRATCH = r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kics_disclosure_scratch_FINAL.json"

with open("data/_derived/_patch_2026q2_KR0010.json", "r", encoding="utf-8") as f:
    patch = json.load(f)

CODE, Q = patch["company_code"], patch["quarter"]

with open(MASTER, "r", encoding="utf-8") as f:
    data = json.load(f)
print(f"live master currently has {len(data)} rows (re-read fresh, in case other sessions changed it)")

existing_kr0010_2q = [r for r in data if r["원보험사코드"] == CODE and r["공시분기"] == Q]
print(f"existing KR0010 2026.2Q rows in LIVE master right now: {len(existing_kr0010_2q)}")

meta_row = next(r for r in data if r["원보험사코드"] == CODE and r["공시분기"] == "2026.1Q" and r["항목번호"] == 1)
NAME, TICKER, LS = meta_row["원수사명"], meta_row["티커"], meta_row["생손보여부"]

patch_rows = []
for c in patch["cells"]:
    row = {
        "원보험사코드": CODE, "원수사명": NAME, "티커": TICKER, "생손보여부": LS,
        "항목번호": c["항목번호"], "항목명": c["항목명"], "공시분기": Q, "값": c["값"],
    }
    if c["값_적용후"] is not None:
        row["값_적용후"] = c["값_적용후"]
    patch_rows.append(row)

new_data = [r for r in data if not (r["원보험사코드"] == CODE and r["공시분기"] == Q)]
insert_at = min(len(new_data), len(data) - len(new_data) and next((i for i, r in enumerate(data) if r["원보험사코드"] == CODE and r["공시분기"] == Q), len(new_data)))
if not existing_kr0010_2q:
    insert_at = next((i for i, r in enumerate(data) if r["원보험사코드"] == CODE), len(new_data))
new_data[insert_at:insert_at] = patch_rows
print(f"spliced: removed {len(data)-len(new_data)+len(patch_rows)} old, inserted {len(patch_rows)} new -> total {len(new_data)}")

with open(SCRATCH, "w", encoding="utf-8") as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

result = subprocess.run(
    [r"C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe",
     "scripts/validate_kics_disclosure.py", "--master", SCRATCH],
    capture_output=True, text=True, encoding="utf-8", cwd=r"C:\Users\sangwook.cho\Desktop\insurequant"
)
print("gate returncode:", result.returncode)

# find the report just written
import glob, os
reports = sorted(glob.glob("artifacts/kics_validation/report_2026*.json"), key=os.path.getmtime)
latest = reports[-1]
print("latest report:", latest)
with open(latest, "r", encoding="utf-8") as f:
    rep = json.load(f)
assert rep["source"] == SCRATCH, f"report source mismatch: {rep['source']}"

fs = [f for f in rep["findings"] if f.get("원보험사코드") == CODE and f.get("공시분기") == Q]
counts = {}
for f in fs:
    counts[f["status"]] = counts.get(f["status"], 0) + 1
print("FINAL KR0010 2026.2Q finding status counts:", counts)
red = [f for f in fs if f["status"] == "RED"]
print("RED findings:", red if red else "NONE")

census = rep["coverage_census"]
print("coverage_census missing_count:", census["missing_count"])
pzc = [x for x in rep["parent_zero_child_nonzero"] if x.get("code")=="KR0010"]
pci = rep["parent_present_child_incomplete"]
pci_kr0010 = [x for x in pci["partial_red"]+pci["full_absent_even_review"] if x.get("code")=="KR0010"]
print("parent_zero_child_nonzero KR0010:", pzc)
print("parent_present_child_incomplete KR0010:", pci_kr0010)
