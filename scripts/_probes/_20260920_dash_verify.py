#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Structural diff of the backfill staging file before vs after the dash adjudication:
prove nothing but dash_promotion / dash_adjudication changed."""
import io
import json
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
NEW = ROOT / "data/_derived/pl_backfill_disclosure_20260918.json"
OLD = Path(os.environ.get("TEMP", "")) / "pl_backfill_stg.bak_20260920"

nb, ob = NEW.read_bytes(), OLD.read_bytes()
print(f"old bytes={len(ob)} CRLF={ob.count(b'\r\n')} LF={ob.count(b'\n')}")
print(f"new bytes={len(nb)} CRLF={nb.count(b'\r\n')} LF={nb.count(b'\n')}")
print(f"byte delta={len(nb)-len(ob)}  (line-ending-only delta would be {-ob.count(b'\r\n')})")

new = json.loads(nb.decode("utf-8"))
old = json.loads(ob.decode("utf-8"))


def flat(d):
    out = {}
    for c in d["cells"]:
        k0 = (c.get("원보험사코드"), c.get("공시분기"))
        for f in ("status", "source_file", "page", "backfill_excluded", "equation_summary"):
            out[(k0, "cell", f)] = json.dumps(c.get(f), ensure_ascii=False, sort_keys=True)
        for k, it in (c.get("items") or {}).items():
            for f, v in it.items():
                out[(k0, f"item{k}", f)] = json.dumps(v, ensure_ascii=False, sort_keys=True)
        for k, cp in (c.get("components") or {}).items():
            out[(k0, f"comp{k}", "*")] = json.dumps(cp, ensure_ascii=False, sort_keys=True)
    return out


fn, fo = flat(new), flat(old)
print(f"\nflattened fields: old={len(fo)} new={len(fn)}")
added, removed = set(fn) - set(fo), set(fo) - set(fn)
changed = [k for k in set(fn) & set(fo) if fn[k] != fo[k]]
print(f"added={len(added)} removed={len(removed)} changed={len(changed)}")
bad = [k for k in changed if k[2] != "dash_promotion"]
print(f"changed fields that are NOT dash_promotion = {len(bad)}")
for k in bad[:10]:
    print("   ", k, "\n      old:", fo[k][:160], "\n      new:", fn[k][:160])
for k in list(added)[:10]:
    print("   ADDED", k, fn[k][:120])
for k in list(removed)[:10]:
    print("   REMOVED", k, fo[k][:120])

print("\ntop-level keys added:", sorted(set(new) - set(old)))
print("top-level keys removed:", sorted(set(old) - set(new)))
for k in sorted(set(new) & set(old)):
    if k != "cells" and json.dumps(new[k], ensure_ascii=False, sort_keys=True) != \
            json.dumps(old[k], ensure_ascii=False, sort_keys=True):
        print("top-level CHANGED:", k)

# merge-candidate value census must be untouched
def cand(d):
    n, tot = 0, 0.0
    for c in d["cells"]:
        if c.get("backfill_excluded"):
            continue
        for k, it in (c.get("items") or {}).items():
            if it.get("merge_candidate") and it.get("값") is not None:
                n += 1
                tot += it["값"]
    return n, round(tot, 3)


print("\nmerge candidates (count, sum 백만원): old=%s new=%s" % (cand(old), cand(new)))
sys.exit(1 if (bad or added or removed) else 0)
