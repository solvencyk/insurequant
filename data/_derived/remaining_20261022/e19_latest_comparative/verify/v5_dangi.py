import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/verify")
import vstmt
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
V = ROOT + "/data/_derived/remaining_20261022/e19_latest_comparative/verify/"
gold = json.load(open(ROOT + "/data/_gold/user_pl_cells.json", encoding="utf-8"))
SP = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"
gh = json.load(open(SP + "/head_gold.json", encoding="utf-8"))
cur = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
C = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in cur}
def later(q):
    y, r = q.split("."); return "%d.%s" % (int(y) + 1, r)
out = []
hs = {json.dumps(x, ensure_ascii=False) for x in gh["set_dangi"]["cells"]}
new_set = [x for x in gold["set_dangi"]["cells"] if json.dumps(x, ensure_ascii=False) not in hs]
hn = {json.dumps(x, ensure_ascii=False) for x in gh["null_dangi"]["cells"]}
new_null = [x for x in gold["null_dangi"]["cells"] if json.dumps(x, ensure_ascii=False) not in hn]
out.append("new set_dangi %d, new null_dangi %d" % (len(new_set), len(new_null)))
bad = 0
for code, q, it, val, src in new_set:
    L = later(q)
    st = vstmt.read_separate_stmt(code, L)
    v3, _, nc = vstmt.item_values(st, "prior3")
    exp = v3.get(it)
    ok = exp is not None and abs(exp - val) <= 0.0105
    if not ok: bad += 1
    out.append("set_dangi %s %s item %s val=%s reader3m(%s)=%s ok=%s master_dangi=%s" % (code, q, it, val, L, None if exp is None else round(exp, 6), ok, C[(code, it, q)].get("값_당분기")))
out.append("set_dangi bad=%d" % bad)
out.append("null_dangi new by (code,q): %s" % sorted({(c, q) for c, q, i in new_null}))
for c, q, i in new_null:
    if C[(c, i, q)].get("값_당분기") is not None:
        out.append("null_dangi cell has non-null dangi in master: %s %s %s" % (c, q, i))
out.append("null_dangi all null in master: checked")
open(V + "v5_dangi.txt", "w", encoding="utf-8").write("\n".join(out))
