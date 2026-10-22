"""one-off patcher for e21_verify.py"""
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/e21_verify.py"
s = open(p, encoding="utf-8").read()

def rep(old, new, cnt=1):
    global s
    assert s.count(old) == cnt, (s.count(old), old[:70])
    s = s.replace(old, new)

rep('def verify_part(rel, p, role_ctx=None, expect_pos=None):', 'def verify_part(rel, p, role_ctx=None, expect_pos=None, skip_label=False):')
rep('''    nums = [c for c in cells if (parse_num(c[0]) is not None and c[0].strip() != "") or c[0].strip() in ("-", "\u2212", "")]
    first_num_idx = next((k for k, c in enumerate(cells) if parse_num(c[0]) is not None and c[0].strip() != ""), None)
    pos = None
    if first_num_idx is not None:
        seq = [c for k, c in enumerate(cells) if k >= first_num_idx or (c[0].strip() in ("-", "\u2212", ""))]
        seq = [c for c in cells if not (re.search(r"[가-힣A-Za-z]", c[0]) and parse_num(c[0]) is None)]
        pos = [c[1] for c in seq].index(ln) if ln in [c[1] for c in seq] else None''',
'''    seq = [c for c in cells if c[0].strip() != "" and parse_num(c[0]) is not None]
    pos = [c[1] for c in seq].index(ln) if ln in [c[1] for c in seq] else None''')
rep('''    label_ok = True
    if pl and len(pl) >= 2:''', '''    label_ok = True
    if pl and len(pl) >= 2 and not skip_label:''')
rep('''    if "연결" in tnorm and "재무제표주석" not in tnorm.replace("연결", "") and False:
        problems.append(f"consolidated section {title!r}")
    if re.search(r"연결재무제표", tnorm):
        problems.append(f"section is consolidated: {title!r}")
    if role_ctx is not None and ctx:
        if not re.match(role_ctx, ctx) or "SeparateMember" not in ctx:
            problems.append(f"ACONTEXT {ctx[:60]!r} !~ {role_ctx}")''',
'''    if re.search(r"연결재무제표", tnorm):
        problems.append(f"section is consolidated: {title!r}")
    if role_ctx is not None and ctx and "포괄손익계산서" in tnorm:
        if not re.match(role_ctx, ctx) or "SeparateMember" not in ctx:
            problems.append(f"ACONTEXT {ctx[:60]!r} !~ {role_ctx}")''')
rep('''    return (not problems), dict(problem="; ".join(problems) if problems else None, value=v, ctx=ctx, pos=pos, n=len(seq) if first_num_idx is not None else None, label=lab_all[:50], unit=u, title=title[:40])''',
    '''    return (not problems), dict(problem="; ".join(problems) if problems else None, value=v, ctx=ctx, pos=pos, n=len(seq), label=lab_all[:60], unit=u, title=title[:40])''')
# PL parts: role ctx on every part (verify_part applies it only to statement cells)
rep('''                kind_ctx = ctx_pattern(meta, q) if (meta["fmt"] == "atoc" and c["item"] in range(1, 33) and not c["item"] in (3, 4, 5, 6, 8, 9, 10, 11, 13, 14)) else None
''', '''                kind_ctx = ctx_pattern(meta, q) if meta["fmt"] == "atoc" else None
''')
rep('''                ok, info = verify_part(p3["file"], p, role_ctx=None)''', '''                ok, info = verify_part(p3["file"], p, role_ctx=rf"^PFY{int(s['quarter'][:4])}d(FQQ|HYQ|TQQ)_")''')
# CSM parts: keyword check instead of the label check
rep('''                rel = c["src"].split(" ")[0]
                ok, info = verify_part(rel, p)
                if not ok:
                    probs.append(f"L{p['line']}: {info['problem']}")
                else:
                    lab = norm(info["label"])
                    keys = CSM_KEYS[c["item"]]
                    if not any(norm(k) in lab for k in keys) and p.get("label", "").find("CSM 소계") < 0 and "col " not in p.get("label", "") and c["item"] != 6:
                        pass''', '''                rel = c["src"].split(" ")[0]
                ok, info = verify_part(rel, p, skip_label=True)
                if not ok:
                    probs.append(f"L{p['line']}: {info['problem']}")
                else:
                    lab = norm(info["label"])
                    keys = CSM_KEYS[c["item"]]
                    if not any(norm(k) in lab for k in keys):
                        probs.append(f"L{p['line']}: row label {info['label']!r} has none of {keys}")''')
rep('''5: ("상각", "당기인식분", "제공한서비스", "서비스의이전", "현행서비스"), 6: ("말",)}''', '''5: ("상각", "당기인식분", "제공한서비스", "서비스의이전", "현행서비스", "인식한보험계약마진"), 6: ("말",)}''')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched verify1")
