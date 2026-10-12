import json, csv, os, subprocess
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
led_new = json.load(open(REPO + "/data/_gold/kics_restatement_ledger.json", encoding="utf-8"))
old_txt = subprocess.check_output(["git", "-C", REPO, "show", "74a415bf^:data/_gold/kics_restatement_ledger.json"]).decode("utf-8")
led_old = json.loads(old_txt)
def entries(d):
    return d.get("entries") or d.get("cells") or {k: v for k, v in d.items() if isinstance(v, dict) and "|" in k}
en, eo = entries(led_new), entries(led_old)
added = sorted(set(en) - set(eo))
changed = [k for k in eo if k in en and eo[k] != en[k]]
out = open(here + "/h1_ledger_check.txt", "w", encoding="utf-8")
out.write(f"ledger entries old={len(eo)} new={len(en)} added={len(added)} changed_existing={len(changed)} removed={len(set(eo)-set(en))}\n")
master = {}
for r in json.load(open(REPO + "/kics_disclosure.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
rows = list(csv.DictReader(open(here + "/e1_final_table.csv", encoding="utf-8-sig")))
prim = {(r["block"].split("_")[0], r["block"].split("_")[1], int(r["item"])): r for r in rows if r["kind"] == "primary"}
bad = 0
for k in added:
    e = en[k]
    code, q, it = k.split("|"); it = int(it)
    m = float(master[(code, q, it)]["값"])
    ok_master = abs(m - float(e["restated"])) < 1e-6
    p = prim.get((code, q, it))
    ok_tbl = p is not None and abs(float(p["new"]) - float(e["restated"])) < 1e-6
    ok_old = p is not None and (abs(float(p["old"]) - float(e["as_filed"])) < 1e-6)
    flag = "" if (ok_master and ok_tbl and ok_old) else "  <-- CHECK"
    if flag: bad += 1
    out.write(f"{k}: as_filed={e['as_filed']} restated={e['restated']} basis={e.get('adopted_basis')} master_now={m} table_new={p and p['new']} table_old={p and p['old']}{flag}\n")
out.write(f"\nprimary applied cells not in ledger-added: {sorted(set(prim)-set((k.split('|')[0],k.split('|')[1],int(k.split('|')[2])) for k in added))}\n")
out.write(f"bad={bad}\n")
