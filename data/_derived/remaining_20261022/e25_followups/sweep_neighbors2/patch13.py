s = open("p20_compile.py", encoding="utf-8").read()
old = """                lines_ = ",".join(str(x["line"]) for x in v["cites"])
                conf = "high" if v["ncand"] == 1 else "medium"
                note = f"{v['how']}; cal cur={round(v['cur_val'],1)} vs master(q+4)={v['master_cur']}; label={v['cites'][0]['label']}; unit={v['cites'][0]['unit']}"
                val = v["val"]"""
new = """                lines_ = ",".join(str(x["line"]) for x in v["cites"])
                conf = "high" if v["ncand"] == 1 else "medium"
                note = f"{v['how']}; cal cur={round(v['cur_val'],1)} vs master(q+4)={v['master_cur']}; label={v['cites'][0]['label']}; unit={v['cites'][0]['unit']}"
                val = v["val"]
                if v["master_cur"] is not None and v["cur_val"] * v["master_cur"] < 0:
                    val = -val
                    note += "; company sign convention: master stores the opposite sign (verified on the current column), prior flipped to the master convention\""""
assert old in s
s = s.replace(old, new.replace('\\"', ''))
# 3M-not-cumulative detector after class assignment loop (before WRONG_LEG)
old2 = "# ---------- WRONG_LEG detection"
new2 = '''# ---------- master holds a single-quarter (3-month) figure instead of the cumulative one
def prevq(q):
    return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"
for r in rows:
    if r["cls"] in ("VINTAGE_NOTE", "VINTAGE_STATEMENT") and r["master"] is not None and r["item"].isdigit():
        pq = prevq(r["quarter"])
        if pq:
            pm = pl.get((r["company"], pq, r["item"]))
            if pm is not None and abs((r["latest"] - pm) - r["master"]) <= 1.5 and abs(pm) > 5:
                r["cls"] = "OTHER_MASTER_HOLDS_3M"
                r["note"] += f"; master = latest cumulative - master of {pq} ({pm}) = single-quarter figure, not cumulative"
# ---------- WRONG_LEG detection'''
s = s.replace(old2, new2, 1)
open("p20_compile.py", "w", encoding="utf-8").write(s)
