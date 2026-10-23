# -*- coding: utf-8 -*-
import io
p = "make_x02.py"
s = io.open(p, encoding="utf-8").read()
add = '''
rep("""bad = []
for k, (a, b) in chg_dangi.items():
    c, i, q = k
    cur = rowsN[k]["값"]
    pq = prev_q(q)
    exp = cur if pq is None else (None if (cur is None or rowsN.get((c, i, pq), {}).get("값") is None) else round(cur - rowsN[(c, i, pq)]["값"], 6))
""", """bad = []
SEAM_SET = {(x[0], x[2], x[1]): float(x[3]) for x in C["set_dangi_add"]}
SEAM_NULL = {(x[0], x[2], x[1]) for x in C["null_dangi_add"]}
for k, (a, b) in chg_dangi.items():
    c, i, q = k
    cur = rowsN[k]["값"]
    pq = prev_q(q)
    exp = cur if pq is None else (None if (cur is None or rowsN.get((c, i, pq), {}).get("값") is None) else round(cur - rowsN[(c, i, pq)]["값"], 6))
    if k in SEAM_SET:
        exp = SEAM_SET[k]
    elif k in SEAM_NULL:
        exp = None
""")
rep("""chk(not bad, f"PL_breakdown.json: every changed 값_당분기 equals cumulative - previous cumulative of the NEW master ({bad[:3]})")""",
    """chk(not bad, f"PL_breakdown.json: every changed 값_당분기 equals cumulative - previous cumulative of the NEW master, except the planned seam cells (set_dangi {len(SEAM_SET)} = printed 3M, null_dangi {len(SEAM_NULL)} = blank) ({bad[:3]})")
for k, v in SEAM_SET.items():
    chk(rowsN[k]["값_당분기"] is not None and abs(rowsN[k]["값_당분기"] - v) < 1e-6, f"seam set_dangi {k}: master 값_당분기 {rowsN[k]['값_당분기']} == planned {v}")
for k in SEAM_NULL:
    chk(rowsN[k]["값_당분기"] is None, f"seam null_dangi {k}: master 값_당분기 is blank")""")
'''
marker = 'DST.write_text(s, encoding="utf-8", newline="\n")'
assert s.count(marker) == 1
s = s.replace(marker, add + marker)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched make_x02")
