import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("data/_derived/_patch_2026q2_KR0010.json", "r", encoding="utf-8") as f:
    patch = json.load(f)

print("company_code:", patch["company_code"], "quarter:", patch["quarter"])
print("num cells:", len(patch["cells"]))
print("unfixable:", patch["unfixable"])
print()
for c in patch["cells"][:3]:
    print(c["항목번호"], repr(c["항목명"]), c["값"], c["값_적용후"])
print("...")
for c in patch["cells"][-3:]:
    print(c["항목번호"], repr(c["항목명"]), c["값"], c["값_적용후"])

# byte-exact label check against master's own historical labels
with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    master = json.load(f)
label_by_item = {}
for r in master:
    if r["원보험사코드"] == "KR0010":
        label_by_item.setdefault(r["항목번호"], r["항목명"])
kr0008_2q = {r["항목번호"]: r["항목명"] for r in master if r["원보험사코드"] == "KR0008" and r["공시분기"] == "2026.2Q"}

mismatches = []
for c in patch["cells"]:
    it = c["항목번호"]
    expected = label_by_item.get(it) or kr0008_2q.get(it)
    if expected is not None and c["항목명"] != expected:
        mismatches.append((it, c["항목명"], expected))
print("\nlabel mismatches vs master convention:", mismatches if mismatches else "NONE - all byte-exact")

# item27/28 precision check
for c in patch["cells"]:
    if c["항목번호"] in (27, 28):
        print(c["항목번호"], c["값"])
