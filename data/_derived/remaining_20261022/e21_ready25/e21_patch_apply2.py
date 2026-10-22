"""one-off patcher #2 for e21_apply.py: DOC_NULL text"""
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/"
s = open(H + "e21_apply.py", encoding="utf-8").read()
old = '''"푸본현대생명 2024.4Q 26/31 (the FVOCI correction of the annual comparative is not in the 9M comparative); KB손해보험 2024.4Q item 16: the master Q4 cumulative (60,900) is a stale value "
            "(FY2025 annual comparative 380,949, outside this load) so the single quarter must not be derived from it. REMOVED the 2026-10-22 pins'''
new = '''"푸본현대생명 2024.4Q 26/31 (the FVOCI correction of the annual comparative is not in the 9M comparative). REMOVED the 2026-10-22 pins'''
assert s.count(old) == 1
s = s.replace(old, new)
s = s.replace("KB손해보험 2023.4Q (15 cells), 미래에셋생명 2023.4Q (11), 에이비엘생명 2024.4Q 26/31, \"\n            \"푸본현대생명", "KB손해보험 2023.4Q (15 cells), 미래에셋생명 2023.4Q (11), 에이비엘생명 2024.4Q 26/31, \"\n            \"푸본현대생명")
open(H + "e21_apply.py", "w", encoding="utf-8", newline="\n").write(s)
print("patched apply2")
