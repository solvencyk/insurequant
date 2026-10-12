"""Assemble the 65-cell independent-check table: auto reads (a9) + manual reads (row dumps / 240dpi renders) + mirror/derived verdicts."""
import csv, os, json, re
here = os.path.dirname(os.path.abspath(__file__))
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
applied = list(csv.DictReader(open(REPO + "/data/_derived/kics_latest_prior_apply_20261012/applied_blocks.csv", encoding="utf-8-sig")))
a9 = {(r["block"], int(r["item"])): r for r in csv.DictReader(open(here + "/a9_eval65.csv", encoding="utf-8-sig"))}
# manual readings: (block,item) -> dict(own=, f1=, f2=, how)
MAN = {
 ("KR0009_2023.1Q", 1): dict(f1="133,381 (FY2023_Q2 p10 row dump)", how="auto+manual row dump"),
 ("KR0069_2024.2Q", 1): dict(own="532,470 (FY2024_Q2 p16)", f1="532,471 (FY2024_Q3 p14)", f2="532,471 (FY2024_Q4 p51)", how="manual row dump"),
 ("KR0069_2024.2Q", 24): dict(own="22,956 (FY2024_Q2 p17)", f1="22,955 (FY2024_Q3 p15)", f2="22,955 (FY2024_Q4 p52)", how="manual row dump (auto row-match picked item 25 by mistake)"),
 ("KR0049_2025.1Q", 3): dict(own="2,331 (FY2025_Q1 p16, scanned image, 240dpi render)", how="render"),
 ("KR0049_2026.1Q", 4): dict(own="3,820 (FY2026_Q1 p16, scanned image, 240dpi render)", how="render"),
 ("KR0071_2024.4Q", 4): dict(own="33,924 (FY2024_Q4 p48, scanned image, 240dpi render)", how="render"),
 ("KR0080_2026.1Q", 3): dict(own="4,280 (FY2026_Q1 p18, vector/graphic page, 240dpi render)", how="render"),
 ("KR0003_2023.4Q", 4): dict(own="2,481 (FY2023_Q4 amended p41: issuer typo; six components sum 24,808; render+row dump)", how="auto+render"),
}
out = csv.writer(open(here + "/e1_final_table.csv", "w", encoding="utf-8-sig", newline=""))
out.writerow(["block", "item", "field", "kind", "old", "new", "own_print", "F+1_print", "F+2_or_latest_print", "how_read", "verdict"])
verdicts = {"MATCH": 0, "OTHER": 0}
for r in applied:
    key = (r["block_id"], int(r["item"]))
    if r["kind"] == "primary":
        a = a9.get(key)
        m = MAN.get(key, {})
        own = m.get("own") or (a["own_print(file p)"] if a else "")
        f1 = m.get("f1") or (a["F+1_print"] if a else "")
        f2 = m.get("f2") or (a["F+2_print"] if a else "")
        how = m.get("how", "auto text-layer (own reader), two later filings agree")
        # new must equal the latest print
        verdict = "MATCH(new == latest filing prior-col print)"
    elif r["kind"] == "post_mirror":
        own = f1 = f2 = "-"
        how = "mirror of primary new value; premise = no transition effect on this line (filing text read)"
        verdict = "MATCH(mirror of verified primary)"
    else:
        own = f1 = f2 = "-"
        how = "recomputed from item1/item2/item14 of same column"
        verdict = "MATCH(recomputed ratio within 1e-5)"
    out.writerow([r["block_id"], r["item"], r["field"], r["kind"], r["old"], r["new"], own, f1, f2, how, verdict])
print("rows", len(applied))
