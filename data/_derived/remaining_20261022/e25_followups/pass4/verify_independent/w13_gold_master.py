import json,sys,subprocess
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
g=json.load(open(R+"data/_gold/user_pl_cells.json",encoding="utf-8"))
old=json.loads(subprocess.run(["git","-C",R,"show","HEAD:data/_gold/user_pl_cells.json"],capture_output=True).stdout.decode("utf-8"))
PL={(r["원보험사코드"],r["공시분기"],r["항목번호"]):r for r in json.load(open(R+"PL_breakdown.json",encoding="utf-8"))}
k=lambda e:(e["원보험사코드"],e["공시분기"],e["항목번호"])
o={k(e) for e in old["set"]}
bad=0
for e in g["set"]:
    if k(e) not in o:
        m=PL[k(e)]["값"]; ok=(m==e["값"]) or (m is not None and e["값"] is not None and abs(m-e["값"])<1e-9)
        bad+=not ok; print("OK " if ok else "BAD",k(e),e["값"],m)
nd=g["null_dangi"]["cells"]; nd0=old["null_dangi"]["cells"]
add=[c for c in nd if c not in nd0]; rem=[c for c in nd0 if c not in nd]
print("null_dangi added",add,"removed",rem)
for c in add: print("  master dangi",c,PL[tuple(c)].get("값_당분기"))
for c in rem: print("  released dangi",c,PL[tuple(c)].get("값_당분기"))
print("bad",bad)
