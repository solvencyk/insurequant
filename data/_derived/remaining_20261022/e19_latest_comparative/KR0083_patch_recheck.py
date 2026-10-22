p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/KR0083_recheck.py"
s = open(p, encoding="utf-8").read()
old = '            txt = re.sub(r"<[^>]+>", "", " ".join(L[k:ln + 1]))'
new = '            end = k\n            while "</TE>" not in L[end] and end < len(L) - 1: end += 1\n            txt = re.sub(r"<[^>]+>", "", " ".join(L[k:end + 1]))'
assert old in s
open(p, "w", encoding="utf-8").write(s.replace(old, new))
