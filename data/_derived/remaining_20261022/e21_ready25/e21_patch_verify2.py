"""one-off patcher #2 for e21_verify.py: replace verify_part by the text in e21_vp_new.txt and apply the other edits"""
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/"
s = open(H + "e21_verify.py", encoding="utf-8").read()
a = s.index("def verify_part(")
b = s.index("SCALE = {")
new = open(H + "e21_vp_new.txt", encoding="utf-8").read()
s = s[:a] + new + "\n\n" + s[b:]

def rep(old, newt):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, newt)

rep('''                kind_ctx = ctx_pattern(meta, q) if (meta["fmt"] == "atoc" and c["item"] in range(1, 33) and not c["item"] in (3, 4, 5, 6, 8, 9, 10, 11, 13, 14)) else None
''', '''                kind_ctx = ctx_pattern(meta, q) if meta["fmt"] == "atoc" else None
''')
rep('''                ok, info = verify_part(p3["file"], p, role_ctx=None)''', '''                ok, info = verify_part(p3["file"], p, role_ctx=rf"^PFY{int(s['quarter'][:4])}d(FQQ|HYQ|TQQ)_")''')
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
open(H + "e21_verify.py", "w", encoding="utf-8", newline="\n").write(s)
print("patched verify2")
