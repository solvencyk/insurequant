# -*- coding: utf-8 -*-
"""Independent check: master 2023 cumulative PL headline cells vs DART FS-API prior-year columns of the FY2024 filings (OFS = separate basis). Read-only."""
import json, re, sys, os
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant"
OUT=R+"/data/_derived/remaining_20261022/e23_d1_d3/verify_final_gates/"
CORP={"KR0070":"00148391","KR0099":"00160393","KR0003":"00113562","KR0009":"00164973","KR0072":"00104069"}
REP={"2023.1Q":"11013","2023.2Q":"11012","2023.3Q":"11014","2023.4Q":"11011"}
PL={ (r["원보험사코드"],r["항목번호"],r["공시분기"]):r for r in json.load(open(R+"/PL_breakdown.json",encoding="utf-8"))}
chg=json.load(open(OUT+"f01_changed_cells.json",encoding="utf-8"))["PL_breakdown.json"]
changed={tuple(k) for c in CORP for k in chg.get(c,[])}
import subprocess
hd=json.loads(subprocess.run(["git","-C",R,"show","HEAD:PL_breakdown.json"],capture_output=True,stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
HD={(r["원보험사코드"],r["항목번호"],r["공시분기"]):r for r in hd}
NAME={1:r"^(보험손익|총\s*보험서비스결과|보험영업손익)",17:r"^(투자손익|투자영업손익)",22:r"(법인세비용차감전|세전)",23:r"^(법인세)",24:r"^당기순이익|^당기순손익|^분기순이익|^반기순이익",25:r"^기타포괄손익$|^기타포괄손익\(?손실|^세후기타포괄|^총기타포괄|^당기기타포괄|^기타포괄손익\s*합계|^법인세.*차감후",31:r"^총포괄손익|^총포괄이익|^당기총포괄|^분기총포괄|^반기총포괄"}
lines=[]
def P(s): lines.append(s); print(s)
tot={"match_changed":0,"match_unchanged":0,"mismatch_changed":[],"mismatch_unchanged":[],"nocand":[]}
for co,corp in CORP.items():
    for q,rep in REP.items():
        fn=f"C:/Users/sangwook.cho/Desktop/insurequant/data/dart/_fs_api_cache/{corp}_2024_{rep}_OFS.json"
        if not os.path.exists(fn): P(f"NOFILE {co} {q} {fn}"); continue
        lst=json.load(open(fn,encoding="utf-8")).get("list") or []
        isr=[r for r in lst if r.get("sj_div") in ("IS","CIS")]
        for it,rx in NAME.items():
            k=(co,it,q); r=PL.get(k)
            if not r or r.get("값") is None: continue
            cands=[]
            for a in isr:
                if re.search(rx,a.get("account_nm","")):
                    v=a.get("frmtrm_add_amount") if rep!="11011" else a.get("frmtrm_amount")
                    if v in (None,"","-") and rep=="11013": v=a.get("frmtrm_amount")
                    try: cands.append((a["account_nm"],float(str(v).replace(",",""))/1e6))
                    except Exception: pass
            tag="changed" if k in changed else "unchanged"
            if not cands: tot["nocand"].append((co,q,it,tag)); continue
            best=min(cands,key=lambda c:abs(c[1]-r["값"]))
            ok=abs(best[1]-r["값"])<=1.0
            if ok: tot["match_"+tag]+=1
            else: tot["mismatch_"+tag].append((co,q,it,r["값"],HD[k]["값"],cands[:3]))
P(f"match_changed={tot['match_changed']} match_unchanged={tot['match_unchanged']} mismatch_changed={len(tot['mismatch_changed'])} mismatch_unchanged={len(tot['mismatch_unchanged'])} nocand={len(tot['nocand'])}")
for m in tot["mismatch_changed"]: P("MISMATCH changed "+str(m))
for m in tot["mismatch_unchanged"]: P("MISMATCH unchanged "+str(m))
P("NOCAND "+str(tot["nocand"]))
open(OUT+"f05_fsapi.txt","w",encoding="utf-8").write("\n".join(lines))
