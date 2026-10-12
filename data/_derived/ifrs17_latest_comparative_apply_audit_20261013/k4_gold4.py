import json, csv, os, subprocess
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
def git(rev, path): return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:{path}"]).decode("utf-8"))
out = open(here + "/k4_gold4.txt", "w", encoding="utf-8")
old_pl = git("b8c37fff^", "data/_gold/user_pl_cells.json"); new_pl = git("b8c37fff", "data/_gold/user_pl_cells.json")
old_cs = git("b8c37fff^", "data/_gold/user_csm_cells.json"); new_cs = git("b8c37fff", "data/_gold/user_csm_cells.json")
out.write("pl set sample key/val: " + str(list(old_pl["set"].items())[:2])[:300] + "\n")
out.write("csm set sample: " + str(list(old_cs["set"].items())[:2])[:300] + "\n")
applied = list(csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")))
def look(setd, code, q, item):
    # find any structure: key could be 'code|quarter|item' or nested
    for k in (f"{code}|{q}|{item}", f"{code}/{q}/{item}", f"{code}|{q}|{item}|값"):
        if k in setd: return setd[k]
    if code in setd and isinstance(setd[code], dict):
        v = setd[code].get(q)
        if isinstance(v, dict): return v.get(str(item))
    return None
ov = 0; miss = 0
for a in applied:
    if a["master"] == "PL_breakdown":
        o = look(old_pl["set"], a["code"], a["quarter"], a["item"]); n = look(new_pl["set"], a["code"], a["quarter"], a["item"])
    elif a["master"] == "CSM_waterfall":
        o = look(old_cs["set"], a["code"], a["quarter"], a["item"]); n = look(new_cs["set"], a["code"], a["quarter"], a["item"])
    else: continue
    if o is not None: ov += 1; out.write(f"PRE-EXISTING GOLD for applied cell {a['master']} {a['code']} {a['quarter']} i{a['item']}: old gold {o} new gold {n}\n")
    if n is None: miss += 1; out.write(f"applied cell has no new gold line: {a['master']} {a['code']} {a['quarter']} i{a['item']}\n")
out.write(f"applied cells that already had an owner gold entry: {ov}; applied cells without a new gold line: {miss}\n")
