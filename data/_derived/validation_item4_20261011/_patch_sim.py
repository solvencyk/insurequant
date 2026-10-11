import re
p = "data/_derived/validation_item4_20261011/sim_item4_lineage.py"
s = open(p, encoding="utf-8").read()
a = s.index("def zleg(proposed):")
b = s.index("def main():")
new_fn = '''def zleg_run(pl_idx, src):
    import contextlib, io
    na = {}
    with contextlib.redirect_stdout(io.StringIO()):
        _p, _f, _s, zrows, _z0 = V._check_pl_bridge(pl_idx, *V.load_pl_extra_lob(V.PL_PATH), source_ids=src, src_na_out=na)
    return {(c, q) for c, q, *_r in zrows}, na


def zleg_sim():
    """current code on live data  vs  current code on data where item 4 is hidden in DISCLOSURE-lineage buckets whose
    other 9 legs are all None  ==  proposed rule on live data (the proposed rule only changes that all-None test)."""
    import copy
    pl = V.load_long(V.PL_PATH)
    src = V.pl_cell_source_ids()
    cur_flag, cur_na = zleg_run(pl, src)
    other = [k for k in ["생명장기원수손익", "원수위험조정변동", "원수예실차", "기타생명장기원수손익", "생명장기재보험손익",
                         "재보험CSM상각", "재보험위험조정변동", "재보험예실차", "기타생명장기재보험손익"]]
    pl2 = copy.deepcopy(pl)
    hidden = []
    for key, m in pl2.items():
        if src.get(key) == "DISCLOSURE" and m.get("원수CSM상각") is not None and all(m.get(k) is None for k in other):
            m["원수CSM상각"] = None
            hidden.append(key)
    new_flag, new_na = zleg_run(pl2, src)
    return cur_flag, cur_na, new_flag, new_na, hidden


'''
s = s[:a] + new_fn + s[b:]
s = s.replace('''    # sidecar blocks carrying the how''', '''    cf, cn, nf, nn, hidden = zleg_sim()
    print(f"(b) 2b ZERO_LEGS  current flag={len(cf)} src_na zleg={cn.get('zleg')} legcov={cn.get('legcov')}  "
          f"proposed flag={len(nf)} src_na zleg={nn.get('zleg')} legcov={nn.get('legcov')}  (item-4-hidden buckets={len(hidden)})")
    print(f"    closed ({len(cf - nf)}): {sorted(cf - nf)}")
    print(f"    newly broken ({len(nf - cf)}): {sorted(nf - cf)}")
    print(f"    still flagged ({len(nf)}): {sorted(nf)}")
    # sidecar blocks carrying the how''')
open(p, "w", encoding="utf-8", newline="\n").write(s)
