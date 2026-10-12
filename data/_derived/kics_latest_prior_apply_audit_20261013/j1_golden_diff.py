import sys, os, json, subprocess, collections, importlib
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
sys.path.insert(0, REPO + "/src"); sys.path.insert(0, REPO + "/scripts"); sys.path.insert(0, REPO + "/tests")
here = os.path.dirname(os.path.abspath(__file__))
import test_kics_rules_golden as T
from solvency.validation.kics_json_rules import run_validation
from validate_kics_disclosure import (_load_life_subrisk_applicability, _load_life_subrisk_source_absent, _load_tfi_applicability, _scan_breakdown_presence)
def run(records):
    return run_validation(records, source_has_breakdown=_scan_breakdown_presence(records), tfi_applicability=_load_tfi_applicability(),
                          life_subrisk_applicability=_load_life_subrisk_applicability(), life_subrisk_source_absent=_load_life_subrisk_source_absent())
def load(rev):
    return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:kics_disclosure.json"]).decode("utf-8"))
golden = json.load(open(REPO + "/tests/fixtures/kics_rules_golden.json", encoding="utf-8"))
out = open(here + "/j1_golden_diff.txt", "w", encoding="utf-8")
rb = run(load("74a415bf^")); ra = run(load("74a415bf"))
mb = T._manifest(rb); ma = T._manifest(ra)
out.write(f"golden sha  {golden['sha256']}\nbaseline(74a415bf^) sha {mb['sha256']}  == golden: {mb['sha256']==golden['sha256']}\ncurrent(74a415bf) sha {ma['sha256']}\n")
out.write(f"golden by_status {golden['by_status']}\nbaseline by_status {mb['by_status']}\ncurrent by_status {ma['by_status']}\n")
# is HEAD master == 74a415bf master?
head = json.loads(open(REPO + "/kics_disclosure.json", encoding="utf-8").read())
mh = T._manifest(run(head))
out.write(f"working-tree master sha {mh['sha256']} == current: {mh['sha256']==ma['sha256']}\n")
def mat(rep): return collections.Counter((f["원보험사코드"], f["공시분기"], f["rule"], f["status"]) for f in rep["findings"])
cb, ca = mat(rb), mat(ra)
rem, add = cb - ca, ca - cb
BL = {("KR0003","2023.4Q"),("KR0003","2025.1Q"),("KR0004","2023.1Q"),("KR0004","2024.1Q"),("KR0009","2023.1Q"),("KR0009","2023.2Q"),("KR0032","2024.3Q"),("KR0049","2025.1Q"),("KR0049","2026.1Q"),("KR0050","2025.3Q"),("KR0069","2024.2Q"),("KR0071","2024.4Q"),("KR0072","2025.2Q"),("KR0080","2026.1Q"),("KR0095","2024.4Q"),("KR0099","2024.3Q")}
outside = [k for k in list(rem) + list(add) if (k[0], k[1]) not in BL]
out.write(f"moved entries: removed {sum(rem.values())} added {sum(add.values())}; outside the 16 applied blocks: {len(outside)} {outside}\n")
rows_bad = [(k, v) for k, v in (rem + add).items() if v != 1]
