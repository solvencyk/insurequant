# -*- coding: utf-8 -*-
import json
from pathlib import Path
H = Path(__file__).resolve().parent
raw = (H / "plan_KR0032.json").read_bytes()
p = json.loads(raw.decode("utf-8"))
v = p["verification"]
L = [f"bom={raw[:3] == b'\xef\xbb\xbf'} bytes={len(raw)}"]
L.append("top keys: " + ",".join(p.keys()))
L.append("buckets: " + json.dumps([(b['quarter'], b['adopt'], b['n_cells'], b['lob_bridge']) for b in p['buckets']], ensure_ascii=False))
for k in ("master_equals_original_print_all", "n_master_vs_original_cells", "census_vs_xml", "note_table_vs_xml", "third_xml_source", "gold"):
    L.append(k + ": " + json.dumps(v[k], ensure_ascii=False, default=str))
pt = v["printed_three_month_check"]
L.append(f"3m: n={pt['n']} ok={pt['n_ok']} max={pt['max_abs_diff']}")
L.append("apply_contract.expected: " + json.dumps(p["apply_contract"]["expected_master_changes"], ensure_ascii=False))
L.append("null_dangi_cells: " + json.dumps(p["apply_contract"]["null_dangi_cells"]))
L.append("gold_set_cells n=%d first=%s" % (len(p["apply_contract"]["gold_set_cells"]), p["apply_contract"]["gold_set_cells"][0]))
L.append("seam[0]: " + json.dumps(p["seam_cells"][0], ensure_ascii=False)[:1500])
L.append("closure after (2023.4Q): " + json.dumps([(x['name'], x['resid'], x['ok'], x['ok_gate']) for x in p['buckets'][0]['closure_merged_after']], ensure_ascii=False))
(H / "KR0032_s4_summary.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
