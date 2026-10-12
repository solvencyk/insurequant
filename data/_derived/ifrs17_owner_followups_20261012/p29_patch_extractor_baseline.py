# -*- coding: utf-8 -*-
p = "C:/Users/sangwook.cho/Desktop/insurequant/scripts/extract_chubb_d2_20261012.py"
s = open(p, encoding="utf-8", newline="").read()
a = '''    bs = json.loads((ROOT / "IFRS17_BS.json").read_bytes().decode("utf-8"))
    bs_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    ilp = json.loads((ROOT / "insurance_liability_portfolio.json").read_bytes().decode("utf-8"))
'''
b = '''    # idempotent: the "old" values are the PRE-APPLY bytes (the backups the appliers wrote) once the masters have been changed
    bk = ROOT / "data" / "_derived" / "ifrs17_owner_followups_backup_20261012"
    bs_src = bk / "chubb_d2" / "IFRS17_BS.json"
    ilp_src = bk / "insurance_liability_portfolio.json.pre_chubb_d2"
    bs = json.loads((bs_src if bs_src.exists() else ROOT / "IFRS17_BS.json").read_bytes().decode("utf-8"))
    bs_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    ilp = json.loads((ilp_src if ilp_src.exists() else ROOT / "insurance_liability_portfolio.json").read_bytes().decode("utf-8"))
'''
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s)
print("patched")
