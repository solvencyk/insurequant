import json, csv, subprocess
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
def load(rev):
    return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:kics_disclosure.json"]).decode("utf-8"))
old = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in load("74a415bf^")}
new = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in load("74a415bf")}
rows = list(csv.DictReader(open(REPO + "/data/_derived/kics_latest_prior_apply_20261012/applied_blocks.csv", encoding="utf-8-sig")))
blocks = []
for r in rows:
    b = (r["code"], r["quarter"])
    if b not in blocks: blocks.append(b)
def f(x):
    try: return float(x)
    except: return None
out = open("a6_post_state.txt", "w", encoding="utf-8")
for code, q in blocks:
    out.write(f"===== {code} {q}\n")
    items = sorted(i for (c, qq, i) in new if c == code and qq == q and i <= 28)
    n_equal_old = n_diff_old = 0
    for i in items:
        o, n = old[(code, q, i)], new[(code, q, i)]
        po, pn = o.get("값_적용후"), n.get("값_적용후")
        out.write(f"  item{i:>2}: pre {o.get('값')}->{n.get('값')} | post {po}->{pn}" + ("  <-- pre changed" if f(o.get('값')) != f(n.get('값')) else "") + ("  <-- post changed" if f(po) != f(pn) else "") + "\n")
        if po not in (None, "") : 
            if f(po) == f(o.get("값")): n_equal_old += 1
            else: n_diff_old += 1
    out.write(f"  old master: post==pre items={n_equal_old}, post!=pre items={n_diff_old}\n")
