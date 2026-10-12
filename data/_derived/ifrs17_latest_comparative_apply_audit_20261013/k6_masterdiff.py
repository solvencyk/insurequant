import json, csv, os, subprocess
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
def git(rev, path): return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:{path}"]).decode("utf-8"))
out = open(here + "/k6_masterdiff.txt", "w", encoding="utf-8")
applied = list(csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")))
tot_bad = 0
for master, f in (("PL_breakdown", "PL_breakdown.json"), ("CSM_waterfall", "CSM_waterfall.json"), ("IFRS17_BS", "IFRS17_BS.json")):
    a = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in git("b8c37fff^", f)}
    b_rows = git("HEAD", f)
    b = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in b_rows}
    out.write(f"{master}: rows before {len(a)} after(HEAD) {len(b)}; added keys {len(set(b)-set(a))} removed keys {len(set(a)-set(b))}\n")
    fields = set()
    chg_val = {}; chg_other = collections = {}
    changed_val = set(); changed_other = {}
    for k in b:
        if k not in a: continue
        ra, rb = a[k], b[k]
        for fld in set(ra) | set(rb):
            if ra.get(fld) != rb.get(fld):
                if fld == "값": changed_val.add(k)
                else: changed_other.setdefault(fld, set()).add(k)
    ap = {(r["code"], r["quarter"], int(r["item"])) for r in applied if r["master"] == master}
    new_keys = set(b) - set(a)
    # applied cells whose old value was blank are new rows
    out.write(f"   cells with changed 값: {len(changed_val)}; applied {len(ap)}; changed but not applied: {sorted(changed_val - ap)[:10]}; applied but unchanged/new: {len(ap - changed_val)} (of which new rows {len((ap - changed_val) & new_keys)})\n")
    out.write(f"   other changed fields: { {k: len(v) for k, v in changed_other.items()} }\n")
    unexplained_other = {fld: [k for k in ks if k not in ap][:6] for fld, ks in changed_other.items()}
    out.write(f"   other-field changes outside applied cells (derived 값_당분기 expected): { {k: len(v) for k, v in unexplained_other.items()} }\n")
    # values equal to plan
    badv = 0
    for r in applied:
        if r["master"] != master: continue
        k = (r["code"], r["quarter"], int(r["item"]))
        v = b.get(k, {}).get("값")
        try: ok = abs(float(v) - float(r["new"])) < 1e-6
        except Exception: ok = False
        if not ok: badv += 1; out.write(f"   VALUE MISMATCH {k}: master {v} plan {r['new']}\n")
    out.write(f"   master value != planned new: {badv}\n")
    tot_bad += badv + len(changed_val - ap)
out.write(f"TOTAL problems {tot_bad}\n")
