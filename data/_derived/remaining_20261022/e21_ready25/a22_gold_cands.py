"""a22_gold_cands: candidate cells that overlap an owner gold cell; plus the gold entries of the READY companies (READ-ONLY)"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(R + "data/_derived/remaining_20261022/e20_held_and_remaining/measure/cands_READY_all.json", encoding="utf-8").read())
print("keys of file:", list(d.keys()))
print("PL cells with gold:")
for c in d["pl_cells"]:
    if c.get("gold") is not None:
        print("  ", c["code"], c["q"], "i", c["item"], "old", c["old"], "new", c["new"], "gold", c["gold"], "was", c.get("gold_was"), "note", str(c.get("gold_note"))[:100])
print("CSM cells with gold:")
for c in d["csm_cells"]:
    if c.get("gold") is not None:
        print("  ", c["code"], c["q"], "i", c["item"], "old", c["old"], "new", c["new"], "gold", c["gold"], "was", c.get("gold_was"), "note", str(c.get("gold_note"))[:100])
gp = json.loads(open(R + "data/_gold/user_pl_cells.json", encoding="utf-8").read())
gc = json.loads(open(R + "data/_gold/user_csm_cells.json", encoding="utf-8").read())
codes = {"KR0104", "KR0083", "KR0070", "KR0079", "KR0010", "KR0099", "KR0003", "KR0001", "KR0068"}
print("PL gold set total", len(gp["set"]), "of READY companies:")
for e in gp["set"]:
    if e["원보험사코드"] in codes:
        print("   PLG", e["원보험사코드"], e["공시분기"], "i", e["항목번호"], e["값"], "was", e.get("was"))
print("CSM gold set total", len(gc["set"]), "of READY companies:")
for e in gc["set"]:
    if e["원보험사코드"] in codes:
        print("   CSMG", e["원보험사코드"], e["공시분기"], "i", e["항목번호"], e["값"], str(e.get("why") or e.get("note"))[:80])
nd = gp["null_dangi"]["cells"]; sd = gp["set_dangi"]["cells"]
print("null_dangi total", len(nd), "READY cos:", [x for x in nd if x[0] in codes])
print("set_dangi total", len(sd), "READY cos:", [x[:4] for x in sd if x[0] in codes])
