#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit the re-issued PL_breakdown_provenance.json against the master.  Exit 1 on any
failure.  This is the verification command quoted in the inbox reply."""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
CN = {4, 5, 6, 9, 10, 11, 13, 14}
fails = []

doc = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))

master = {}
for r in rows:
    try:
        it = int(r.get("항목번호"))
    except (TypeError, ValueError):
        continue
    if not (r.get("원보험사코드") and r.get("공시분기")):
        continue
    k = (r["원보험사코드"], r["공시분기"], "contract_notes" if it in CN else "income_statement")
    master.setdefault(k, []).append((it, r.get("값")))

cells = doc["cells"]
keys = [(c["company_code"], c["quarter"], c["item_block"]) for c in cells]
print(f"sidecar cells = {len(cells)}   master cells = {len(master)}")

if len(keys) != len(set(keys)):
    fails.append(f"duplicate sidecar keys: {len(keys)-len(set(keys))}")
missing = set(master) - set(keys)
extra = set(keys) - set(master)
if missing:
    fails.append(f"master cells with NO sidecar entry: {len(missing)} e.g. {sorted(missing)[:3]}")
if extra:
    fails.append(f"sidecar cells not in master: {len(extra)} e.g. {sorted(extra)[:3]}")

if "source_file" in doc.get("fields_pending_downloader", []):
    fails.append("source_file still listed in fields_pending_downloader")
if "source_file" not in doc.get("fields_owned", []):
    fails.append("source_file not listed in fields_owned")
print(f"generated_at = {doc['generated_at']}   "
      f"fields_pending_downloader = {doc['fields_pending_downloader']}")

n_null = 0
for c in cells:
    k = (c["company_code"], c["quarter"], c["item_block"])
    pub = [i for i, v in master.get(k, []) if v is not None]
    if c.get("published_items") != len(pub):
        fails.append(f"{k}: published_items={c.get('published_items')} but master has {len(pub)}")
    sf = c.get("source_file")
    if sf is None:
        n_null += 1
        if not c.get("unresolved_reason"):
            fails.append(f"{k}: source_file null without unresolved_reason")
    elif not (ROOT / sf).exists():
        fails.append(f"{k}: source_file {sf} does not exist on disk")
    # no filing path may be claimed for builder-fabricated items
    bd = set(c.get("builder_derived_items") or [])
    for b in c.get("source_files", []):
        if b["file"] and set(b["items"]) & bd:
            fails.append(f"{k}: builder-fabricated items {sorted(set(b['items']) & bd)} "
                         f"attributed to file {b['file']}")
    # every published item must appear in exactly one bucket
    listed = [i for b in c.get("source_files", []) for i in b["items"]]
    if sorted(listed) != sorted(pub):
        fails.append(f"{k}: bucket items {sorted(listed)} != published {sorted(pub)}")

print(f"source_file null = {n_null}")
print("source_id:", dict(Counter(c["source_id"] for c in cells)))
print("unresolved_reason:", dict(Counter(c.get("unresolved_reason") for c in cells
                                         if c.get("unresolved_reason"))))
print("builder_derived values =",
      sum(len(c.get("builder_derived_items") or []) for c in cells),
      "in", sum(1 for c in cells if c.get("builder_derived_items")), "cells")
bysrc = Counter()
for c in cells:
    for b in c.get("source_files", []):
        bysrc[b["how"]] += len(b["items"])
print("published values by attribution:", dict(bysrc.most_common()))
print("total published values =", sum(bysrc.values()),
      "/ master non-null =", sum(1 for v in master.values() for _, x in v if x is not None))

print("\nFAILURES:", len(fails))
for f in fails[:25]:
    print("  ", f)
sys.exit(1 if fails else 0)
