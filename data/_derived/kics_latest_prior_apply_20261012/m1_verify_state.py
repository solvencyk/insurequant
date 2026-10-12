"""m1_verify_state.py -- READ-ONLY resume check: is the working tree exactly what this ticket intended?

 A. master  : live kics_disclosure.json vs plans/*.json AND vs applied_blocks.csv (cell guard: live == new, git HEAD == old), nothing else changed vs HEAD
 B. ledger  : data/_gold/kics_restatement_ledger.json entries == class-R/T cells of the plans, adopted_basis as_restated, values match the master
 C. release : the two registry keys are gone from the code, every other registry entry equals HEAD; provenance records of the two = CONTRADICTED, nothing else changed
 D. xlsx    : sheet 'K-ICS공시' == master (scripts/check_master_xlsx_drift.py is the gate; here: only that sheet differs from HEAD's xlsx, by value)
"""
import csv
import importlib.util
import io
import subprocess
import sys
import zipfile

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/src")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
live = read_rows()
head = head_rows()
lk, hk = {key(r): r for r in live}, {key(r): r for r in head}
mp = merge_plans(APPLIED)
planned = {(e["code"], e["q"], e["item"], e["field"]): (e["old"], e["new"]) for e in mp["edits"]}

# ---- A. master
bad = []
for (c, q, it, f), (old, new) in planned.items():
    if lk[(c, q, it)].get(f, "<nokey>") != new:
        bad.append(("live != plan new", c, q, it, f))
    if hk[(c, q, it)].get(f, "<nokey>") != old:
        bad.append(("HEAD != plan old", c, q, it, f))
rows = list(csv.DictReader(open(OUT / "applied_blocks.csv", encoding="utf-8-sig")))
n_csv = 0
for r in rows:
    k = (r["code"], r["quarter"], int(r["item"]), r["field"])
    old, new = planned[k]
    n_csv += 1
    if str(old) != r["old"] or str(new) != r["new"]:
        bad.append(("csv != plan", *k))
    if str(lk[k[:3]].get(k[3])) != r["new"] or str(hk[k[:3]].get(k[3])) != r["old"]:
        bad.append(("csv vs live/HEAD", *k))
diff = {}
for k, hr in hk.items():
    lr = lk[k]
    for f in set(hr) | set(lr):
        if hr.get(f, "<nokey>") != lr.get(f, "<nokey>"):
            diff[(*k, f)] = (hr.get(f, "<nokey>"), lr.get(f, "<nokey>"))
print(f"A. master: sha {sha_file(MASTER)[:12]} rows {len(live)} (HEAD {len(head)}) | plan cells {len(planned)} | applied_blocks.csv rows {n_csv}")
print(f"   guard violations: {len(bad)} {bad[:3]} | cells differing from HEAD: {len(diff)} == planned: {set(diff) == set(planned)} | key sets equal: {set(lk) == set(hk)}")
assert not bad and set(diff) == set(planned) and set(lk) == set(hk) and len(live) == len(head) and n_csv == len(planned)

# ---- B. ledger
led = read_json(REPO / "data" / "_gold" / "kics_restatement_ledger.json")
ent = led["entries"]
exp = {}
for b in APPLIED:
    p = load_plan(b)
    for ev in p["evidence"]:
        if ev["class"] in ("R", "T"):
            e = [x for x in p["edits"] if x["kind"] == "primary" and x["item"] == ev["item"]][0]
            exp[f"{p['code']}|{p['quarter']}|{ev['item']}"] = (ev["class"], float(e["old"]) if ev["class"] == "R" else float(ev["own_print"]), float(e["new"]))
mine = {k: v for k, v in ent.items() if v.get("adopted_by") == "owner 2026-10-12"}
print(f"B. ledger: entries {len(ent)} (owner 2026-10-12: {len(mine)}) | expected R/T cells {len(exp)}")
missing = sorted(set(exp) - set(mine))
extra = sorted(set(mine) - set(exp))
print("   missing entries:", missing, "| unexpected entries:", extra)
for k, (cls, asf, rest) in exp.items():
    if k in mine:
        e = mine[k]
        c, q, it = k.split("|")
        assert e["adopted_basis"] == "as_restated" and e["as_filed"] == asf and e["restated"] == rest, (k, e["as_filed"], e["restated"], asf, rest)
        assert float(lk[(c, q, int(it))]["값"]) == rest, k
print("   decision record present:", any(d.get("date") == "2026-10-12" for d in led.get("_policy_decisions", [])))

# ---- C. release
def load(path_bytes, name):
    p = OUT / "_tmp" / f"{name}.py"
    p.parent.mkdir(exist_ok=True)
    p.write_bytes(path_bytes)
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

head_src = subprocess.run(["git", "show", "HEAD:scripts/validate_kics_disclosure.py"], cwd=REPO, capture_output=True).stdout
m_old = load(head_src, "vkd_head_check")
m_new = load((REPO / "scripts" / "validate_kics_disclosure.py").read_bytes(), "vkd_live_check")
o, n = m_old._TIER2_ISSUER_INCONSISTENT, m_new._TIER2_ISSUER_INCONSISTENT
print("C. registry: HEAD", len(o), "-> live", len(n), "| removed:", sorted(set(o) - set(n)), "| other entries equal:", all(o[k] == n[k] for k in n))
assert sorted(set(o) - set(n)) == [("KR0003", "2025.1Q"), ("KR0032", "2024.3Q")] and all(o[k] == n[k] for k in n) and set(n) <= set(o)
# rest of the module unchanged: compare source text outside the two removed blocks
a = head_src.decode("utf-8")
b = (REPO / "scripts" / "validate_kics_disclosure.py").read_bytes().decode("utf-8")
import difflib
dl = [l for l in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0) if l and l[0] in "+-" and not l.startswith(("+++", "---"))]
added = [l for l in dl if l[0] == "+"]
removed = [l for l in dl if l[0] == "-"]
print(f"   validate_kics_disclosure.py diff vs HEAD: +{len(added)} / -{len(removed)} lines (all inside the two released registry blocks: {all('KR0003' in l or 'KR0032' in l or l[1:].strip().startswith(('#', 'cells', '\"cells', 'findings', '\"findings', '47', '48', '49', '50', '51', '54', '1:', '2:', '3:', '4:', '12:', '13:', '\"2_tier1_bridge', '(', '},', ')')) or l[1:].strip() == '' for l in dl)})")
prov = read_json(REPO / "data" / "_gold" / "kics_exemption_provenance.json")
hp = json.loads(subprocess.run(["git", "show", "HEAD:data/_gold/kics_exemption_provenance.json"], cwd=REPO, capture_output=True).stdout.decode("utf-8"))
chg = []
for ea, eb in zip(hp["entries"], prov["entries"]):
    ks = [k for k in set(ea) | set(eb) if ea.get(k) != eb.get(k)]
    if ks:
        chg.append((eb["registry"], eb["company"], eb["quarter"], sorted(ks), eb.get("status")))
print("   provenance entries changed vs HEAD:", chg)
assert len(hp["entries"]) == len(prov["entries"]) and len(chg) == 2 and all(c[3] == ["refuted_by", "resolved_note", "status"] and c[4] == "CONTRADICTED" for c in chg)
assert {k: v for k, v in hp.items() if k != "entries"} == {k: v for k, v in prov.items() if k != "entries"}

# ---- D. xlsx (value-level, only the K-ICS sheet may differ from HEAD)
import openpyxl
hx = subprocess.run(["git", "show", "HEAD:insurequant_master_tables.xlsx"], cwd=REPO, capture_output=True).stdout
wa = openpyxl.load_workbook(io.BytesIO(hx), data_only=False, read_only=True)
wb = openpyxl.load_workbook(REPO / "insurequant_master_tables.xlsx", data_only=False, read_only=True)
print("D. xlsx sheets HEAD vs live:", wa.sheetnames == wb.sheetnames, len(wb.sheetnames))
changed_sheets = {}
for name in wb.sheetnames:
    ra = [list(r) for r in wa[name].iter_rows(values_only=True)]
    rb = [list(r) for r in wb[name].iter_rows(values_only=True)]
    if ra != rb:
        nd = sum(1 for x, y in zip(ra, rb) for a_, b_ in zip(x, y) if a_ != b_) + abs(len(ra) - len(rb))
        changed_sheets[name] = (len(ra), len(rb), nd)
print("   sheets whose values differ from HEAD:", changed_sheets)
assert set(changed_sheets) == {"K-ICS공시"} and changed_sheets["K-ICS공시"][0] == changed_sheets["K-ICS공시"][1]
print("ALL STATE CHECKS PASSED")
