# -*- coding: utf-8 -*-
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
new = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
old = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:PL_breakdown_provenance.json"], capture_output=True, stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
ok = {(c["company_code"], c["quarter"], c["item_block"]): c for c in old["cells"]}
for c in new["cells"]:
    if c["company_code"] == "KR0099" and c["quarter"] in ("2023.1Q", "2023.2Q", "2023.3Q"):
        k = (c["company_code"], c["quarter"], c["item_block"])
        print("=" * 100)
        print("NEW", k)
        print(json.dumps(c, ensure_ascii=False, indent=1)[:1800])
        print("OLD", json.dumps(ok.get(k), ensure_ascii=False)[:700])
print(new["merge_note_20261023_e23_kr0099_kblife"])
csm = json.loads((ROOT / "CSM_waterfall_provenance.json").read_text(encoding="utf-8"))
for c in csm["cells"]:
    if c["company_code"] == "KR0099" and c["quarter"] in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
        print("CSM", c["quarter"], c["item_block"], "owner_override", c.get("owner_override"), json.dumps({k: v for k, v in c.items() if k not in ("company_code", "quarter", "item_block")}, ensure_ascii=False)[:300])
