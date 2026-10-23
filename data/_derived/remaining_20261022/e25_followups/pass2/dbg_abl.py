import json, sys
sys.argv = ["x"]
sys.stdout.reconfigure(encoding="utf-8")
src = open("x01_verify_p2.py", encoding="utf-8").read().split("for name, fn in")[0]
exec(compile(src, "x01", "exec"))
abl = json.load(open(f"{EV}/kr0070_abl/r03_abl_read.json", encoding="utf-8"))
rec = abl["2023.1Q"]
rows, _ = table_rows(rec["file"], rec["rev_table"])
for r in rows[:14]:
    print(r["tr"], repr(r["key1"]), len(r["nums"]), [c["text"] for c in r["cells"]][:4])
