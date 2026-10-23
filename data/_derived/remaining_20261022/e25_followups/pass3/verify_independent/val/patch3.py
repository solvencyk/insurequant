p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val/b03_nh.py"
s = open(p, encoding="utf-8").read()
s = s.replace('    ncols = len(got["20"])', '    if "20" not in got:\n        P(f"##### {q}: statement table not found/parsed (found_tab={found_tab}, got={sorted(got)})")\n        continue\n    ncols = len(got["20"])')
open(p, "w", encoding="utf-8").write(s)
