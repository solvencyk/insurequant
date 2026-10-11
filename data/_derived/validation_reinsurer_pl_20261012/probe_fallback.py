# -*- coding: utf-8 -*-
"""verify_provenance_sidecar 의 (회사, 분기) 블록불문 폴백 매칭이 라이브 PL 에서 실제로 쓰이는 셀 수를 센다(읽기 전용)."""
import json
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
CN = {4, 5, 6, 9, 10, 11, 13, 14}
side = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
keys = {(c["company_code"], c["quarter"], c["item_block"]) for c in side["cells"]}
pub = set()
for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")):
    try:
        it = int(r.get("항목번호"))
    except (TypeError, ValueError):
        continue
    if r.get("값") is None:
        continue
    pub.add((r["원보험사코드"], r["공시분기"], "contract_notes" if it in CN else "income_statement"))
missing = sorted(pub - keys)
print("published blocks", len(pub), "sidecar blocks", len(keys), "published-but-exact-key-missing", len(missing))
for m in missing[:30]:
    print(m)
