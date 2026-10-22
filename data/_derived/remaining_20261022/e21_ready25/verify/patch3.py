p="v10_note_engine.py"
s=open(p,encoding="utf-8").read()
old=s[s.index("    leaf = None\n"):s.index("    secs = collections.OrderedDict()")]
new='''    hdr = None
    for r in t["rows"]:
        txts = [c["t"] for c in r["cells"]]
        if "누적" in txts and "3개월" in txts:
            hdr = r
            break
'''
s=s.replace(old,new)
old2=s[s.index("    ncols = max("):s.index("    return secs, cum_idx, ncols")]
new2='''    ncols = max((len(v) for s in secs.values() for _, v in s), default=0)
    if hdr:
        T = sum(c["span"] for c in hdr["cells"])
        off = ncols - T
        cum_idx = []
        c0 = 0
        for c in hdr["cells"]:
            if c["t"] == "누적":
                cum_idx += [c0 + off + j for j in range(c["span"])]
            c0 += c["span"]
    else:
        cum_idx = list(range(ncols))
'''
s=s.replace(old2,new2)
open(p,"w",encoding="utf-8").write(s)
