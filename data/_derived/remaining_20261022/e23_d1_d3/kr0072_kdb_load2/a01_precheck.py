# -*- coding: utf-8 -*-
"""KR0072 KDB load 2 precheck (read-only).
Facts established before anything is written:
  1. the seven apply files (masters, provenance, gold, CSM gold) are byte-identical to the state after the Hyundai (KR0009) load of this chain
     (kr0009_hyundai/apply_manifest_e23_hd.json after_sha256);
  2. the ledger of gold-overlay pins is identical to git HEAD;
  3. tests/test_rule_coverage_manifest.py, tests/fixtures/master_tables_golden.json and scripts/validate_master_tables.py are the validation agent's post-cleanup copies
     (gate_cleanup/post_copies), and the validation edit relative to the Hyundai state (gate_cleanup/pre_copies) is the only difference;
  4. no KR0072 cell of the PL / CSM masters, the gold files or the provenance files differs from git HEAD (no earlier KDB load is in the tree).
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EVD = ROOT / "data/_derived/remaining_20261022/e23_d1_d3"
sys.stdout.reconfigure(encoding="utf-8")


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def sha(rel):
    return sha_b((ROOT / rel).read_bytes())


def git_show(rel):
    r = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + rel], capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"git show HEAD:{rel} failed: {r.stderr[:200]!r}")
    return r.stdout


ok = True
man = json.loads((EVD / "kr0009_hyundai/apply_manifest_e23_hd.json").read_text(encoding="utf-8"))
print("== 1. apply files vs the Hyundai after_sha256")
for rel, h in man["after_sha256"].items():
    if rel.startswith("tests/"):
        continue
    same = sha(rel) == h
    ok = ok and same
    print(f"  {rel}: live == Hyundai after_sha256 : {same}")

print("== 2. gold-overlay ledger vs git HEAD")
rel = "data/_gold/gold_overlay_ledger.json"
# the working-tree copy is CRLF while the git blob is LF (core.autocrlf=true): compare with line endings normalised, and as parsed JSON
live_b = (ROOT / rel).read_bytes()
head_b = git_show(rel)
same = live_b.replace(b"\r\n", b"\n") == head_b.replace(b"\r\n", b"\n") and json.loads(live_b.decode("utf-8")) == json.loads(head_b.decode("utf-8"))
ok = ok and same
has_crlf = b"\r\n" in live_b
print(f"  {rel}: == HEAD (line endings normalised, CRLF in working tree: {has_crlf}) : {same}")

print("== 3. validation cleanup copies")
GC = EVD / "gate_cleanup"
pairs = [("tests/test_rule_coverage_manifest.py", "test_rule_coverage_manifest.py"),
         ("tests/fixtures/master_tables_golden.json", "master_tables_golden.json"),
         ("scripts/validate_master_tables.py", "validate_master_tables.py")]
for rel, name in pairs:
    post = sha_b((GC / "post_copies" / name).read_bytes())
    pre = sha_b((GC / "pre_copies" / name).read_bytes())
    cur = sha(rel)
    print(f"  {rel}: live == validation post copy : {cur == post} ; live == pre copy : {cur == pre}")
    ok = ok and cur == post
print("  pre copy of the test file == Hyundai after_sha256 of the test file :",
      sha_b((GC / "pre_copies/test_rule_coverage_manifest.py").read_bytes()) == man["after_sha256"]["tests/test_rule_coverage_manifest.py"])

print("== 4. KR0072 cells of the live files vs git HEAD")
CODE = "KR0072"


def rows_of(raw):
    return json.loads(raw.decode("utf-8"))


for rel in ("PL_breakdown.json", "CSM_waterfall.json"):
    live = [r for r in rows_of((ROOT / rel).read_bytes()) if r.get("원보험사코드") == CODE]
    head = [r for r in rows_of(git_show(rel)) if r.get("원보험사코드") == CODE]
    same = live == head
    ok = ok and same
    print(f"  {rel}: KR0072 rows live {len(live)} head {len(head)} identical : {same}")
for rel in ("data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json"):
    live = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    head = json.loads(git_show(rel).decode("utf-8"))
    ls = [e for e in live["set"] if e.get("원보험사코드") == CODE]
    hs = [e for e in head["set"] if e.get("원보험사코드") == CODE]
    same = ls == hs
    ok = ok and same
    extra = ""
    if rel.endswith("user_pl_cells.json"):
        for key in ("null_dangi", "set_dangi"):
            a = [x for x in live[key]["cells"] if x[0] == CODE]
            b = [x for x in head[key]["cells"] if x[0] == CODE]
            extra += f" | {key} KR0072 cells live {len(a)} head {len(b)} identical : {a == b}"
            ok = ok and a == b
    print(f"  {rel}: KR0072 gold set entries live {len(ls)} head {len(hs)} identical : {same}{extra}")
for rel in ("PL_breakdown_provenance.json", "CSM_waterfall_provenance.json"):
    live = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    head = json.loads(git_show(rel).decode("utf-8"))
    lc = [c for c in live["cells"] if c.get("company_code") == CODE]
    hc = [c for c in head["cells"] if c.get("company_code") == CODE]
    same = lc == hc
    ok = ok and same
    print(f"  {rel}: KR0072 blocks live {len(lc)} head {len(hc)} identical : {same}")

print("ALL OK" if ok else "MISMATCH")
