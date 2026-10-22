import json, io
D = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/"
out = io.open(D+"e19_latest_comparative/KR0005_s3_cand.txt","w",encoding="utf-8")
c = json.load(io.open(D+"d_census/cand_pl_cells.json",encoding="utf-8"))
out.write(json.dumps(c[0],ensure_ascii=False)+"\n")
for e in c:
    s = json.dumps(e,ensure_ascii=False)
    if "KR0005" in s: out.write(s+"\n")
out.close()
