import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
led = json.load(open(R + "data/_gold/csm_amort_identity_ledger.json", encoding="utf-8"))
key = "교보생명보험|2026.1Q"
assert key in led["entries"]
del led["entries"][key]
out = R + "data/_derived/kyobo_csm_basis_fix_20261021/sim/amort_ledger_SAFE.json"
with open(out, "w", encoding="utf-8", newline="\n") as f:
    json.dump(led, f, ensure_ascii=False, indent=2)
print("wrote", out, "entries left:", list(led["entries"]))
