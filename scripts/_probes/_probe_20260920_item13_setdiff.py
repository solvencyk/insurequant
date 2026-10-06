# -*- coding: utf-8 -*-
"""Cell-by-cell set diff: my 55 vs validation's 55 (mirror_channel probe). Read-only."""
import json, io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + os.sep
D = os.path.join(ROOT, "data", "_derived")

mine = {(r["code"], r["q"]) for r in
        json.load(io.open(os.path.join(D, "_probe_20260920_item13_final_set.json"), encoding="utf-8"))["delete"]}
val = {(r["code"], r["q"]) for r in
       json.load(io.open(os.path.join(D, "_probe_20260920_mirror_channel.json"), encoding="utf-8"))["rows"]
       if r.get("group") == "CONTAM" and r.get("item13_mirror_wrong")}
orch = {(r["code"], r["q"]) for r in
        json.load(io.open(os.path.join(D, "_probe_20260920_item13_deletion_set.json"), encoding="utf-8"))["rows"]
        if r.get("cls_tol1_5") == "OVER"}

print("mine(parser, Dtier-gated) = %d" % len(mine))
print("validation(CONTAM-filtered) = %d" % len(val))
print("orchestrator(over_by sweep) = %d" % len(orch))
print("mine == validation ?", mine == val)
print("mine - validation:", sorted(mine - val))
print("validation - mine:", sorted(val - mine))
print("orchestrator - mine:", sorted(orch - mine))
print("mine - orchestrator:", sorted(mine - orch))
