import json, sys
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
d = json.loads(open(M + "p_lotte.json", encoding="utf-8").read())
for q, v in d.items():
    print(q, "prior_run", {k: (round(x, 3) if isinstance(x, float) else x) for k, x in v["prior_run"].items()}, "tables", v["tables_prior"])
