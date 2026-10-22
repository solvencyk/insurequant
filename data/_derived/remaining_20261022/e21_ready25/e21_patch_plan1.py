"""one-off patcher for e21_plan.py: main() -> build_pl_buckets() returning the state"""
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/e21_plan.py"
s = open(p, encoding="utf-8").read()
s = s.replace("def main():\n    plh = P.head_json", "def build_pl_buckets():\n    plh = P.head_json", 1)
old = '''    plan["_log_pl"] = LOG
    (EV / "e21_plan_pl_tmp.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("\n".join(LOG))
'''
new = '''    plan["_log_pl"] = LOG
    return dict(plan=plan, master=master, masterd=masterd, csm_m=csm_m, name_of=name_of, gold=gold, gold_csm=gold_csm, GOLD=GOLD, GOLDC=GOLDC, NULLD=NULLD, SETD=SETD,
                cand=cand, cand_csm=cand_csm, pl_cells_all=pl_cells_all, bucket_by=bucket_by, LOG=LOG)
'''
assert s.count(old) == 1
s = s.replace(old, new)
old2 = '''if __name__ == "__main__":
    main()
'''
assert s.count(old2) == 1
s = s.replace(old2, '')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched plan1")
