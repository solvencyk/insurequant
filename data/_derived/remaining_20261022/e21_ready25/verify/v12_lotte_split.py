# -*- coding: utf-8 -*-
import sys, json; sys.stdout.reconfigure(encoding="utf-8")
import xmlrd, v10_note_engine as E
R = E.ROOT
master, head = E.master, E.head
CFG = {("KR0003","2024.2Q"): ("data/dart/FY2025_Q2/raw/KR0003_롯데손해보험/xml/20250814003966.xml", [58037,58628,59020,59560,60274,60935,61487,61879]),
       ("KR0003","2024.3Q"): ("data/dart/FY2025_Q3/raw/KR0003_롯데손해보험/xml/20251114002985.xml", [32050,32353,32577,32844,33198,33520,33811,34035])}

def rows_of(t):
    res = []
    for r in t["rows"]:
        cs = [c["t"] for c in r["cells"]]
        # numeric tail
        vals = []
        for c in cs:
            v = E.nz(c)
            vals.append(v)
        res.append((cs, vals))
    return res

def cum_cols(vals_len, t):
    # all these tables have 3개월/누적 pairs; cumulative = odd index among the last 8 values
    return None

def lastnums(cs, n=8):
    nums = []
    for c in cs:
        v = xmlrd.parse_num(c)
        if v is None and c.strip() in ("-", "0"):
            v = 0.0
        nums.append(v)
    tail = nums[-n:]
    return tail

def find_row(t, needle, nth=1, exclude=()):
    hits = []
    for r in t["rows"]:
        cs = [c["t"] for c in r["cells"]]
        lab = "".join(cs[:2]).replace(" ", "")
        if needle.replace(" ", "") in lab and not any(e in lab for e in exclude):
            tail = lastnums(cs)
            if all(x is not None for x in tail) and len(tail) == 8:
                hits.append((cs, tail))
    return hits[nth-1] if len(hits) >= nth else (None, None)

for (c,q),(f,starts) in CFG.items():
    d = xmlrd.get(R+f)
    T = []
    for s in starts:
        ti, t = d.table_at_line(s)
        assert t["start"] == s, (s, t["start"])
        T.append(t)
    cum = lambda tail, k: tail[2*k+1]    # k: 0 장기 1 일반 2 자동차 3 합계
    # T0 rev nonPAA, T1 rev PAA, T2 rev total, T3 cost, T4 re_rev, T5 re_cost nonPAA, T6 re_cost PAA, T7 re_cost total
    def val(t, needle, k=0, **kw):
        cs, tail = find_row(t, needle, **kw)
        return None if tail is None else cum(tail, k)
    if q == "2024.2Q":
        L = dict(csm="서비스의 이전으로 당기손익에 인식한 보험계약마진", ra="비금융위험에 대한 위험조정의 변동분", rev_exp="보고기간에 발생한 보험서비스비용",
                 cost_act="발생한 보험금 및 그 밖의", re_rev="발생보험금 및 기타재보험수익", re_exp="보고기간에 발생한 보험서비스비용")
    else:
        L = dict(csm="보험계약마진 상각", ra="위험조정 변동", rev_exp="예상보험금 및 예상기타보험서비스비용",
                 cost_act="발생보험금 및 기타서비스비용", re_rev="발생보험금 및 기타재보험수익", re_exp="회수예상 보험금 및 기타보험서비스비용")
    csm = val(T[0], L["csm"]); ra = val(T[0], L["ra"]); rev_exp = val(T[0], L["rev_exp"])
    cost_act = val(T[3], L["cost_act"]); re_rev_act = val(T[4], L["re_rev"])
    re_csm = val(T[5], L["csm"]); re_ra = val(T[5], L["ra"]); re_exp = val(T[5], L["re_exp"])
    def last_tail(t):
        for r in reversed(t["rows"]):
            cs = [x["t"] for x in r["cells"]]
            tail = lastnums(cs)
            if len(tail) == 8 and all(x is not None for x in tail):
                return cs[:2], tail
    rv = last_tail(T[2]); cs_ = last_tail(T[3]); rr = last_tail(T[4]); rc = last_tail(T[7])
    print("==", c, q, "labels of totals:", rv[0], cs_[0], rr[0], rc[0])
    out = {4: abs(csm) if csm is not None else None, 5: abs(ra) if ra is not None else None,
           6: (rev_exp - cost_act) if None not in (rev_exp, cost_act) else None,
           9: -abs(re_csm) if re_csm is not None else None, 10: -abs(re_ra) if re_ra is not None else None,
           11: (abs(re_rev_act) - abs(re_exp)) if None not in (re_rev_act, re_exp) else None}
    out[3] = cum(rv[1],0) - abs(cum(cs_[1],0))
    out[8] = cum(rr[1],0) - abs(cum(rc[1],0))
    out[2] = out[3] + out[8]
    net = lambda k: cum(rv[1],k) - abs(cum(cs_[1],k)) + cum(rr[1],k) - abs(cum(rc[1],k))
    out[14] = net(1); out[13] = net(2)
    print("  raw: csm",csm,"ra",ra,"rev_exp",rev_exp,"cost_act",cost_act,"re_rev_act",re_rev_act,"re_csm",re_csm,"re_ra",re_ra,"re_exp",re_exp)
    for it in (2,3,4,5,6,8,9,10,11,13,14):
        m,h,e = master.get((c,q,it)), head.get((c,q,it)), out.get(it)
        dd = "" if (e is not None and m is not None and abs(e-m) < 0.51) else "  <== DIFF"
        print(f"  item{it}: expected={e} master={m} head={h}{dd}")
