"""Cell-level diff of HEAD vs working tree for IFRS17_BS.json and insurance_liability_portfolio.json (all fields)."""
import json, subprocess, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
def head(path):
    b = subprocess.run(["git", "-C", R, "show", "HEAD:" + path], capture_output=True).stdout
    return json.loads(b.decode("utf-8")), hashlib.sha256(b).hexdigest()
def work(path):
    b = open(R + path, "rb").read()
    return json.loads(b.decode("utf-8")), hashlib.sha256(b).hexdigest(), b[:3]
for path in ["IFRS17_BS.json", "insurance_liability_portfolio.json"]:
    h, hs = head(path); w, ws, bom = work(path)
    print("==", path, "rows head", len(h), "work", len(w), "sha", hs[:8], ws[:8], "bom", bom == b"\xef\xbb\xbf")
    def key(r):
        return (r["원보험사코드"], r["항목번호"], r["공시분기"], r.get("항목명"))
    hd = {}; wd = {}
    for r in h: hd.setdefault(key(r), []).append(r)
    for r in w: wd.setdefault(key(r), []).append(r)
    print("dup keys head", sum(1 for v in hd.values() if len(v) > 1), "work", sum(1 for v in wd.values() if len(v) > 1))
    added = [k for k in wd if k not in hd]; removed = [k for k in hd if k not in wd]
    print("added", added, "removed", removed)
    n = 0
    for k in hd:
        if k in wd and hd[k] != wd[k]:
            n += 1
            a, b = hd[k][0], wd[k][0]
            fields = {f: (a.get(f), b.get(f)) for f in set(a) | set(b) if a.get(f) != b.get(f)}
            print("CHANGED", k, fields)
    print("changed cells:", n)
