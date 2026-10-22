from pathlib import Path
p = Path("e19_diff_vs_head.py")
s = p.read_text(encoding="utf-8")
s = s.replace("cover = {(k[0], k[2]) for k in dif}", "cover = {(k[0], k[1]) for k in dif}")
s = s.replace("(k[0], k[2]) not in cover)", "(k[0], k[2]) not in cover)")
s = s.replace('d = [(i, a, b) for i, (a, b) in enumerate(zip(ht, lt)) if a != b]', 'import difflib\nd = [x for x in difflib.unified_diff(ht, lt, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]')
s = s.replace("len(lt) == len(ht) + 1 and len(d) <= 2", "len(lt) == len(ht) + 1 and len(d) == 3")
p.write_text(s, encoding="utf-8", newline="\n")
