import json, io
from pathlib import Path
EVD = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
raw = (EVD / "plan_KR0005.json").read_bytes()
P = json.loads(raw.decode("utf-8"))
out = ["bom=%s bytes=%d" % (raw[:3] == b"\xef\xbb\xbf", len(raw))]
out.append("gold entry sample: " + json.dumps(P["cells"][0]["gold_set_entry"], ensure_ascii=False))
out.append("gold entry sample 19: " + json.dumps([c for c in P["cells"] if c["item"] == 19][0]["gold_set_entry"], ensure_ascii=False))
out.append("verification: " + json.dumps(P["verification"], ensure_ascii=False, indent=1))
for s in P["seam_cells"]:
    out.append("seam: " + json.dumps(s, ensure_ascii=False))
out.append("keys: " + json.dumps(list(P.keys())))
out.append("counts by quarter: " + json.dumps({b["quarter"]: b["n_cells"] for b in P["buckets"]}))
(EVD / "KR0005_s13_audit.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
