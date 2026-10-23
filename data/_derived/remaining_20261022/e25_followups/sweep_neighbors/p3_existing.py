# -*- coding: utf-8 -*-
"""Phase 3: reuse the existing (e21/e23) company readers on the touched quarters; compare each returned item with the working-tree master."""
import json, sys, collections, traceback
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
import e23_read as E
import e21_t2 as T
import e21_t2b as T2
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
csm = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/CSM_waterfall.json", encoding="utf-8"))}
t = json.load(open("s01_touched.json", encoding="utf-8"))
cq = sorted({tuple(k.split("|")) for v in t.values() for k in v})
out = []
def cmp(c, q, it, newv, src, line, how):
    m = pl.get((c, str(it), q))
    out.append(dict(sheet="PL", code=c, q=q, item=str(it), master=m, latest=round(newv, 6), diff=(None if m is None else round(newv - m, 6)), src=src, line=line, how=how))
for c, q in cq:
    try:
        if c == "KR0010":
            r = T.kb_read(c, q)
            for it, d in r.items():
                if isinstance(it, int): cmp(c, q, it, d["val"], d["src"], d["parts"][0]["line"], "kb_read")
        elif c == "KR0003":
            r = T.lotte_combined_read(c, q) if q in ("2023.1Q", "2023.2Q", "2024.1Q") else T2.lotte_split_read(c, q)
            for it, d in r.items():
                if isinstance(it, int): cmp(c, q, it, d["val"], d["src"], d["parts"][0]["line"], "lotte_read")
        elif c == "KR0001":
            r = T.meritz_read(c, q)
            for it, d in r.items():
                if isinstance(it, int): cmp(c, q, it, d["val"], d["src"], d["parts"][0]["line"], "meritz_read")
    except Exception as e:
        out.append(dict(sheet="PL", code=c, q=q, item="*", err=f"{type(e).__name__}: {str(e)[:160]}"))
    # CSM readers
    try:
        fn = {"KR0099": E.csm_kblife, "KR0070": E.csm_abl, "KR0072": E.csm_kdb, "KR0009": E.csm_hd}.get(c)
        if fn:
            v = fn(q)
            vec = v.get("vec_exact") or v.get("vec")
            out.append(dict(sheet="CSM", code=c, q=q, item="vec", raw={k: (v[k] if k in v else None) for k in ("vec", "vec_exact", "src")} ))
    except Exception as e:
        out.append(dict(sheet="CSM", code=c, q=q, item="*", err=f"{type(e).__name__}: {str(e)[:160]}"))
json.dump(out, open("p3_existing.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
d = [x for x in out if x.get("diff") not in (None, ) and abs(x["diff"]) >= 1.0]
print("PL reads", sum(1 for x in out if x["sheet"] == "PL" and "latest" in x), "differ>=1mn", len(d), "errors", sum(1 for x in out if "err" in x))
for x in d: print(x["code"], x["q"], x["item"], x["master"], x["latest"], x["diff"], x["how"], x["line"])
for x in out:
    if "err" in x: print("ERR", x["code"], x["q"], x["sheet"], x["err"])
