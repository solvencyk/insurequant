#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 23 (read-only): final state check -> s23_final_state.txt
 (1) the five written files still carry the post-apply hashes of apply_manifest_e20.json (nobody wrote them afterwards)
 (2) size of the evidence dir and the biggest files (limit for new files: 50 MB)
 (3) pycache / stray files created by my imports under the evidence dir and scripts/"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
L = []
man = json.loads((HERE / "apply_manifest_e20.json").read_text(encoding="utf-8"))
L.append("(1) post-apply hash check (manifest after_sha256 vs current)")
for rel, h in man["after_sha256"].items():
    cur = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    L.append(f"   {rel}: manifest {h} current {cur[:len(h)]} -> {'SAME' if cur.startswith(h) else 'CHANGED'}")
EV = HERE.parent
sizes = sorted(((p.stat().st_size, str(p.relative_to(EV))) for p in EV.rglob("*") if p.is_file()), reverse=True)
L.append(f"(2) evidence dir {EV.relative_to(ROOT)}: {len(sizes)} files, {sum(s for s, _ in sizes) / 1e6:.2f} MB; biggest:")
for s, n in sizes[:5]:
    L.append(f"   {s / 1e6:.2f} MB {n}")
L.append(f"   files over 50 MB: {[n for s, n in sizes if s > 50e6]}")
L.append("(3) __pycache__ dirs under the evidence dir:")
for p in sorted(EV.rglob("__pycache__")):
    L.append(f"   {p.relative_to(ROOT)}")
(HERE / "s23_final_state.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
print("\n".join(L))
