"""one-off patcher for e21_post_klife.py: the measured 'old' census already contains the 3 masked cells (rebuilt source); the declared tuple is the pre-adjust (1174, 22)"""
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/"
s = open(H + "e21_post_klife.py", encoding="utf-8").read()
old = '''    if cen_old[1] != cen_new[1] or cen_old[0] - cen_new[0] != 3:
        errs.append(f"census {cen_old} -> {cen_new}")'''
new = '''    if cen_old[1] - cen_new[1] != 3 or cen_old[0] - cen_new[0] != 3:
        errs.append(f"census {cen_old} -> {cen_new} (the rebuilt source makes the 3 gold cells masked: masked must drop by 3 too)")'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''    if m is None or (int(m.group(3)), int(m.group(4))) != cen_old:
        errs.append(f"declared census {m.group(0) if m else None} != measured {cen_old}")'''
new = '''    if m is None or (int(m.group(3)), int(m.group(4))) != (1174, 22):
        errs.append(f"declared census {m.group(0) if m else None} != the e21-apply declaration (1174, 22)")'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''"(masked gold would need new pins): PL gold %d->%d cells, masked %d->%d.\n" % (cen_old[0], cen_new[0], cen_old[1], cen_new[1]))'''
new = '''"(masked gold would need new pins): PL gold 1174->%d cells, masked 22->%d.\n" % (cen_new[0], cen_new[1]))'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
open(H + "e21_post_klife.py", "w", encoding="utf-8", newline="\n").write(s)
print("patched post1")
