import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
cs = M.load_csm()
code = sys.argv[1]
for q in sys.argv[2].split(","):
    m = cs.get((code, q), {})
    print(code, q, [m.get(i) for i in range(1, 7)])
