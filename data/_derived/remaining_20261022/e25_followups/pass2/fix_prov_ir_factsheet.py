# -*- coding: utf-8 -*-
"""Post-apply provenance repair (pass2): the sandbox emitter that p2_apply.py uses replaced the two KR0009 (2023.1Q / 2023.2Q) contract_notes blocks and thereby dropped their hand-curated lineage entry
`ir_factsheet_uw_income_prior_year_cumulative` (items 13 / 14, written in the 2026-10-23 D3 load).  Re-insert that entry VERBATIM from the pre-apply backup right after the owner_gold_overlay entry.
Writes PL_breakdown_provenance.json (exact-format JSON writer of the audited helpers) and updates the after-hash in apply_manifest_p2.json so that `--revert --apply` keeps working."""
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
import p2_apply as A

ROOT = A.ROOT
EV = A.EV
rel = "PL_breakdown_provenance.json"
bk = json.loads((EV / "backup_before_apply" / rel).read_text(encoding="utf-8"))
live = A.ak.JsonFile(rel)
man_path = EV / "apply_manifest_p2.json"
man = json.loads(man_path.read_text(encoding="utf-8"))
assert A.ak.sha((ROOT / rel).read_bytes()) == man["after_sha256"][rel], "the live sidecar is not the post-apply one"
done = []
for q in ("2023.1Q", "2023.2Q"):
    old = next(c for c in bk["cells"] if c["company_code"] == "KR0009" and c["quarter"] == q and c["item_block"] == "contract_notes")
    ent = [f for f in old["source_files"] if f["how"] == "ir_factsheet_uw_income_prior_year_cumulative"]
    assert len(ent) == 1, (q, len(ent))
    blk = next(c for c in live.obj["cells"] if c["company_code"] == "KR0009" and c["quarter"] == q and c["item_block"] == "contract_notes")
    assert not any(f["how"] == "ir_factsheet_uw_income_prior_year_cumulative" for f in blk["source_files"])
    i = next(k for k, f in enumerate(blk["source_files"]) if f["how"] == "owner_gold_overlay")
    blk["source_files"].insert(i + 1, ent[0])
    done.append(q)
out = A.ak.JsonFile._dump(live.obj, *live.fmt)
A.ak.write_atomic(ROOT / rel, out)
man["after_sha256"][rel] = A.ak.sha(out)
man["note_prov_repair"] = "2026-10-24: KR0009 2023.1Q/2023.2Q contract_notes ir_factsheet lineage entry re-inserted verbatim from backup_before_apply (fix_prov_ir_factsheet.py); after_sha256 of the sidecar updated"
man_path.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("repaired", done, "new sidecar sha", man["after_sha256"][rel])
