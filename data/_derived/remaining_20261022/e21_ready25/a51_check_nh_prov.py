# -*- coding: utf-8 -*-
"""READ-ONLY: provenance source_id of KR0104 2023.1Q/2Q income_statement blocks at HEAD and now."""
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
live = json.load(open(f"{ROOT}/PL_breakdown_provenance.json", encoding="utf-8"))
head = json.loads(subprocess.run(["git", "-C", ROOT, "show", "HEAD:PL_breakdown_provenance.json"], capture_output=True, stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
for tag, d in (("HEAD", head), ("LIVE", live)):
    for c in d["cells"]:
        if c["company_code"] == "KR0104" and c["quarter"] in ("2023.1Q", "2023.2Q") and c["item_block"] == "income_statement":
            print(tag, c["quarter"], c.get("source_id"), c.get("resolution"), c.get("published_items"), c.get("owner_override"))
