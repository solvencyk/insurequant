import sys, json, subprocess, re, time, collections
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl")
import vlib
ROOT = vlib.ROOT
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/"
def jload(p):
    for a in range(3):
        try: return json.load(open(p, encoding="utf-8"))
        except Exception: time.sleep(30)
    raise
W = {(r["공시분기"], r["항목번호"]): r for r in jload(ROOT + "/CSM_waterfall.json") if r["원보험사코드"] == "KR0070"}
hr = subprocess.run(["git", "-C", ROOT, "show", "HEAD:CSM_waterfall.json"], capture_output=True).stdout.decode("utf-8")
H = {(r["공시분기"], r["항목번호"]): r for r in json.loads(hr) if r["원보험사코드"] == "KR0070"}
L = []
def P(s): L.append(s)
ROWLAB = {1: "기초 보험계약마진", 2: "신계약 인식효과", 3: "보험금융손익", 4: "보험계약마진을 조정하는 추정치 변동", 5: "제공된 서비스 관련 당기손익 인식", 6: "분기말 보험계약마진"}
def ctables(fy):
    lines = vlib.load(fy); out = []
    for t in vlib.tables(fy):
        labs = [r["cells"][0][1].strip() for r in t["rows"] if r["cells"]]
        if "기초 보험계약마진" in labs and any("수정소급법" in c[1] for r in t["rows"][:2] for c in r["cells"]):
            prev = []
            for j in range(t["start"] - 1, max(0, t["start"] - 60), -1):
                s = re.sub(r"<[^>]*>", "", lines[j - 1]).strip()
                if s: prev.append(s)
                if len(prev) >= 3: break
            out.append((t, prev))
    return out
def rowvals(t):
    d = {}
    for r in t["rows"]:
        if r["cells"]:
            lab = r["cells"][0][1].strip()
            if lab not in d: d[lab] = [vlib.num(c[1]) for c in r["cells"][1:]] ; d[lab + "#line"] = r["line"]
    return d
SEL = {}
for fy in ("FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"):
    ct = ctables(fy)
    P("%s: %d CSM tables" % (fy, len(ct)))
    for t, prev in ct:
        d = rowvals(t)
        P("   T%d-%d hdr=%s prev=%s | 기초 합계=%s 기말 합계=%s" % (t["start"], t["end"], [c[1][:14] for c in t["rows"][0]["cells"]], prev[:2], d["기초 보험계약마진"][-1], d.get("분기말 보험계약마진", d.get("기말 보험계약마진", [None]))[-1]))
    SEL[fy] = ct
open(OUT + "v11_csm_tables.txt", "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))

# ---- value verification
from decimal import Decimal, ROUND_HALF_UP
def r1(x):  # 백만원 -> 억원, 1 decimal, half-up
    return float((Decimal(str(x)) / Decimal(100)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
PRIOR = {"2023.1Q": ("FY2024_Q1", 1), "2023.2Q": ("FY2024_Q2", 1), "2023.3Q": ("FY2024_Q3", 1), "2023.4Q": ("FY2024_Q4", 1)}  # index of prior table in ctables list
L2 = []
res = []
for q, (fy, idx) in PRIOR.items():
    t, prev = SEL[fy][idx]
    d = rowvals(t)
    endlab = [k for k in d if k.endswith("말 보험계약마진") and not k.endswith("#line")][0]
    raw = {1: d["기초 보험계약마진"][-1], 2: d["신계약 인식효과"][-1], 3: d["보험금융손익"][-1],
           4: d["보험계약마진을 조정하는 추정치 변동"][-1], 5: d["제공된 서비스 관련 당기손익 인식"][-1], 6: d[endlab][-1]}
    lines = {1: d["기초 보험계약마진#line"], 2: d["신계약 인식효과#line"], 3: d["보험금융손익#line"], 4: d["보험계약마진을 조정하는 추정치 변동#line"], 5: d["제공된 서비스 관련 당기손익 인식#line"], 6: d[endlab + "#line"]}
    # identity in raw: sum
    ident = raw[1] + raw[2] + raw[3] + raw[4] + raw[5] - raw[6]
    L2.append("%s table T%d-%d (%s) raw identity open+nb+int+adj+amort-close = %s (백만원)" % (q, t["start"], t["end"], prev[-1][:20] if prev else "", ident))
    for it in range(1, 7):
        e = r1(raw[it]); w = W[(q, it)]["값"]; h = H[(q, it)]["값"]
        tie = abs(abs(raw[it]) % 10 - 5) < 1e-9
        ok = abs(w - e) < 1e-9
        res.append((q, it, raw[it], e, w, h, ok, lines[it]))
        L2.append("   item %d raw %10.0f 백만원 line %d -> expected %9.1f | master %9.1f | HEAD %9.1f | %s%s" % (it, raw[it], lines[it], e, w, h, "OK" if ok else "MISMATCH", " (moved)" if abs(w - h) > 1e-9 else " (unchanged)"))
nm = [r for r in res if not r[6]]
L2.append("CSM cells checked %d, mismatch %d" % (len(res), len(nm)))
L2.append("moved vs HEAD among them: %d ; moved & ok %d" % (len([r for r in res if abs(r[4] - r[5]) > 1e-9]), len([r for r in res if abs(r[4] - r[5]) > 1e-9 and r[6]])))
# calibration on current columns of same filings -> master 2024.xQ
L2.append("")
L2.append("== calibration: current tables vs master 2024.xQ")
CUR = {"2024.1Q": ("FY2024_Q1", 0), "2024.2Q": ("FY2024_Q2", 0), "2024.3Q": ("FY2024_Q3", 0), "2024.4Q": ("FY2024_Q4", 0)}
ok = bad = 0
for q, (fy, idx) in CUR.items():
    t, prev = SEL[fy][idx]; d = rowvals(t)
    endlab = [k for k in d if k.endswith("말 보험계약마진") and not k.endswith("#line")][0]
    raw = {1: d["기초 보험계약마진"][-1], 2: d["신계약 인식효과"][-1], 3: d["보험금융손익"][-1], 4: d["보험계약마진을 조정하는 추정치 변동"][-1], 5: d["제공된 서비스 관련 당기손익 인식"][-1], 6: d[endlab][-1]}
    for it in range(1, 7):
        e = r1(raw[it]); w = W[(q, it)]["값"]
        if abs(w - e) < 1e-9: ok += 1
        else: bad += 1; L2.append("   CAL DIFF %s item %d raw->%.1f master %.1f" % (q, it, e, w))
L2.append("calibration ok %d diff %d" % (ok, bad))
# 값_당분기 recompute for all KR0070 CSM cells
L2.append("")
L2.append("== CSM 값_당분기 recompute (Q1: =값; else flows diff, item1=prev close, item6=close)")
def prevq(q):
    y, k = q.split("."); n = int(k[0]); return None if n == 1 else "%s.%dQ" % (y, n - 1)
mm = 0; cnt = 0
for (q, it), r in sorted(W.items()):
    v = r["값"]; dg = r.get("값_당분기"); p = prevq(q)
    if p is None: exp = v
    elif it == 1: exp = W.get((p, 6), {}).get("값")
    elif it == 6: exp = v
    else:
        pv = W.get((p, it), {}).get("값"); exp = None if (v is None or pv is None) else round(v - pv, 10)
    cnt += 1
    if not ((exp is None and dg is None) or (exp is not None and dg is not None and abs(exp - dg) < 0.051)):
        mm += 1; L2.append("   DANGI MISMATCH %s item %d 값=%s 당분기=%s expected=%s" % (q, it, v, dg, exp))
L2.append("checked %d, mismatches %d (tolerance 0.05 for 0.1-rounding)" % (cnt, mm))
chg = [(k, H[k].get("값_당분기"), W[k].get("값_당분기")) for k in W if k in H and H[k].get("값_당분기") != W[k].get("값_당분기")]
L2.append("changed 값_당분기 vs HEAD: %d by quarter %s" % (len(chg), dict(collections.Counter(k[0] for k, a, b in chg))))
# opening chain
L2.append("")
L2.append("== opening/closing chain")
for nm_, D in (("HEAD", H), ("WORK", W)):
    L2.append(nm_)
    for fyr in ("2023", "2024", "2025"):
        o = [(q, D.get((q, 1), {}).get("값"), D.get((q, 6), {}).get("값")) for q in ("%s.1Q" % fyr, "%s.2Q" % fyr, "%s.3Q" % fyr, "%s.4Q" % fyr)]
        L2.append("   FY%s opening/closing: %s | opening spread within FY: %s" % (fyr, o, None if any(x[1] is None for x in o) else round(max(x[1] for x in o) - min(x[1] for x in o), 3)))
    for a, b in (("2023.4Q", "2024.1Q"), ("2024.4Q", "2025.1Q")):
        ca = D.get((a, 6), {}).get("값"); ob = D.get((b, 1), {}).get("값")
        L2.append("   boundary %s close %s -> %s open %s drift %s" % (a, ca, b, ob, None if ca is None or ob is None else round(ob - ca, 3)))
# identity per quarter of master (open+nb+int+adj+amort = close within 0.15)
L2.append("")
L2.append("== master identity per quarter (1+2+3+4+5-6)")
for q in sorted({k[0] for k in W}):
    try:
        s = sum(W[(q, i)]["값"] for i in range(1, 6)) - W[(q, 6)]["값"]
        L2.append("   %s %.2f" % (q, s))
    except Exception as e: L2.append("   %s n/a" % q)
open(OUT + "v11_csm_verify.txt", "w", encoding="utf-8").write("\n".join(L + [""] + L2))
print("\n".join(L2))
