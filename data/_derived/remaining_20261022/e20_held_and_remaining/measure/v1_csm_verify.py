"""v1_csm_verify: independent check of the (dry-run) CSM latest vectors of the READY buckets.
For each (code, quarter): load the vector (csmvec), read the LATER filing with my own line-oriented reader, and list the tables whose printed cells (converted to 억원) match the vector items
(|abs(cell) - abs(item)| <= 0.06).  A single table matching opening + closing + >= 4 items = the vector is printed as a total there (line numbers given);
otherwise the vector is a sum over product/LOB tables (reported separately).  READ-ONLY.
usage: v1_csm_verify.py CODE:Q,CODE:Q,...   -> v1_csm_verify.txt/json"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import csmvec as CV  # noqa: E402
import mlib as M  # noqa: E402
import plan_lib as PL  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
TOL = 0.06
out, txt = {}, []
for sp in sys.argv[1].split(","):
    code, q = sp.split(":")
    vec = CV.prior(code, q)
    fy = M.later_fy(q)
    if vec is None:
        txt.append(f"{code} {q}: no DIFF vector ({CV.status(code, q)})")
        continue
    files = M.main_xmls(code, fy)
    best = []
    for path in files:
        if path.name.endswith(("_00761.xml",)):
            continue
        lines = M.read_lines(path)
        for t in M.iter_tables(lines):
            bestk = None
            for ulabel, k in (("백만원", 1.0 / 100.0), ("천원", 1.0 / 1e5), ("원", 1.0 / 1e8)):
                hits = {}
                for r in t["rows"]:
                    lab = r["cells"][0]["text"][:30] if r["cells"] else ""
                    for c in r["cells"][1:]:
                        if c["val"] is None:
                            continue
                        e = abs(c["val"]) * k
                        for i, v in enumerate(vec):
                            if v is not None and abs(abs(v) - e) <= TOL and (i + 1) not in hits:
                                hits[i + 1] = (lab, c["line"], c["text"])
                if bestk is None or len(hits) > len(bestk[1]):
                    bestk = (ulabel, hits)
            ulabel, hits = bestk
            if len(hits) >= 3:
                best.append((len(hits), 1 in hits and 6 in hits, path.name, t["start"], ((t["caption"] or "")[:50] + " [unit " + ulabel + "]"), hits))
    best.sort(key=lambda x: (-x[0], not x[1]))
    res = [{"n_items": b[0], "open_close": b[1], "file": b[2], "table_start": b[3], "caption": b[4], "hits": {str(k): v for k, v in b[5].items()}} for b in best[:6]]
    out[f"{code}|{q}"] = {"vec": vec, "later": fy, "tables": res}
    txt.append(f"{code} {q} later {fy} vec={vec}")
    if not res:
        txt.append("   no single table matches >=3 items (vector is a sum over product/LOB tables or not printed)")
    for b in res[:4]:
        txt.append(f"   {b['file']} table@L{b['table_start']} items={b['n_items']} open+close={b['open_close']} caption='{b['caption']}'")
        for k, (lab, ln, tx) in sorted(b["hits"].items(), key=lambda kv: int(kv[0])):
            txt.append(f"        item{k}: {lab} L{ln} {tx}")
M.MEASURE.joinpath("v1_csm_verify.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("v1_csm_verify.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt)[:12000])
