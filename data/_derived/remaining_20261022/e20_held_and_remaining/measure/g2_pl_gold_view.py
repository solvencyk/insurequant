"""g2: owner PL gold cells (user_pl_cells.json 'set') of chosen buckets next to: master, FS-API original print (same), FS-API latest comparative (prior) (READ-ONLY).
usage: g2_pl_gold_view.py KR0010:2023.1Q,KR0010:2023.2Q,..."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import fsapi as F  # noqa: E402
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
gold = M.jload(M.SNAP / "user_pl_cells.json")
pl, names, inames = M.load_pl()
out = []
for sp in sys.argv[1].split(","):
    code, q = sp.split(":")
    t_same, _ = F.same(code, q)
    t_prior, _ = F.prior(code, q)
    for c in gold["set"]:
        if c["원보험사코드"] == code and c["공시분기"] == q:
            it = c["항목번호"]
            out.append(f"{code} {q} item{it:>2} {inames.get(it, '')[:14]:<14} gold={c.get('값')} | was={c.get('was')} | FS-API same={None if not t_same else t_same.get(it)} | FS-API prior={None if not t_prior else t_prior.get(it)} | note={(c.get('note') or '')[:110]}")
txt = "\n".join(out)
M.MEASURE.joinpath("g2_pl_gold_view.txt").write_text(txt, encoding="utf-8")
print(txt)
