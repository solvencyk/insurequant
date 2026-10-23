# -*- coding: utf-8 -*-
"""kr0003_verify.py: add section F = the issuer's OWN restatement table (note 47, '소급 전 / 재작성효과 / 소급 후' for 제79(전)기) as a third, independent witness of the restated FY2023 values."""
from pathlib import Path

p = Path("kr0003_verify.py")
s = p.read_text(encoding="utf-8")

func = '''
def issuer_restatement_table(rel):
    """the issuer's note '재무제표 소급재작성 - 포괄손익계산서에 미치는 영향' for 제79(전)기: {normalised label: (before, effect, after)} in 백만원 (rows with 5 cells: label, note ref, 소급 전, 재작성효과, 소급 후)"""
    L = lines_of(rel)
    found = []
    for (a, b) in all_tables(L):
        hp = header_paths(L, a, b)
        if not hp:
            continue
        flat = " ".join(nspace(x) for p_ in hp for x in p_)
        if "소급전" in flat and "재작성효과" in flat and "소급후" in flat and "제79(전)기" in flat:
            rows = body_rows(L, a, b)
            labs = [norm_label(r["cells"][0]["text"]) for r in rows if r["cells"]]
            if "보험손익" in labs and "당기순이익" in labs:
                found.append((a, b, rows))
    if len(found) != 1:
        raise RuntimeError(f"{rel}: {len(found)} candidate restatement-effect tables for the statement of comprehensive income")
    a, b, rows = found[0]
    out = {}
    for r in rows:
        cs = r["cells"]
        if len(cs) == 5:
            vals = [parse_num(c["text"]) for c in cs[2:5]]
            if None not in vals:
                out.setdefault(norm_label(cs[0]["text"]), (vals[0], vals[1], vals[2], cs[0]["line"], cs[4]["line"]))
    return (a + 1, b + 1), out

'''
marker = "# ================================================================================================ main\n"
assert s.count(marker) == 1
s = s.replace(marker, func + marker)

sec = '''
    # ------------------------------------------------------------------ F. the issuer's own restatement table (note 47)
    say("")
    say("== F. issuer's OWN restatement table (FY2024 annual report, note 47 'effect on the statement of comprehensive income', 제79(전)기: 소급 전 / 재작성효과 / 소급 후, 백만원)")
    (ta, tb), rt = issuer_restatement_table(F["A24"])
    say(f"  table L{ta}-{tb}; {len(rt)} rows with 3 numbers")
    pairs = [("보험손익", 1), ("투자손익", 17), ("영업이익", 20), ("법인세비용차감전순이익", 22), ("법인세비용", 23), ("당기순이익", 24), ("기타포괄손익", 25),
             ("기타포괄손익-공정가치측정채무증권평가손익", 26), ("보험계약자산(부채)순금융손익", 27), ("총포괄손익", 31)]
    nF = 0
    for lab, it_ in pairs:
        bef, eff, aft, ll, la = rt[norm_label(lab)]
        old = pl_live[(CODE, it_, Q)]["값"]
        new_mn = allnew[it_]
        ok_after = abs(aft - new_mn) <= 1.0
        ok_before = abs(bef - old) <= 2.0
        ok_eff = abs((aft - bef) - eff) <= 1.0
        ok_delta = abs(eff - (new_mn - old)) <= 2.0
        nF += 1 if (ok_after and ok_before and ok_eff and ok_delta) else 0
        say(f"  item {it_:2d} {lab[:22]:22s}: issuer 소급전 {bef:>10,.0f} | 효과 {eff:>+9,.0f} | 소급후 {aft:>10,.0f}   ||   master old {old:>14,.3f} -> reread {new_mn:>14,.3f} (delta {new_mn - old:+,.3f})  after-ok {ok_after} before-ok {ok_before} effect-ok {ok_eff} delta-ok {ok_delta}  [L{la}]")
        if not (ok_after and ok_before and ok_eff and ok_delta):
            problem("F.issuer", f"item {it_}: issuer restatement table {bef}/{eff}/{aft} vs master old {old} / reread {new_mn}")
    fin_after = sum(rt[norm_label(x)][2] * sg for x, sg in (("보험금융수익", 1), ("재보험금융수익", 1), ("보험금융비용", -1), ("재보험금융비용", -1)))
    fin_before = sum(rt[norm_label(x)][0] * sg for x, sg in (("보험금융수익", 1), ("재보험금융수익", 1), ("보험금융비용", -1), ("재보험금융비용", -1)))
    say(f"  item 19 (보험금융수익+재보험금융수익-보험금융비용-재보험금융비용): issuer 소급전 {fin_before:,.0f} -> 소급후 {fin_after:,.0f}; master old {pl_live[(CODE, 19, Q)]['값']:,.3f} -> reread {allnew[19]:,.3f}")
    if abs(fin_after - allnew[19]) > 2.0 or abs(fin_before - pl_live[(CODE, 19, Q)]["값"]) > 3.0:
        problem("F.issuer", f"item 19: issuer table {fin_before}/{fin_after} vs master/reread")
    say(f"  -> {nF}/{len(pairs)} Tier-1 items agree with the issuer's own 소급 전 / 소급 후 table (소급 전 = the old master value, 소급 후 = the value adopted here)")
    RES["issuer_restatement_agree"] = nF

'''
marker2 = "    # ------------------------------------------------------------------ E. plan sanity\n"
assert s.count(marker2) == 1
s = s.replace(marker2, sec + marker2)
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
