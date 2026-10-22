"""p_kblife: prototype of the Tier-2 PRIOR-column reader for KB라이프생명 (KR0099).
production extract_tier2_kblife: picks the table whose header names the CURRENT period and reads block 'first' (당기/전기 annual note) or 'last' (3개월/누적 or single).
prior variant: annual note -> block 2 (전기); quarterly -> the TWIN table whose header names 전분기/전반기/전기, same block rule.  Production helper _kblife_block_total is reused unchanged.
READ-ONLY.  usage: p_kblife.py <quarters csv>"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import prod as P  # noqa: E402
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
C = P.C
_norm, _is_rollforward = C._norm, C._is_rollforward


def kblife(tables, prior):
    note = None
    for t in tables:
        cap = (t.caption or "").replace(" ", "")
        if "기타사업비용을제외한" not in cap or "보험영업수익" not in cap or "보험영업비용" not in cap:
            continue
        if _is_rollforward(t):
            continue
        hb = " ".join(" ".join(h) for h in t.header)
        cur_ok = any(k in hb for k in ("당분기", "당반기", "당기"))
        pri_ok = any(k in hb for k in ("전분기", "전반기", "전기"))
        if not any(_norm(r[0]).replace(" ", "") == "서비스제공에따른보험계약마진의변동" for r in t.rows):
            continue
        if not prior and cur_ok:
            note = t
            break
        if prior:
            if cur_ok and pri_ok and ("전기" in hb):        # annual 당기/전기 in one table -> block 2
                note = t
                break
            if pri_ok and not cur_ok:                         # quarterly prior twin
                note = t
                break
    if note is None:
        return {}, None
    hbn = " ".join(" ".join(h) for h in note.header).replace(" ", "")
    annual_two_block = ("당기" in hbn and "전기" in hbn)
    if prior:
        which = "last" if annual_two_block else "last"
    else:
        which = "first" if "전기" in hbn else "last"
    g = lambda nd: C._kblife_block_total(note, which, nd)
    out = {}
    csm, ra = g("서비스제공에 따른 보험계약마진의 변동"), g("위험해제에 따른 위험조정의 변동")
    re_csm, re_ra = g("제공받은 서비스의 재보험계약마진"), g("위험해제로 인한 위험조정의 변동")
    if csm is not None:
        out[4] = abs(csm)
    if ra is not None:
        out[5] = abs(ra)
    if re_csm is not None:
        out[9] = -abs(re_csm)
    if re_ra is not None:
        out[10] = -abs(re_ra)
    return out, note.line_no


pl, names, inames = M.load_pl()
res, txt = {}, []
for q in sys.argv[1].split(","):
    m = pl[("KR0099", q)]
    tabs = P.tables_for("KR0099", M.later_fy(q))
    cur, lc = kblife(tabs, False)
    pri, lp = kblife(tabs, True)
    del tabs
    tabs_o = P.tables_for("KR0099", M.fy_of(q))
    o, lo = kblife(tabs_o, False)
    del tabs_o
    res[q] = {"orig_run": o, "master": {str(k): m.get(k) for k in (4, 5, 9, 10)}, "later_cur": cur, "later_prior": pri, "lines": [lo, lc, lp]}
    txt.append(f"KR0099 {q}: master 4/5/9/10={[m.get(k) for k in (4, 5, 9, 10)]} | orig-filing run {o} (L{lo}) | later cur {cur} (L{lc}) | later PRIOR {pri} (L{lp})")
M.MEASURE.joinpath("p_kblife.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("p_kblife.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt))
