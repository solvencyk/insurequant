import json
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ilp_restated_comparative.json"
raw = open(p, "rb").read().decode("utf-8")
o = json.loads(raw)
assert json.dumps(o, ensure_ascii=False, indent=1) + "\n" == raw
o["extended_by"] = ["scripts/load_ilp_interim_2023_2024.py", "scripts/load_ilp_interim_2023_2024.py", "scripts/load_ilp_interim_2023_2024.py",
                    "scripts/load_ilp_lic_stage3b_pdf.py", "scripts/apply_kr0073_bs_ilp_restated_20261022.py"]
open(p, "wb").write((json.dumps(o, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
print("ok")

s = "C:/Users/sangwook.cho/Desktop/insurequant/scripts/apply_kr0073_bs_ilp_restated_20261022.py"
t = open(s, encoding="utf-8").read()
old = '''    files["SIDE"].obj["extended_by"] = "scripts/apply_kr0073_bs_ilp_restated_20261022.py (KR0073 2023.4Q cell added)"'''
new = '''    prev_by = files["SIDE"].obj.get("extended_by", [])
    prev_by = [prev_by] if isinstance(prev_by, str) else list(prev_by)
    files["SIDE"].obj["extended_by"] = prev_by + ["scripts/apply_kr0073_bs_ilp_restated_20261022.py"]'''
assert old in t
open(s, "w", encoding="utf-8", newline="").write(t.replace(old, new))
