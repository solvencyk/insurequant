import json, sys, collections
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/verify")
import vstmt
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
V = ROOT + "/data/_derived/remaining_20261022/e19_latest_comparative/verify/"
cur = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
C = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in cur}
COS = ["KR0082", "KR0032", "KR0104", "KR0087", "KR0070", "KR0083", "KR0005"]
QS = ["%d.%dQ" % (y, q) for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)]
ITEMS = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
data = {}
for co in COS:
    for q in QS:
        try:
            st = vstmt.read_separate_stmt(co, q)
        except Exception as e:
            data[(co, q)] = None
            continue
        try:
            c_, _, nc = vstmt.item_values(st, "cur")
            p_, _, _ = vstmt.item_values(st, "prior")
            c3 = vstmt.item_values(st, "cur3")[0] if nc == 4 else None
            p3 = vstmt.item_values(st, "prior3")[0] if nc == 4 else None
        except Exception as e:
            data[(co, q)] = None
            continue
        data[(co, q)] = {"cur": c_, "prior": p_, "cur3": c3, "prior3": p3, "unit": st["unit"], "ncol": nc}
def later(q):
    y, r = q.split("."); return "%d.%s" % (int(y) + 1, r)
def prevq(q):
    y, r = q.split("."); r = int(r[0])
    return None if r == 1 else "%s.%dQ" % (y, r - 1)
out = []
bad = []
state = {}
for co in COS:
    for q in QS[:8]:
        L = later(q)
        d0 = data.get((co, q)); d1 = data.get((co, L))
        if not d0 or not d1:
            out.append("%s %s: missing filing data (orig=%s later=%s)" % (co, q, bool(d0), bool(d1)))
            continue
        tol = 0.5001 if (d0["unit"] == "백만원" or d1["unit"] == "백만원") else 0.0105
        for it in ITEMS:
            m = C.get((co, it, q))
            if not m or m["값"] is None:
                continue
            o = d0["cur"].get(it); n = d1["prior"].get(it)
            if o is None or n is None:
                state[(co, q, it)] = "?"
                continue
            eo = abs(m["값"] - o) <= tol; en = abs(m["값"] - n) <= tol
            neutral = abs(o - n) <= tol
            s = "neutral" if neutral and eo else ("orig" if eo and not en else ("new" if en and not eo else "neither"))
            state[(co, q, it)] = s
# summary of states per (co,q)
for co in COS:
    for q in QS[:8]:
        c = collections.Counter(state.get((co, q, it)) for it in ITEMS)
        out.append("STATE %s %s %s" % (co, q, dict(c)))
# seams
seam_rows = []
for co in COS:
    for q in QS[:8]:
        pq = prevq(q)
        if not pq: continue
        for it in ITEMS:
            s1 = state.get((co, q, it)); s0 = state.get((co, pq, it))
            if {s1, s0} == {"orig", "new"} or "neither" in (s1, s0):
                m = C.get((co, it, q)); 
                if not m: continue
                dg = m.get("값_당분기")
                cumdiff = None
                mp = C.get((co, it, pq))
                if mp and mp["값"] is not None and m["값"] is not None: cumdiff = m["값"] - mp["값"]
                seam_rows.append((co, q, it, s0, s1, dg, cumdiff))
out.append("SEAM cells (prev state / this state): %d" % len(seam_rows))
for r in seam_rows:
    co, q, it, s0, s1, dg, cd = r
    tag = "null" if dg is None else ("= cumdiff(MIXED)" if (cd is not None and abs(dg - cd) < 1e-6) else "other(set?)")
    out.append("   SEAM %s %s item %s prev=%s this=%s dangi=%s cumdiff=%s -> %s" % (co, q, it, s0, s1, dg, cd, tag))
json.dump({"%s|%s|%s" % k: v for k, v in state.items()}, open(V + "v7_state.json", "w"))
open(V + "v7_seam.txt", "w", encoding="utf-8").write("\n".join(out))
