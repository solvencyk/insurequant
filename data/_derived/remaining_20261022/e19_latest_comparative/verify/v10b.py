import json, collections
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
V = ROOT + "/data/_derived/remaining_20261022/e19_latest_comparative/verify/"
SP = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
h = json.load(open(SP + "/head_PLprov.json", encoding="utf-8"))
c = json.load(open(ROOT + "/PL_breakdown_provenance.json", encoding="utf-8"))
B = {"KR0082": ["2023.3Q"], "KR0032": ["2023.4Q","2024.1Q","2024.2Q","2024.3Q"], "KR0104": ["2023.3Q"],
     "KR0087": ["2023.4Q","2024.1Q","2024.2Q","2024.3Q"], "KR0070": ["2024.1Q","2024.2Q","2024.3Q"],
     "KR0083": ["2024.1Q","2024.2Q"], "KR0005": ["2023.3Q","2023.4Q","2024.1Q","2024.2Q"]}
want = {(k, q) for k, v in B.items() for q in v}
kf = lambda e: json.dumps(e, sort_keys=True, ensure_ascii=False)
hs = collections.Counter(kf(e) for e in h["cells"]); cs = collections.Counter(kf(e) for e in c["cells"])
rm = {(json.loads(x)["company_code"], json.loads(x)["quarter"], json.loads(x)["item_block"]) for x in (hs - cs).elements()}
ad = {(json.loads(x)["company_code"], json.loads(x)["quarter"], json.loads(x)["item_block"]) for x in (cs - hs).elements()}
o = ["removed==added keys: %s ; n=%d ; equals the 19 buckets income_statement: %s" % (rm == ad, len(rm), {(a, b) for a, b, _ in rm} == want and all(x[2] == "income_statement" for x in rm))]
# non-cells top-level keys identical except new merge note
diff = [k for k in set(h) | set(c) if k != "cells" and h.get(k) != c.get(k)]
o.append("top-level keys differing outside cells: %s" % diff)
# fields of each added block: do published items values stay consistent? check generated_at unchanged
o.append("generated_at head=%s cur=%s" % (h["generated_at"], c["generated_at"]))
open(V + "v10b.txt", "w", encoding="utf-8").write("\n".join(o))
