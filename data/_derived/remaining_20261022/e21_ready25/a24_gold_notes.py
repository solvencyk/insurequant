"""a24_gold_notes: full why/note text of selected owner-gold cells (READ-ONLY)"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
gc = json.loads(open(R + "data/_gold/user_csm_cells.json", encoding="utf-8").read())
gp = json.loads(open(R + "data/_gold/user_pl_cells.json", encoding="utf-8").read())
print("CSM gold top-level keys:", list(gc.keys()))
for e in gc["set"]:
    if e["원보험사코드"] == "KR0003" and e["공시분기"] in ("2023.1Q",) and e["항목번호"] in (1, 2, 3, 4, 5, 6):
        print("CSMG", e["공시분기"], e["항목번호"], e["값"], "|", e.get("why") or e.get("note"), "| keys:", list(e.keys()))
for e in gp["set"]:
    k = (e["원보험사코드"], e["공시분기"], e["항목번호"])
    if k in {("KR0010", "2023.1Q", 16), ("KR0010", "2023.2Q", 16), ("KR0003", "2023.2Q", 19), ("KR0001", "2023.1Q", 16), ("KR0001", "2023.2Q", 16), ("KR0068", "2023.1Q", 20), ("KR0068", "2023.2Q", 21)}:
        print("PLG", k, e["값"], "was", e.get("was"), "|", e.get("note"))
print("PL gold top-level keys:", list(gp.keys()))
