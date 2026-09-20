#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adversarial checks on the emit_pl_provenance attribution before it is written:
 (1) contract_notes blocks whose ONLY published items are the 생보 13/14 zero convention
     (assemble() sets v[13]=v[14]=0.0 for is_life) -> attributing those to the raw filing
     would be an overclaim;
 (2) spot-check known cells against the earlier evidence probes."""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
CN = {4, 5, 6, 9, 10, 11, 13, 14}
vals, life = {}, {}
for r in rows:
    try:
        it = int(r.get("항목번호"))
    except (TypeError, ValueError):
        continue
    k = (r.get("원보험사코드"), r.get("공시분기"))
    vals.setdefault(k, {})[it] = r.get("값")
    life[r.get("원보험사코드")] = r.get("생손보여부")

only1314, zero1314 = [], Counter()
for k, v in vals.items():
    pub = sorted(i for i in CN if v.get(i) is not None)
    if not pub:
        continue
    if life[k[0]] == "생명보험":
        if set(pub) <= {13, 14}:
            only1314.append((k, pub, [v[i] for i in pub]))
        if 13 in pub and v[13] == 0.0 and 14 in pub and v[14] == 0.0:
            zero1314["life_1314_both_zero"] += 1
print(f"생보 contract_notes blocks whose published items ⊆ {{13,14}} = {len(only1314)}")
for k, pub, vv in only1314[:20]:
    print("   ", k, pub, vv)
print("생보 blocks with 13==14==0.0 (convention present alongside real note items):",
      dict(zero1314))

# item 6 / 11 exactly 0.0 (may be the owner 0-fill convention rather than a disclosed 0)
z6 = sum(1 for v in vals.values() if v.get(6) == 0.0)
z11 = sum(1 for v in vals.values() if v.get(11) == 0.0)
print(f"\nblocks with item6 == 0.0: {z6}   item11 == 0.0: {z11}")

# ---- spot checks against the written sidecar draft ------------------------- #
p = ROOT / "PL_breakdown_provenance.json"
if p.exists():
    doc = json.loads(p.read_text(encoding="utf-8"))
    idx = {(c["company_code"], c["quarter"], c["item_block"]): c for c in doc["cells"]}
    for key in [("KR0008", "2023.1Q", "income_statement"),
                ("KR0001", "2023.1Q", "income_statement"),
                ("KR0001", "2023.1Q", "contract_notes"),
                ("KR0029", "2024.4Q", "income_statement"),
                ("KR0029", "2024.4Q", "contract_notes"),
                ("KR0009", "2023.1Q", "income_statement"),
                ("KR0002", "2023.4Q", "income_statement"),
                ("KR0069", "2026.2Q", "income_statement")]:
        c = idx.get(key)
        print(f"\n{key}")
        if not c:
            print("   ABSENT")
            continue
        print(f"   source_id={c['source_id']} resolution={c.get('resolution')} "
              f"published={c['published_items']}")
        print(f"   source_file={c.get('source_file')}")
        for sf in c.get("source_files", []):
            print(f"     - {sf['how']}: {sf['file']}  items={sf['items']}")
