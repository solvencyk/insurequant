"""one-off patcher for e21_diff_vs_head.py: account for the KB라이프 handler fix (3 gold cells removed afterwards, viz master 3 cells, golden manifest, companies.py)"""
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/"
s = open(H + "e21_diff_vs_head.py", encoding="utf-8").read()
old = '''added = lg["set"][n0:]
chk("gold: appended entries == plan new entries (order, 값, was, note)", [(gk(e), e["값"], e["was"], e["note"]) for e in added] == [((e["code"], e["item"], e["quarter"]), e["value"], e["was"], e["note"]) for e in C["gold_new"]])'''
new = '''added = lg["set"][n0:]
KLIFE = {("KR0099", 2, "2024.1Q"), ("KR0099", 8, "2024.1Q"), ("KR0099", 12, "2024.1Q")}
chk("gold: appended entries == plan new entries minus the 3 KB라이프 cells removed after the handler fix (order, 값, was, note)", [(gk(e), e["값"], e["was"], e["note"]) for e in added] == [((e["code"], e["item"], e["quarter"]), e["value"], e["was"], e["note"]) for e in C["gold_new"] if (e["code"], e["item"], e["quarter"]) not in KLIFE])
chk("gold: the 3 KB라이프 2024.1Q cells (2/8/12) are NOT in the gold file (the fixed builder source carries them)", not any(gk(e) in KLIFE for e in lg["set"]))
vh = json.loads(head("data/dart/viz/pl_breakdown_master.json").decode("utf-8"))
vl = json.loads(live("data/dart/viz/pl_breakdown_master.json").decode("utf-8"))
vhm, vlm = {key(r): r for r in vh}, {key(r): r for r in vl}
vchg = sorted(k for k in vlm if vhm.get(k) != vlm[k])
chk("viz builder master: exactly the 3 KB라이프 cells changed, to the plan values", vchg == sorted(KLIFE) and all(vlm[k]["값"] == planned[k]["value"] for k in vchg) and len(vh) == len(vl), f"({vchg})")
fh = json.loads(head("tests/fixtures/pl_breakdown_golden.json").decode("utf-8"))
fl = json.loads(live("tests/fixtures/pl_breakdown_golden.json").decode("utf-8"))
chk("PL golden manifest: only sha256_master moved", {k for k in fl if fl[k] != fh.get(k)} == {"sha256_master"}, f"({[k for k in fl if fl[k] != fh.get(k)]})")
ch = head("scripts/pl_breakdown/companies.py").decode("utf-8").split("\n")
cl_ = live("scripts/pl_breakdown/companies.py").decode("utf-8").split("\n")
dd = [x for x in difflib.unified_diff(ch, cl_, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
chk("companies.py: only the extract_tier2_kblife _jang_rerev line (abs removed, + 2 comment lines)", len(dd) == 4 and sum(1 for x in dd if x.startswith("-")) == 1 and "abs(jrr)" in [x for x in dd if x.startswith("-")][0], f"({len(dd)} lines)")
for x in dd:
    out.append("   " + x[:200])'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
open(H + "e21_diff_vs_head.py", "w", encoding="utf-8", newline="\n").write(s)
print("patched diff1")
