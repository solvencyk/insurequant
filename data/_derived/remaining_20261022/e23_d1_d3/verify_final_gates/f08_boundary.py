import json,sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
cs={(r["원보험사코드"],r["항목번호"],r["공시분기"]):r["값"] for r in json.load(open(R+"/CSM_waterfall.json",encoding="utf-8"))}
out=[]
for co in ("KR0099","KR0003","KR0070","KR0009","KR0072"):
    for fy in (2023,2024,2025):
        c=cs.get((co,6,f"{fy}.4Q")); o=cs.get((co,1,f"{fy+1}.1Q"))
        d=None if c is None or o is None else round(o-c,2)
        out.append(f"{co} FY{fy}->{fy+1} 4Q closing {c} vs next 1Q opening {o} diff {d}")
    ops=[cs.get((co,1,f"2023.{q}Q")) for q in (1,2,3,4)]
    out.append(f"{co} FY2023 openings 1Q-4Q {ops} spread {round(max(ops)-min(ops),2)}")
    for fy in (2024,2025):
        ops=[cs.get((co,1,f"{fy}.{q}Q")) for q in (1,2,3,4)]
        out.append(f"{co} FY{fy} openings spread {round(max(ops)-min(ops),2)}")
print("\n".join(out))
open(R+"/"+"data/_derived/remaining_20261022/e23_d1_d3/verify_final_gates/f08_boundary.txt","w",encoding="utf-8").write("\n".join(out))
