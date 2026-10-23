# -*- coding: utf-8 -*-
"""READ-ONLY: show the KR0009 2023.1Q / 2023.2Q contract_notes provenance blocks in the backup (pre-apply) and in the live sidecar."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
for tag, path in (("BACKUP", f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass2/backup_before_apply/PL_breakdown_provenance.json"), ("LIVE", f"{ROOT}/PL_breakdown_provenance.json")):
    doc = json.load(open(path, encoding="utf-8"))
    for c in doc["cells"]:
        if c["company_code"] == "KR0009" and c["quarter"] in ("2023.1Q",) and c["item_block"] == "contract_notes":
            print(tag, json.dumps(c, ensure_ascii=False, indent=1))
