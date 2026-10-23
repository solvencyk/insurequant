# -*- coding: utf-8 -*-
"""Post-apply provenance repair (pass3): the sandbox emitter that p3_apply.py uses replaced the KR0032 2023.2Q income_statement block and thereby dropped its hand-curated lineage entry
`disclosure_summary_pl` (data/disclosure/FY2023_Q2/raw/KR0032_NH농협손해보험_amended.pdf, items 16 / 22 / 23 / 24) and labelled item 16 as raw_filing_derived.  Items 22 / 23 / 24 now come from the gold overlay (FY2024_Q2
prior cumulative column); item 16 (41,900) is STILL the disclosure-summary value.  Repair: raw_filing_derived keeps items [2, 3, 8], and the disclosure_summary_pl entry is re-inserted VERBATIM from the pre-apply backup with
items [16] only.  Writes PL_breakdown_provenance.json (exact-format JSON writer of the audited helpers) and updates the after-hash in apply_manifest_p3.json so that `--revert --apply` keeps working."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3")
import p3_apply as A

ROOT, EV = A.ROOT, A.EV
rel = "PL_breakdown_provenance.json"
bk = json.loads((EV / "backup_before_apply" / rel).read_text(encoding="utf-8"))
live = A.ak.JsonFile(rel)
man_path = EV / "apply_manifest_p3.json"
man = json.loads(man_path.read_text(encoding="utf-8"))
assert A.ak.sha((ROOT / rel).read_bytes()) == man["after_sha256"][rel], "the live sidecar is not the post-apply one"
key = ("KR0032", "2023.2Q", "income_statement")
old = next(c for c in bk["cells"] if (c["company_code"], c["quarter"], c["item_block"]) == key)
ent = [f for f in old["source_files"] if f["how"] == "disclosure_summary_pl"]
assert len(ent) == 1 and ent[0]["items"] == [16, 22, 23, 24], ent
blk = next(c for c in live.obj["cells"] if (c["company_code"], c["quarter"], c["item_block"]) == key)
assert not any(f["how"] == "disclosure_summary_pl" for f in blk["source_files"])
raw = [f for f in blk["source_files"] if f["how"] == "raw_filing_derived"]
assert len(raw) == 1 and raw[0]["items"] == [2, 3, 8, 16], raw
raw[0]["items"] = [2, 3, 8]
new_ent = dict(ent[0])
new_ent["items"] = [16]
i = next(k for k, f in enumerate(blk["source_files"]) if f["how"] == "raw_filing_derived")
blk["source_files"].insert(i + 1, new_ent)
out = A.ak.JsonFile._dump(live.obj, *live.fmt)
A.ak.write_atomic(ROOT / rel, out)
man["after_sha256"][rel] = A.ak.sha(out)
man["note_prov_repair"] = "2026-10-24: KR0032 2023.2Q income_statement lineage: disclosure_summary_pl entry re-inserted from backup_before_apply with items [16] only, raw_filing_derived items [2, 3, 8] (fix_prov_nh_2q.py); after_sha256 of the sidecar updated"
man_path.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("repaired", key, "new sidecar sha", man["after_sha256"][rel])
print(json.dumps(blk["source_files"], ensure_ascii=False)[:900])
