"""Read-only: pivot census_blocks.csv (domain x verdict -> blocks / cells) and list the adoption blocks; type tables from classification.csv."""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
cens = list(csv.DictReader(open(HERE / "census_blocks.csv", encoding="utf-8-sig")))
piv = defaultdict(lambda: [0, 0, 0])
for c in cens:
    p = piv[(c["domain"], c["verdict"])]
    p[0] += 1
    p[1] += int(c["n_diff"] or 0)
    p[2] += int(c["n_filled"] or 0)
print("domain | verdict | blocks | cells_differ | cells_filled")
for k in sorted(piv):
    print(" | ".join([k[0], k[1], str(piv[k][0]), str(piv[k][1]), str(piv[k][2])]))
tot = defaultdict(lambda: [0, 0, 0])
for (d, v), (b, n, f) in piv.items():
    tot[v][0] += b
    tot[v][1] += n
    tot[v][2] += f
print("\nTOTAL by verdict")
for v in sorted(tot):
    print(v, tot[v])
print("\nadoption blocks")
for c in cens:
    if c["verdict"].startswith("최신 채택"):
        print(c["verdict"], "|", c["domain"], c["code"], c["company"][:8], c["quarter"], "| diff", c["n_diff"], "fill", c["n_filled"], "|", c["joint_group"])
cls = list(csv.DictReader(open(HERE / "classification.csv", encoding="utf-8-sig")))
core = [r for r in cls if r["status"] not in ("gold_overlay", "released", "informational", "resolved_prior_round")]
print("\ncore", len(core), "by type before", dict(Counter(r["type"] for r in core)), "after", dict(Counter(r["type_after_dryrun"] for r in core)))
print("all", len(cls), "before", dict(Counter(r["type"] for r in cls)), "after", dict(Counter(r["type_after_dryrun"] for r in cls)))
print("core by status", dict(Counter(r["status"] for r in core)))
print("core type x status:")
c2 = Counter((r["type_after_dryrun"], r["status"]) for r in core)
for k in sorted(c2):
    print("  ", k, c2[k])
print("core A rows verdict:", dict(Counter(r["dry_run_verdict"][:40] for r in core if r["type_after_dryrun"] == "A")))
