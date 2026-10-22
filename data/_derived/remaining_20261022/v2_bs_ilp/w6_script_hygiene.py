import ast, json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
p = R + "scripts/apply_kr0073_bs_ilp_restated_20261022.py"
b = open(p, "rb").read()
print("BOM:", b[:3] == b"\xef\xbb\xbf")
ast.parse(b.decode("utf-8"))
print("ast ok, bytes", len(b))
for f in ["data/dart/viz/bs_manual_overrides.json", "data/_derived/ilp_restated_comparative.json", "insurance_liability_portfolio_provenance.json", "tests/fixtures/ifrs17_bs_golden.json", "tests/fixtures/builder_input_fingerprints.json"]:
    raw = open(R + f, "rb").read()
    json.loads(raw.decode("utf-8"))
    print(f, "valid json, BOM:", raw[:3] == b"\xef\xbb\xbf")
ov = json.load(open(R + "data/dart/viz/bs_manual_overrides.json", encoding="utf-8"))
ks = [k for k in ov.get("overrides", ov) if k.startswith("KR0073|")]
print("KR0073 override keys:", ks)
