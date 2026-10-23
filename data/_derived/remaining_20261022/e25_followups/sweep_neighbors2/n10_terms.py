# -*- coding: utf-8 -*-
"""Part 2 v2: term-based calibrated reader for note items 4/5/6/9/10/11.  Read-only.
Each TERM (csm_rev, ra_rev, exp_rev, act_cost, csm_re, ra_re, recv_rerev, rexp_recost) is located as an occurrence (block, row) in the separate-basis notes of the later filing.
Single-term items: calibration = some (occurrence, column j) reproduces the master at quarter+4 (|diff|<=1 mn).
Two-term items (6, 11): calibration over (occurrence A, nearest following occurrence B with the same column count, column j): |A_j|-|B_j| == master at quarter+4.
Prior value of an occurrence = positional prior half of the same row (header names both periods) or the next occurrence of the same term with the same column count within 4000 lines (twin table)."""
import json, sys, re, collections
sys.argv = [sys.argv[0], "__lib__"] + sys.argv[1:]
from n00_lib import *     # blocks_of, pl, UD, ITEMS, S2, T, E, ...

ONLY2 = set(sys.argv[2:])
tg = collections.defaultdict(set)
for c, q, i in unc:
    if i in ITEMS and q != "2025.3Q" and (not ONLY2 or c in ONLY2):
        tg[(c, q)].add(i)

TERMS = {"4": ["csm_rev"], "5": ["ra_rev"], "9": ["csm_re"], "10": ["ra_re"], "6": ["exp_rev", "act_cost"], "11": ["recv_rerev", "rexp_recost"]}


def mn(occ, j):
    t = occ["t"]
    return t["nums"][j][0] / UD.get(occ["b"]["unit"], float("nan"))


def cite(occ, j):
    t = occ["t"]
    return dict(line=t["nums"][j][1], printed=t["nums"][j][2], tr=t["tr"], label=t["label"][:60], table=occ["b"]["start"], unit=occ["b"]["unit"], col=j, ncol=t["n"])


def prior_of(occ, j, occs):
    """-> (value_mn_raw, cite, how) or None"""
    b, t = occ["b"], occ["t"]
    n = t["n"]
    hdr = b["hdr"]
    if n % 2 == 0 and re.search(r"(전기|전분기|전반기)", hdr) and re.search(r"(당기|당분기|당반기)", hdr) and j < n // 2:
        return mn(occ, j + n // 2), cite(occ, j + n // 2), f"POS col {j}->{j + n // 2} of {n} (table@L{b['start']})"
    for o2 in occs:
        if o2["b"]["start"] <= b["start"]:
            continue
        if o2["b"]["start"] - b["end"] > 4000:
            break
        if o2["t"]["n"] == n and o2["t"]["label"][:12] == t["label"][:12]:
            return mn(o2, j), cite(o2, j), f"TWIN table@L{b['start']} -> table@L{o2['b']['start']} col {j}"
    return None


out = {}
for (c, q), want in sorted(tg.items()):
    fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
    mq = f"{int(q[:4]) + 1}.{q[5:]}"
    rec = dict(file=None, items={}, err=None, blocks=0)
    try:
        path = T.main_path(c, fy)
        rec["file"] = str(path).replace("\\", "/").split("insurequant/")[-1]
        lines, bl = blocks_of(path)
        rec["blocks"] = len(bl)
        occ = collections.defaultdict(list)
        for b in bl:
            for term, t in b["terms"].items():
                occ[term].append(dict(b=b, t=t))
        for i in sorted(want, key=int):
            m_now = pl.get((c, i, q))
            m_cur = pl.get((c, i, mq))
            ts = TERMS[i]
            cands = []   # (occA, occB|None, j)
            if m_cur is not None and abs(m_cur) >= 0.5:
                if len(ts) == 1:
                    sg = 1 if i in ("4", "5") else -1
                    for oa in occ[ts[0]]:
                        for j in range(oa["t"]["n"]):
                            if abs(abs(mn(oa, j)) - abs(m_cur)) <= 1.0:
                                cands.append((oa, None, j))
                else:
                    for oa in occ[ts[0]]:
                        for ob in occ[ts[1]]:
                            if ob["b"]["start"] < oa["b"]["start"] or ob["b"]["start"] - oa["b"]["end"] > 6000 or ob["t"]["n"] != oa["t"]["n"]:
                                continue
                            for j in range(oa["t"]["n"]):
                                if abs((abs(mn(oa, j)) - abs(mn(ob, j))) - m_cur) <= 1.5:
                                    cands.append((oa, ob, j))
                            break
            if not cands and m_cur is not None and abs(m_cur) < 0.5:
                rec["items"][i] = dict(status="UNCAL", why="master at quarter+4 is 0/blank-zero: cannot calibrate a column", master=m_now)
                continue
            if not cands:
                rec["items"][i] = dict(status="UNCAL", why="no occurrence/column reproduces the master at quarter+4" if m_cur is not None else "master at quarter+4 missing", master=m_now)
                continue
            oa, ob, j = cands[0]
            pa = prior_of(oa, j, occ[ts[0]])
            pb = prior_of(ob, j, occ[ts[1]]) if ob else None
            if pa is None or (ob and pb is None):
                rec["items"][i] = dict(status="NOPRIOR", why=f"calibrated (table@L{oa['b']['start']} col {j}) but no prior half/twin", master=m_now)
                continue
            if ob:
                val = abs(pa[0]) - abs(pb[0])
                cur = abs(mn(oa, j)) - abs(mn(ob, j))
                cites = [pa[1], pb[1]]
                how = pa[2] + " ; " + pb[2]
            else:
                sg = 1 if i in ("4", "5") else -1
                val = sg * abs(pa[0])
                cur = sg * abs(mn(oa, j))
                cites = [pa[1]]
                how = pa[2]
            rec["items"][i] = dict(status="OK", val=val, cites=cites, how=how, cur_val=cur, master=m_now, master_cur=m_cur, ncand=len(cands),
                                   raw_prior=[pa[0]] + ([pb[0]] if ob else []))
    except Exception as e:
        rec["err"] = f"{type(e).__name__}: {str(e)[:200]}"
    out[f"{c}|{q}"] = rec
    st = collections.Counter(v["status"] for v in rec["items"].values())
    print(c, q, dict(st), rec["err"] or "", f"blocks={rec['blocks']}", flush=True)
json.dump(out, open(S2 + "n10_terms.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
