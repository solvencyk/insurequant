# -*- coding: utf-8 -*-
"""read-only: sha256 of the files around the masters that this load must NOT change (panels, NB, xlsx, other masters, fixtures, gate scripts, ledgers, baselines, exception registries).
  a03_side_hashes.py snapshot <tag>        -> side_hashes_<tag>.txt
  a03_side_hashes.py diff <tagA> <tagB>    -> prints every path whose hash differs / appeared / vanished"""
import hashlib
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
GLOBS = ["*.json", "*.xlsx", "data/dart/viz/*.json", "data/_gold/*.json", "tests/fixtures/*.json", "tests/*.py", "scripts/*.py", "scripts/pl_breakdown/*.py", "public_exports/manifest.json",
         "data/_derived/qoq_warn.json", "data/_derived/pl_oci_vs_bs_aoci_warn.json", "data/_derived/*.json"]
TOUCHABLE = {"PL_breakdown.json", "PL_breakdown_provenance.json", "CSM_waterfall.json", "CSM_waterfall_provenance.json", "data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json",
             "data/_gold/gold_overlay_ledger.json", "tests/test_rule_coverage_manifest.py", "tests/fixtures/master_tables_golden.json", "tests/fixtures/builder_input_fingerprints.json",
             "data/_derived/qoq_warn.json", "data/_derived/pl_oci_vs_bs_aoci_warn.json"}


def snap():
    out = {}
    for g in GLOBS:
        for p in sorted(ROOT.glob(g)):
            if p.is_file():
                rel = p.relative_to(ROOT).as_posix()
                out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def load(tag):
    d = {}
    for line in (HERE / f"side_hashes_{tag}.txt").read_text(encoding="utf-8").splitlines():
        h, _, rel = line.partition(" *")
        d[rel] = h
    return d


if sys.argv[1] == "snapshot":
    s = snap()
    (HERE / f"side_hashes_{sys.argv[2]}.txt").write_text("\n".join(f"{h} *{r}" for r, h in sorted(s.items())) + "\n", encoding="utf-8", newline="\n")
    print("files hashed:", len(s))
else:
    a, b = load(sys.argv[2]), load(sys.argv[3])
    ch = sorted(r for r in set(a) | set(b) if a.get(r) != b.get(r))
    print(f"changed/appeared/vanished: {len(ch)}")
    for r in ch:
        print(("  expected-touchable " if r in TOUCHABLE else "  UNEXPECTED         ") + r, "| before", (a.get(r) or "-")[:12], "after", (b.get(r) or "-")[:12])
    print("UNEXPECTED count:", sum(1 for r in ch if r not in TOUCHABLE))
