"""cell-level diff of the working IFRS17_BS.json vs git HEAD; expects exactly the 6 KR0073 cells."""
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
head = json.loads(subprocess.run(["git", "show", "HEAD:IFRS17_BS.json"], cwd=R, capture_output=True, check=True).stdout.decode("utf-8"))
cur = json.loads(open(R + "IFRS17_BS.json", encoding="utf-8").read())
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
h = {key(r): r for r in head}; c = {key(r): r for r in cur}
assert len(h) == len(head) and len(c) == len(cur)
added = sorted(set(c) - set(h)); removed = sorted(set(h) - set(c))
changed = sorted(k for k in h if k in c and h[k] != c[k])
print("rows head/cur:", len(head), len(cur), "added", len(added), "removed", len(removed), "changed", len(changed))
for k in changed:
    meta = {f for f in h[k] if h[k][f] != c[k].get(f)}
    print(k, h[k]["값"], "->", c[k]["값"], "delta", round(c[k]["값"] - h[k]["값"], 6), "fields", sorted(meta))
exp = {("KR0073", 1, "2023.4Q"), ("KR0073", 2, "2023.4Q"), ("KR0073", 3, "2023.4Q"), ("KR0073", 20, "2023.4Q"), ("KR0073", 31, "2023.4Q"), ("KR0073", 1, "2024.4Q")}
print("EXACTLY_THE_6_CELLS:", set(changed) == exp and not added and not removed)
