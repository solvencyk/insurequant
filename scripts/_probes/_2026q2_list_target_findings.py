import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

path = "artifacts/kics_validation/report_latest.json"
with open(path, encoding="utf-8") as f:
    data = json.load(f)

findings = data.get("findings") if isinstance(data, dict) else data
print("top-level type:", type(data), "keys:" , list(data.keys()) if isinstance(data, dict) else None)
print("n findings:", len(findings))

targets_19market = ["KR0004","KR0011","KR0029","KR0051","KR0068","KR0080","KR0087","KR0094","KR0099","KR0100","KR0104","KR1098"]
targets_36irr = ["KR0072","KR1010"]

want = set()
for c in targets_19market:
    want.add(("19_market", c))
for c in targets_36irr:
    want.add(("36_irr", c))

found = []
for f_ in findings:
    rule = f_.get("rule")
    code = f_.get("원보험사코드")
    q = f_.get("공시분기")
    if q != "2026.2Q":
        continue
    if (rule, code) in want and f_.get("status") == "RED":
        found.append(f_)

print("matched RED count:", len(found))
for f_ in found:
    print("----")
    for k in ["rule","원보험사코드","원수사명","공시분기","status","expected","actual","diff","detail"]:
        print(f"{k}: {f_.get(k)}")
