import sys,re,glob,os,json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd, v10_note_engine as E
import v34_seam_lob as S
R=E.ROOT
f=S.main_file("KR0010",2025,4); doc=xmlrd.get(f)
cands=[c for c in S.lobs_tables(doc) if c[2] and "연결" not in c[2] and "주석" in c[2]]
print(os.path.basename(f),[(c[0]["start"],c[1]) for c in cands])
for t,mk,bt in cands:
    if mk in ("전기","전분기","전반기") or True:
        out,secs,cum_idx=E.compute(doc,t,"KB")
        print("table",t["start"],"marker",mk,{k:out.get(k) for k in (4,5,6,9,10,11,13,14,2,3,8)})
print("master 2024.4Q KB:",{i:E.master.get(("KR0010","2024.4Q",i)) for i in (4,5,6,9,10,11,13,14,2,3,8)})
