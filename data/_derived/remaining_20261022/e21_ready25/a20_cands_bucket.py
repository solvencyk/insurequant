"""a20_cands_bucket: list the candidate PL/CSM cells of the given buckets (READ-ONLY).  usage: a20 CODE Q [Q...]"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
d = json.loads(open(R + "data/_derived/remaining_20261022/e20_held_and_remaining/measure/cands_READY_all.json", encoding="utf-8").read())
code = sys.argv[1]
for q in sys.argv[2:]:
    pl = sorted([c for c in d["pl_cells"] if c["code"] == code and c["q"] == q], key=lambda c: c["item"])
    cs = sorted([c for c in d["csm_cells"] if c["code"] == code and c["q"] == q], key=lambda c: c["item"])
    print(f"== {code} {q}: PL {len(pl)} CSM {len(cs)}")
    for c in pl:
        print(f"   PL i{c['item']:>2} old={c['old']} new={c['new']} gold={c.get('gold')} was={c.get('gold_was')}")
    for c in cs:
        print(f"   CSM i{c['item']} old={c['old']} new={c['new']} gold={c.get('gold')}")
