import json, os, subprocess
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
new = json.load(open(REPO + "/data/_derived/pl_oci_vs_bs_aoci_warn.json", encoding="utf-8"))
old = json.loads(subprocess.check_output(["git", "-C", REPO, "show", "HEAD:data/_derived/pl_oci_vs_bs_aoci_warn.json"]).decode("utf-8"))
out = open(here + "/l1_oci.txt", "w", encoding="utf-8")
out.write(f"worktree file rows {len(new)}; HEAD rows {len(old)}\n")
key = lambda r: json.dumps(r, sort_keys=True, ensure_ascii=False)
so = set(key(r) for r in old); sn = set(key(r) for r in new)
for r in new:
    if key(r) not in so: out.write("   NEW: " + key(r)[:320] + "\n")
for r in old:
    if key(r) not in sn: out.write("   GONE: " + key(r)[:320] + "\n")
