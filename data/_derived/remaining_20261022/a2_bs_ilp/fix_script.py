p = "C:/Users/sangwook.cho/Desktop/insurequant/scripts/apply_kr0073_bs_ilp_restated_20261022.py"
s = open(p, encoding="utf-8").read()
bad1 = '(r["원보験사코드".replace("験", "험")], r["공시분기"], r["항목번호"])'
good1 = '(r["원보험사코드"], r["공시분기"], r["항목번호"])'
assert bad1 in s
s = s.replace(bad1, good1)
bad2 = '''    assert (n[(1, "2024.4Q")] - bs_idx[(CODE, 2, "2024.4Q")]["값"] - bs_idx[(CODE, 3, "2024.4Q")]["值" if False else "값"]) < 1e-3                # 2024.4Q block closes with items 2,3 already on that column'''
good2 = '''    assert abs(n[(1, "2024.4Q")] - bs_idx[(CODE, 2, "2024.4Q")]["값"] - bs_idx[(CODE, 3, "2024.4Q")]["값"]) < 1e-3   # 2024.4Q: items 2,3 already on that column, so 1 = 2 + 3 closes'''
assert bad2 in s
s = s.replace(bad2, good2)
open(p, "w", encoding="utf-8", newline="").write(s)
import re
print("non-hangul CJK chars:", [c for c in s if "\u3040" <= c <= "\u30ff" or "\u4e00" <= c <= "\u9fff"])
