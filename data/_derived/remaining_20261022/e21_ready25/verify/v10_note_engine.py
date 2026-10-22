# -*- coding: utf-8 -*-
"""v10: independent LOB-note recomputation for 손보 buckets (KB손보 / 메리츠 / 롯데) from raw XML (prior-period separate tables).
Own table reader; formulas written from the accounting definitions used in the master (item list in PL_breakdown), not imported."""
import json, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
import xmlrd

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
HERE = ROOT + "data/_derived/remaining_20261022/e21_ready25/verify/"
master = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in json.load(open(ROOT + "PL_breakdown.json", encoding="utf-8"))}
head = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in json.load(open(HERE + "head/PL_breakdown.json", encoding="utf-8"))}

SEC = {"보험수익": "rev", "보험서비스비용": "cost", "보험비용": "cost", "재보험수익": "re_rev", "재보험비용": "re_cost"}


def nz(s):
    v = xmlrd.parse_num(s)
    if v is None:
        return 0.0 if s.strip() in ("-", "") else None
    return v


def read_table(doc, t):
    """-> (sections dict sec -> list of (label, values list), lob cum index list, flat rows)"""
    hdr = None
    for r in t["rows"]:
        txts = [c["t"].replace(" ", "") for c in r["cells"]]
        if "누적" in txts and "3개월" in txts:
            hdr = r
            break
    secs = collections.OrderedDict()
    cur = None
    flat = []
    for r in t["rows"]:
        cs = [c["t"] for c in r["cells"]]
        if not cs:
            continue
        lab = cs[0].replace(" ", "")
        vals = cs[1:]
        if lab in SEC and not any(v.strip() for v in vals):
            cur = SEC[lab]
            secs.setdefault(cur, [])
            continue
        if cur is None:
            continue
        # numeric value row
        nums = [nz(v) for v in vals]
        if vals and all(n is not None for n in nums) and len(vals) >= 3:
            secs[cur].append((cs[0], nums))
            flat.append((cur, cs[0], nums))
    ncols = max((len(v) for s in secs.values() for _, v in s), default=0)
    if hdr:
        T = sum(c["span"] for c in hdr["cells"])
        off = ncols - T
        cum_idx = []
        c0 = 0
        for c in hdr["cells"]:
            if c["t"].replace(" ", "") == "누적":
                cum_idx += [c0 + off + j for j in range(c["span"])]
            c0 += c["span"]
    else:
        cum_idx = list(range(ncols))
    return secs, cum_idx, ncols


def pick(vals, cum_idx, k):
    return vals[cum_idx[k]]


def find(secs, sec, *needles, exclude=()):
    for lab, vals in secs.get(sec, []):
        l = lab.replace(" ", "")
        if any(n.replace(" ", "") in l for n in needles) and not any(e in l for e in exclude):
            return lab, vals
    return None, None


def compute(doc, t, style):
    secs, cum_idx, ncols = read_table(doc, t)
    res = {"ncols": ncols, "ncum": len(cum_idx)}
    nl = len(cum_idx)

    def v(sec, needles, k=0, exclude=(), nth=1):
        hits = [(lab, vals) for lab, vals in secs.get(sec, []) if any(n.replace(" ", "") in lab.replace(" ", "") for n in needles) and not any(e in lab.replace(" ", "") for e in exclude)]
        if len(hits) < nth:
            return None
        return pick(hits[nth - 1][1], cum_idx, k)
    out = {}
    if style == "KB":
        csm = v("rev", ["보험계약마진상각"]) ; ra = v("rev", ["위험해제로인한위험조정의변동"])
        rev_exp = v("rev", ["예상보험금및보험서비스비용"]); cost_act = v("cost", ["보험금및보험서비스비용"], exclude=("총",))
        re_csm = v("re_cost", ["제공받은서비스의재보험계약마진"]); re_ra = v("re_cost", ["위험해제로인한위험조정의변동"])
        re_rev = v("re_rev", ["회수가능보험금및보험서비스비용"]); re_exp = v("re_cost", ["회수예상보험금및보험서비스비용"])
        tr = v("rev", ["총보험수익"]); tc = v("cost", ["총보험서비스비용"]); trr = v("re_rev", ["총재보험수익"]); trc = v("re_cost", ["총재보험비용"])
        # 총 보험서비스결과 row sits after the last section; look it up from the flat table
        gl = None
        for r in t["rows"]:
            if r["cells"] and r["cells"][0]["t"].replace(" ", "") == "총보험서비스결과":
                gl = [nz(c["t"]) for c in r["cells"][1:]]
        res["raw"] = dict(csm=csm, ra=ra, rev_exp=rev_exp, cost_act=cost_act, re_csm=re_csm, re_ra=re_ra, re_rev=re_rev, re_exp=re_exp, tr=tr, tc=tc, trr=trr, trc=trc, gl=[gl[i] for i in cum_idx] if gl else None)
        out[4] = abs(csm) if csm is not None else None
        out[5] = abs(ra) if ra is not None else None
        out[6] = (abs(rev_exp) - abs(cost_act)) if None not in (rev_exp, cost_act) else None
        out[9] = -abs(re_csm) if re_csm is not None else None
        out[10] = -abs(re_ra) if re_ra is not None else None
        out[11] = (abs(re_rev) - abs(re_exp)) if None not in (re_rev, re_exp) else None
        if None not in (tr, tc, trr, trc):
            out[3] = tr - abs(tc); out[8] = trr - abs(trc); out[2] = out[3] + out[8]
        if gl:
            g = [gl[i] for i in cum_idx]
            out["gl"] = g
            out[13] = g[2]
            out[14] = g[1] + (g[3] if len(g) >= 5 else 0)
    return out, secs, cum_idx


if __name__ == "__main__":
    # KB buckets
    KB = {("KR0010", "2023.1Q"): ("data/dart/FY2024_Q1/raw/KR0010_KB손해보험/20240516001008.xml", 35403),
          ("KR0010", "2023.2Q"): ("data/dart/FY2024_Q2/raw/KR0010_KB손해보험/20240814002750.xml", 38795),
          ("KR0010", "2023.4Q"): ("data/dart/FY2024_Q4/raw/KR0010_KB손해보험_20250314001697/20250314001697.xml", 65978),
          ("KR0010", "2024.1Q"): ("data/dart/FY2025_Q1/raw/KR0010_KB손해보험/20250515001437.xml", 36148),
          ("KR0010", "2024.2Q"): ("data/dart/FY2025_Q2/raw/KR0010_KB손해보험/20250814003072.xml", 39399),
          ("KR0010", "2024.3Q"): ("data/dart/FY2025_Q3/raw/KR0010_KB손해보험/20251114001554.xml", 33735)}
    for (c, q), (f, ln) in KB.items():
        doc = xmlrd.get(ROOT + f)
        ti, t = doc.table_at_line(ln)
        out, secs, cum_idx = compute(doc, t, "KB")
        print("==", c, q, f.split("/")[-1], "table", t["start"], "cum_idx", cum_idx)
        for it in (2, 3, 4, 5, 6, 8, 9, 10, 11, 13, 14):
            m, h = master.get((c, q, it)), head.get((c, q, it))
            e = out.get(it)
            flag = "" if (e is not None and m is not None and abs(e - m) < 0.51) else "  <== DIFF"
            print(f"  item{it}: expected={e} master={m} head={h}{flag}")


# ---------------------------------------------------------------- style B (Meritz / Lotte single table) and Lotte split
def styleB(doc, t, sty):
    secs, cum_idx, ncols = read_table(doc, t)
    # tolerate '누 적'
    out = {}
    if sty == "LOTTE":
        N = dict(csm=["보험계약마진상각"], ra=["위험조정변동"], rev_exp=["예상보험금및예상기타보험서비스비용"], cost_act=["발생보험금및기타서비스비용"],
                 re_csm=["보험계약마진상각"], re_ra=["위험조정변동"], re_rev=["발생보험금및기타재보험수익"], re_exp=["회수예상보험금및기타보험서비스비용"],
                 tr=["총보험수익"], tc=["총보험비용"], trr=["총재보험수익"], trc=["총재보험비용"])
    else:  # MERITZ
        N = dict(csm=["당기손익으로인식한보험계약마진금액"], ra=["위험해제에따른위험조정변동"], rev_exp=["예상보험금및보험서비스비용"], cost_act=["보험금및보험서비스비용"],
                 re_csm=["당기손익으로인식한보험계약마진금액"], re_ra=["위험해제에따른위험조정변동"], re_rev=["회수가능보험금및보험서비스비용"], re_exp=["회수예상보험금및보험서비스비용"],
                 tr=["총보험수익"], tc=["총보험서비스비용"], trr=["총재보험수익"], trc=["총재보험비용"])

    def g(sec, key, k, excl=()):
        for lab, vals in secs.get(sec, []):
            l = lab.replace(" ", "")
            if any(n in l for n in N[key]) and not any(e in l for e in excl):
                return vals[cum_idx[k]]
        return None
    csm = g("rev", "csm", 0); ra = g("rev", "ra", 0); rev_exp = g("rev", "rev_exp", 0)
    cost_act = g("cost", "cost_act", 0, excl=("총", "미적용", "적용계약"))
    re_csm = g("re_cost", "re_csm", 0); re_ra = g("re_cost", "re_ra", 0)
    re_rev = g("re_rev", "re_rev", 0, excl=("총",)); re_exp = g("re_cost", "re_exp", 0)
    raw = dict(csm=csm, ra=ra, rev_exp=rev_exp, cost_act=cost_act, re_csm=re_csm, re_ra=re_ra, re_rev=re_rev, re_exp=re_exp)
    out[4] = abs(csm) if csm is not None else None
    out[5] = abs(ra) if ra is not None else None
    out[6] = (rev_exp - cost_act) if None not in (rev_exp, cost_act) else None
    out[9] = -abs(re_csm) if re_csm is not None else None
    out[10] = -abs(re_ra) if re_ra is not None else None
    out[11] = (abs(re_rev) - abs(re_exp)) if None not in (re_rev, re_exp) else None
    tot = {}
    for key, sec in (("tr", "rev"), ("tc", "cost"), ("trr", "re_rev"), ("trc", "re_cost")):
        tot[key] = [g(sec, key, k) for k in range(len(cum_idx))]
    raw["tot"] = tot
    if all(tot[x][0] is not None for x in tot):
        out[3] = tot["tr"][0] - abs(tot["tc"][0])
        out[8] = tot["trr"][0] - abs(tot["trc"][0])
        out[2] = out[3] + out[8]
        def net(k):
            return tot["tr"][k] - abs(tot["tc"][k]) + tot["trr"][k] - abs(tot["trc"][k])
        out[14] = net(1); out[13] = net(2)
    return out, raw


def lotte_split(doc, prior_marker_words=("전반기", "전분기")):
    """Lotte 2025-era: 8 prior-period tables in a row; returns outputs for LOB 장기/일반/자동차 (누적 columns)."""
    import re as _re
    pri = []
    for ti, t in enumerate(doc.tables):
        if not t["rows"] or len(t["rows"]) < 2:
            continue
        pre = xmlrd.strip(doc.text[max(0, t["pos"] - 400):t["pos"]])
        # the marker is the last cell text before the table ('전반기 (단위 : 백만원)')
        if _re.search(r"(전반기|전분기)\s*\(단위", pre[-40:]):
            pri.append(t)
    return pri
