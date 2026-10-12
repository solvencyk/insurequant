import json, subprocess, os
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
def git(rev, path): return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:{path}"]).decode("utf-8"))
out = open(os.path.dirname(os.path.abspath(__file__)) + "/k4b.txt", "w", encoding="utf-8")
for f in ("data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json"):
    d = git("b8c37fff", f)
    out.write(f"{f}: set type {type(d['set']).__name__} len {len(d['set'])}; first: {json.dumps(d['set'][0], ensure_ascii=False)[:300]}; last: {json.dumps(d['set'][-1], ensure_ascii=False)[:300]}\n")
