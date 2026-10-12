import json, os, subprocess
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
def git(rev, path): return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"{rev}:{path}"]).decode("utf-8"))
out = open(here + "/k7_flow.txt", "w", encoding="utf-8")
for f in ("PL_breakdown.json", "CSM_waterfall.json"):
    a = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in git("b8c37fff^", f)}
    b = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in git("HEAD", f)}
    chg = [k for k in b if k in a and a[k].get("값_당분기") != b[k].get("값_당분기")]
    bad = 0
    for (c, q, it) in chg:
        y, n = int(q[:4]), int(q[5])
        v = b[(c, q, it)].get("값")
        try: v = float(v)
        except Exception: v = None
        if it == 1 and f.startswith("CSM"): exp = v   # opening balance: not a flow
        else:
            pv = 0.0
            if n > 1:
                p = b.get((c, f"{y}.{n-1}Q", it))
                try: pv = float(p["값"])
                except Exception: pv = None
            exp = (v - pv) if (v is not None and pv is not None) else None
        got = b[(c, q, it)].get("값_당분기")
        try: got = float(got)
        except Exception: got = None
        ok = (exp is None and got is None) or (exp is not None and got is not None and abs(exp - got) < 0.0015)
        if not ok:
            bad += 1; out.write(f"   {f} {c} {q} i{it}: 값_당분기 {b[(c,q,it)].get('값_당분기')} vs 값-prev {exp}\n")
    out.write(f"{f}: derived-flow rows changed {len(chg)}; not equal to (값 - prior-quarter 값): {bad}\n")
