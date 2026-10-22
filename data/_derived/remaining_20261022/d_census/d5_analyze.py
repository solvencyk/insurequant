# -*- coding: utf-8 -*-
"""d5 (v2): per-bucket facts (read-only).  Universe = the 51 buckets of the 2026-10-22 vintage measurement (scope A51)
+ every other (company, quarter) whose master still differs from the later filing's prior column on items 1/17/22/24/25/31
(scope ADDL: FY siblings 2023.1Q/2Q whose original has no FS-API, and OCI-only 2024.4Q-2025.2Q).  Kyobo (KR0073) excluded (done).
Output d5_buckets.json."""
import csv, json, sys
from pathlib import Path
from collections import defaultdict, Counter
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); D = ROOT / "data/_derived"; OUT = D / "remaining_20261022/d_census"
def rd(p): return list(csv.DictReader(open(p, encoding="utf-8-sig", newline="")))
res = json.loads((OUT / "d1_scan.json").read_text(encoding="utf-8"))
RES = {(r["code"], r["q"]): r for r in res}
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
PLM = defaultdict(dict); NAME = {}
for r in pl:
    PLM[(r["원보험사코드"], r["공시분기"])][str(r["항목번호"])] = (r.get("값"), r.get("값_당분기")); NAME[r["원보험사코드"]] = r["원수사명"]
cs = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
CSM = defaultdict(dict)
for r in cs: CSM[(r["원보험사코드"], r["공시분기"])][int(r["항목번호"])] = (r["값"], r["값_당분기"])
gpl = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
GOLD_PL = defaultdict(dict)
for c in gpl["set"]: GOLD_PL[(c["원보험사코드"], c["공시분기"])][str(c["항목번호"])] = c["값"]
gcs = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
GOLD_CSM = defaultdict(dict)
for c in gcs["set"]: GOLD_CSM[(c["원보험사코드"], c["공시분기"])][int(c["항목번호"])] = c["값"]
cvd = {(r["kr"], r["quarter"]): r for r in rd(D / "ifrs17_latest_comparative_precedence_dryrun_20261012/csm_block_verdicts.csv")}
pvd = {(r["kr"], r["quarter"]): r for r in rd(D / "ifrs17_latest_comparative_precedence_dryrun_20261012/pl_block_verdicts.csv")}
status = json.loads((OUT / "d7_status.json").read_text(encoding="utf-8"))
setA = set(map(tuple, json.loads((OUT / "d5_setA.json").read_text(encoding="utf-8"))))

TIER1 = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
ITEM_NM = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익", 19: "보험금융손익", 20: "영업이익", 21: "영업외손익", 22: "세전이익",
           23: "법인세", 24: "당기순이익", 25: "기타포괄손익", 26: "FVOCI채무", 27: "보험계약금융(OCI)", 28: "위험회피파생", 29: "FVOCI지분",
           30: "재보험금융(OCI)", 31: "총포괄손익", 32: "기타OCI"}
PL_PANELS = {1: "compare(보험손익)+IFRS17-P3", 17: "compare(투자손익)+IFRS17-P3", 24: "compare(순이익,ROE)+IFRS17-P3", 16: "IFRS17-P3", 21: "IFRS17-P3", 23: "IFRS17-P3",
             26: "IFRS17-P3 OCI", 27: "IFRS17-P3 OCI", 28: "IFRS17-P3 OCI", 29: "IFRS17-P3 OCI", 30: "IFRS17-P3 OCI", 31: "IFRS17-P3 OCI", 32: "IFRS17-P3 OCI"}
DL = "download-only"
def eok(x): return None if x is None else round(x / 100.0, 2)
def differs(a, b, floor=0.5, rel=1e-6): return a is not None and b is not None and abs(a - b) > max(rel * abs(a), floor)
def sign_flip(a, b): return a is not None and b is not None and a * b < 0 and abs(abs(a) - abs(b)) <= max(0.001 * abs(a), 1.0)

pl_universe = {k for k in (set(setA) | {tuple(k.split("|")) for k, v in status.items() if v[0] == "DIFF"}) if k[0] != "KR0073"}
# CSM-only buckets: 2026-10-12 scan says the CSM latest comparative differs from the current master, but the PL Tier-1 vintages agree.
# Same companies as the PL universe + the 17; extraction tier 'implausible' is not trusted and is left out.
csm_only = set()
_cos = {c for c, q in pl_universe}
for (kr, qq), r in cvd.items():
    if kr in _cos and r["scan_status"] == "DIFF" and r["tier"] != "implausible" and (kr, qq) not in pl_universe and kr != "KR0073":
        try:
            lat = json.loads(r["latest"]); now = [CSM.get((kr, qq), {}).get(i, (None,))[0] for i in range(1, 7)]
        except Exception:
            continue
        if now[0] is not None and not all(abs((a or 0) - (b or 0)) <= 0.051 for a, b in zip(now, lat)):
            csm_only.add((kr, qq))
universe = sorted(pl_universe | csm_only)
rows = []
for k in universe:
    code, q = k
    rec = RES.get(k) or {"items": {}, "div_same": None, "div_prior": None}; its = {int(i): v for i, v in rec["items"].items() if int(i) in TIER1}
    scope = "A51" if k in setA else ("ADDL_CSM_ONLY" if k in csm_only else ("ADDL_OCI_ONLY" if q >= "2024.4Q" else "ADDL_SIBLING"))
    cls = {}; relm = {}
    anchors = [i for i in (1, 17, 20, 22, 24) if i in its]
    def _base(v):
        return v["same"] if v["same"] is not None else v["master"]      # vintage evidence = original FS-API column; master only when the original has no API
    anchors_eq = all(not differs(_base(its[i]), its[i]["prior"], 1.0) for i in anchors if its[i]["prior"] is not None and _base(its[i]) is not None)
    for i, v in its.items():
        a = _base(v); b = v["prior"]; s = v["same"]; mm = v["master"]
        if a is None or b is None: cls[i] = "NA"
        elif not differs(a, b, 1.0): cls[i] = "EQ"
        elif s is not None and mm is not None and not differs(mm, b, 1.0): cls[i] = "LATEST_IN_MASTER"
        elif sign_flip(a, b): cls[i] = "SIGN"
        elif i in (18, 19) and anchors_eq: cls[i] = "SIGN_DERIVED"
        else: cls[i] = "REAL"
        m = v["master"]
        if m is None: relm[i] = "NONE"
        elif s is not None and abs(m - s) <= max(0.001 * abs(s), 1.0): relm[i] = "ORIGINAL"
        elif b is not None and abs(m - b) <= max(0.001 * abs(b), 1.0): relm[i] = "LATEST"
        elif s is not None and abs(m + s) <= max(0.001 * abs(s), 1.0): relm[i] = "ORIGINAL_NEGATED"
        else: relm[i] = "NEITHER" if s is not None else "ORIGINAL_NOAPI"
    real = sorted(i for i, c in cls.items() if c == "REAL")
    def ident(get):
        g = {i: get(i) for i in (1, 17, 20, 22, 23, 24, 25, 31)}
        out = {}
        out["I1"] = None if None in (g[1], g[17], g[20]) else abs(g[20] - (g[1] + g[17])) <= max(0.001 * abs(g[20]), 200)
        out["I2"] = None if None in (g[22], g[24], g[23]) else abs(abs(g[22] - g[24]) - abs(g[23])) <= max(0.001 * abs(g[24]), 200)
        out["I3"] = None if None in (g[24], g[25], g[31]) else abs(g[31] - (g[24] + g[25])) <= max(0.001 * abs(g[31]), 200)
        return out
    id_latest = ident(lambda i: its.get(i, {}).get("prior"))
    id_master = ident(lambda i: its.get(i, {}).get("master"))
    disp = []
    for i in real:
        v = its[i]; base = v["master"] if v["master"] is not None else v["same"]
        disp.append({"item": i, "name": ITEM_NM[i], "master_eok": eok(base), "latest_eok": eok(v["prior"]), "delta_eok": eok(v["prior"] - base),
                     "rel": (None if not base else round((v["prior"] - base) / abs(base), 4)), "panel": PL_PANELS.get(i, DL)})
    leaf = [26, 27, 28, 29, 30, 32]
    def dlt(i):
        v = its.get(i)
        if not v: return None
        a = v["master"] if v["master"] is not None else v["same"]
        return None if a is None or v["prior"] is None else v["prior"] - a
    dl = {i: dlt(i) for i in leaf if dlt(i) is not None and cls.get(i) != "SIGN"}
    d25 = dlt(25)
    tag_move = None if d25 is None or not dl else round((sum(abs(x) for x in dl.values()) - abs(d25)) / 100.0, 2)
    gb = GOLD_PL.get(k, {})
    gold_overlap = sorted(i for i in real if str(i) in gb)
    gold_in_block = sorted(gb, key=lambda x: int(x) if x.isdigit() else 99)
    gold_val = {}
    for gi in gold_in_block:
        if gi.isdigit() and int(gi) in its:
            v = its[int(gi)]; g = gb[gi]
            gold_val[gi] = ("=original" if v["same"] is not None and abs(g - v["same"]) <= max(0.001 * abs(v["same"]), 1) else
                            ("=latest" if v["prior"] is not None and abs(g - v["prior"]) <= max(0.001 * abs(v["prior"]), 1) else "other"))
    cv = cvd.get(k); cur_now = CSM.get(k, {}); now_vec = [cur_now.get(i, (None,))[0] for i in range(1, 7)]
    csm = {"status": None, "verdict_1012": None, "diff_items": [], "now": now_vec, "latest": None, "rel_now": None, "gold": sorted(GOLD_CSM.get(k, {})), "fid": None, "tier": None}
    if cv:
        csm.update(status=cv["scan_status"], verdict_1012=cv["verdict"], fid=cv["fidelity"], tier=cv["tier"])
        csm["diff_items"] = [int(x) for x in cv["diff_items"].split(",") if x.strip()]
        try:
            lat = json.loads(cv["latest"]) if cv["latest"] else None; cur = json.loads(cv["current"]) if cv["current"] else None
        except Exception:
            lat = cur = None
        csm["latest"] = lat; csm["current1012"] = cur
        if lat and now_vec[0] is not None:
            if all(abs((a or 0) - (b or 0)) <= 0.051 for a, b in zip(now_vec, lat)): csm["rel_now"] = "LATEST"
            elif cur and all(abs((a or 0) - (b or 0)) <= 0.051 for a, b in zip(now_vec, cur)): csm["rel_now"] = "ORIGINAL"
            else: csm["rel_now"] = "NEITHER"
    pl4 = PLM.get(k, {}).get("4", (None, None))[0]
    csm["pl4_eok"] = eok(pl4)
    fy = q[:4]
    sib = {}
    for sq in ("1Q", "2Q", "3Q", "4Q"):
        s = status.get(f"{code}|{fy}.{sq}")
        sib[f"{fy}.{sq}"] = None if s is None else s[0]
    rows.append({"code": code, "name": NAME[code], "q": q, "scope": scope, "div": [rec["div_same"], rec["div_prior"]], "its": {str(i): v for i, v in its.items()},
                 "cls": {str(i): c for i, c in cls.items()}, "real": real, "rel_master": {str(i): c for i, c in relm.items()},
                 "id_latest": id_latest, "id_master": id_master, "disp": disp, "tag_move_eok": tag_move, "d24_eok": eok(dlt(24)), "d25_eok": eok(dlt(25)), "d31_eok": eok(dlt(31)),
                 "gold_overlap": gold_overlap, "gold_in_block": gold_in_block, "gold_val": gold_val, "csm": csm, "fy_status": sib,
                 "pl_verdict_1012": (pvd.get(k) or {}).get("verdict")})
json.dump(rows, open(OUT / "d5_buckets.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("universe", len(rows), Counter(r["scope"] for r in rows))
