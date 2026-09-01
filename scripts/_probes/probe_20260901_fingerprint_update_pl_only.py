"""Refresh ONE builder's entry in tests/fixtures/builder_input_fingerprints.json.

Why not `validate_golden_input_fingerprints.py --update`: that rewrites EVERY spec from
the current tree.  Right now `post_transition` is also drifting (INPUTS_MOVED) because the
K-ICS lane is editing its md_inbox inputs in this shared worktree.  A blanket --update
would stamp that drift as verified without anyone having run the post_transition golden --
textbook false-green.  This writes only the spec named on the command line and leaves
every other stored fingerprint byte-identical, so the other lane still sees its RED.

usage: probe_20260901_fingerprint_update_pl_only.py <spec_name>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from scripts.validate_golden_input_fingerprints import (  # noqa: E402
    RECORD, SPECS, STAT_ONLY, compute,
)

name = sys.argv[1]
if name not in SPECS:
    raise SystemExit(f"unknown spec {name!r}; known: {sorted(SPECS)}")

record = json.loads(RECORD.read_text(encoding="utf-8"))
before = json.dumps(record["specs"], ensure_ascii=False, sort_keys=True)

spec = SPECS[name]
c = dict(compute(name, spec))
c["_golden"] = spec["golden"]
c["_why_not_in_hook"] = spec["why"]
c["_input_patterns"] = {p: ("stat(path+size)" if p in STAT_ONLY else "content-sha256")
                        for p in spec["inputs"]}
c["_evidence"] = spec["evidence"]

old = record["specs"].get(name, {})
record["specs"][name] = c
RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

# prove nothing else moved
after = json.loads(RECORD.read_text(encoding="utf-8"))["specs"]
for k in sorted(set(after) | set(json.loads(before))):
    if k == name:
        continue
    a = json.dumps(after[k], ensure_ascii=False, sort_keys=True)
    b = json.dumps(json.loads(before)[k], ensure_ascii=False, sort_keys=True)
    print(f"  {k:18s} {'UNCHANGED' if a == b else '*** MOVED ***'}")
print(f"\nupdated spec {name!r} only:")
for f in ("input_files", "input_bytes", "inputs_sha256", "code_sha256", "fixture_sha256"):
    if f in c:
        print(f"    {f}: {old.get(f)} -> {c[f]}")
