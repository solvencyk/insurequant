# -*- coding: utf-8 -*-
from n00_lib import *

out = {}
for (c, q), want in sorted(targets.items()):
    fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
    mq = f"{int(q[:4]) + 1}.{q[5:]}"
    rec = dict(file=None, items={}, err=None, blocks=0)
    try:
        path = T.main_path(c, fy)
        rec["file"] = str(path).replace("\\", "/").split("insurequant/")[-1]
        lines, bl = blocks_of(path)
        rec["blocks"] = len(bl)
        cal = collections.defaultdict(list)
        for bi, b in enumerate(bl):
            maxn = max((v["n"] for v in b["terms"].values()), default=0)
            for j in range(maxn):
                for i in ITEMS:
                    m = pl.get((c, i, mq))
                    if m is None or abs(m) < 0.5:
                        continue
                    v = item_value(b, i, j)
                    if v is None:
                        continue
                    if abs(abs(v["val"]) - abs(m)) <= 1.0:
                        cal[(bi, j)].append(i)
        for i in sorted(want):
            m_now = pl.get((c, i, q))
            m_cur = pl.get((c, i, mq))
            cands = [(bi, j) for (bi, j), its in cal.items() if i in its]
            method_cal = "SELF"
            if not cands:
                cands = [(bi, j) for (bi, j), its in cal.items() if item_value(bl[bi], i, j) is not None]
                method_cal = "COLUMN_FROM_OTHER_ITEMS"
            if not cands:
                rec["items"][i] = dict(status="UNCAL", why="no block/column reproduces the master at quarter+4 for this or a neighbouring item", master=m_now)
                continue
            cands.sort(key=lambda bj: (-len(cal[bj]), bj))
            bi, j = cands[0]
            b = bl[bi]
            n = max(v["n"] for v in b["terms"].values())
            prior = None
            how = None
            pb = None
            hdr = b["hdr"]
            if n % 2 == 0 and re.search(r"(전기|전분기|전반기)", hdr) and re.search(r"(당기|당분기|당반기)", hdr) and j < n // 2:
                bj = j + n // 2
                prior = item_value(b, i, bj)
                how = f"POS block@L{b['start']} col {j}->{bj} of {n}"
                pb = b
            if prior is None:
                s0 = sig(b)
                for b2 in bl[bi + 1:]:
                    if b2["start"] - b["end"] > 4000:
                        break
                    if set(termset(i)) <= set(b2["terms"]) and sig(b2) == s0:
                        prior = item_value(b2, i, j)
                        how = f"TWIN block@L{b['start']} -> block@L{b2['start']} col {j}"
                        pb = b2
                        break
            if prior is None:
                for b2 in bl[bi + 1:]:
                    if b2["start"] - b["end"] > 4000:
                        break
                    if set(termset(i)) <= set(b2["terms"]) and b2["terms"][termset(i)[0]]["n"] == b["terms"][termset(i)[0]]["n"]:
                        prior = item_value(b2, i, j)
                        how = f"TWIN_LOOSE block@L{b['start']} -> block@L{b2['start']} col {j}"
                        pb = b2
                        break
            if prior is None:
                rec["items"][i] = dict(status="NOPRIOR", why=f"calibrated current block@L{b['start']} col {j} but no twin/prior half found", master=m_now)
                continue
            cur = item_value(b, i, j)
            rec["items"][i] = dict(status="OK", val=prior["val"], raw=prior["raw"], cells=prior["cells"], tr=prior["tr"], how=how, cal=method_cal, cal_items=cal[(bi, j)],
                                   cur_val=cur["val"], cur_cells=cur["cells"], prior_hdr=pb["hdr"][:80], prior_cap=pb["cap"], unit=pb["unit"], master=m_now, master_cur=m_cur)
    except Exception as e:
        rec["err"] = f"{type(e).__name__}: {str(e)[:200]}"
    out[f"{c}|{q}"] = rec
    st = collections.Counter(v["status"] for v in rec["items"].values())
    print(c, q, dict(st), rec["err"] or "", f"blocks={rec['blocks']}", flush=True)
json.dump(out, open(S2 + "n01_notes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
