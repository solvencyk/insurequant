import sys, json
sys.path.insert(0, ".")
import vmaster
PH, PW = vmaster.load_all("PL_breakdown"); CH, CW = vmaster.load_all("CSM_waterfall")
out = []
def P(s=""):
    print(s); out.append(s)
f = lambda v: "None" if v is None else "%.2f" % (v / 100.0)
P("Headline (억원, cumulative 값; HEAD -> WORK; delta)")
for name, M, items in (("보험손익", PW, 1), ("투자손익", PW, 17), ("당기순이익", PW, 24), ("기타포괄손익", PW, 25), ("총포괄손익", PW, 31)):
    for q in ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]:
        h = PH[(q, items)]["값"]; w = PW[(q, items)]["값"]
        dg_h = PH[(q, items)]["값_당분기"]; dg_w = PW[(q, items)]["값_당분기"]
        P("%-8s %s cum %s -> %s (%s) | dangi %s -> %s" % (name, q, f(h), f(w), "NA" if h is None else "%.2f" % ((w - h) / 100.0), f(dg_h), f(dg_w)))
for q in ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]:
    P("CSM 기말 %s %s -> %s ; 기초 %s -> %s" % (q, CH[(q, 6)]["값"], CW[(q, 6)]["값"], CH[(q, 1)]["값"], CW[(q, 1)]["값"]))
P("\nCSM identity per quarter WORK: open+new+int+adj+amort-close")
for q in ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]:
    v = {i: CW[(q, i)]["값"] for i in range(1, 7)}
    P("  %s %.3f" % (q, v[1] + v[2] + v[3] + v[4] + v[5] - v[6]))
P("\nboundary 2023.4Q close vs 2024.1Q open: HEAD %s vs %s ; WORK %s vs %s" % (CH[("2023.4Q", 6)]["값"], CH[("2024.1Q", 1)]["값"], CW[("2023.4Q", 6)]["값"], CW[("2024.1Q", 1)]["값"]))
P("opening drift within FY2023 (WORK): %s" % [CW[(q, 1)]["값"] for q in ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]])
P("opening within FY2024 (WORK): %s" % [CW[(q, 1)]["값"] for q in ["2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"]])
P("\nPL 4Q identity 3 = 4+5+6+7 (WORK): items %s" % {i: PW[("2023.4Q", i)]["값"] for i in (3, 4, 5, 6, 7)})
v = PW[("2023.4Q", 3)]["값"] - sum(PW[("2023.4Q", i)]["값"] for i in (4, 5, 6, 7))
vh = PH[("2023.4Q", 3)]["값"] - sum(PH[("2023.4Q", i)]["값"] for i in (4, 5, 6, 7))
P("  residual HEAD %.3f WORK %.3f" % (vh, v))
# gold vs master consistency
for n, M in (("user_pl_cells", PW), ("user_csm_cells", CW)):
    g = vmaster.work("data/_gold/%s.json" % n)
    bad = 0; k = 0
    for e in g["set"]:
        if e["원보험사코드"] != "KR0009": continue
        k += 1
        m = M.get((e["공시분기"], e["항목번호"]))
        if m is None or m["값"] is None or abs(m["값"] - e["값"]) > 1e-9:
            bad += 1; P("  gold!=master %s %s %s gold %s master %s" % (n, e["공시분기"], e["항목번호"], e["값"], m and m["값"]))
    P("%s KR0009 gold entries %d, gold-vs-master mismatches %d" % (n, k, bad))
# null_dangi section KR0009
h = vmaster.head("data/_gold/user_pl_cells.json"); w = vmaster.work("data/_gold/user_pl_cells.json")
for sec in ("null_dangi", "set_dangi"):
    hs = h[sec]; ws = w[sec]
    P("%s: type %s head keys %s" % (sec, type(hs).__name__, list(hs)[:12] if isinstance(hs, dict) else len(hs)))
    P("  work keys %s" % (list(ws)[:12] if isinstance(ws, dict) else len(ws)))
    for kk in ws:
        if kk != "_doc" and "KR0009" in str(kk):
            P("  work[%s] = %s" % (kk, json.dumps(ws[kk], ensure_ascii=False)[:600]))
            P("  head[%s] = %s" % (kk, json.dumps(hs.get(kk), ensure_ascii=False)[:600]))
# provenance meta diff
for nm in ("PL_breakdown_provenance", "CSM_waterfall_provenance"):
    a = vmaster.head(nm + ".json"); b = vmaster.work(nm + ".json")
    ta = {k: v for k, v in a.items() if k != "cells"}; tb = {k: v for k, v in b.items() if k != "cells"}
    P("%s top-level meta diff keys: %s" % (nm, [k for k in set(ta) | set(tb) if ta.get(k) != tb.get(k)]))
open("v11_headline.txt", "w", encoding="utf-8").write("\n".join(out))
