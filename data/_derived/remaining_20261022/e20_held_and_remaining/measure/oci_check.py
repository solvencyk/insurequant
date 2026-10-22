import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import fsapi as F, mlib as M, cand as K
sys.stdout.reconfigure(encoding="utf-8")
code, q = sys.argv[1], sys.argv[2]
pl, names, inames = M.load_pl()
t1, div = F.prior(code, q)
m = pl[(code, q)]
print(code, q, "prior div", div)
for it in (24, 25, 26, 27, 28, 29, 30, 31, 32):
    print(f"  item {it} {inames.get(it,'')[:18]:<18} master={m.get(it)}  prior={t1.get(it)}")
s = sum((t1.get(i) or 0) for i in (26, 27, 28, 29, 30, 32))
print("  prior sum(26..30,32) =", s, " prior 25 =", t1.get(25), " diff =", s - (t1.get(25) or 0))
s2 = sum((m.get(i) or 0) for i in (26, 27, 28, 29, 30, 32))
print("  master sum =", s2, " master 25 =", m.get(25))
