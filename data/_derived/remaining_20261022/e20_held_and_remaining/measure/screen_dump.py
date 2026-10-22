import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
for scn in sys.argv[1:]:
    d = json.loads((M.MEASURE / f"cands_{scn}.json").read_text(encoding="utf-8"))
    print("==", scn)
    cs = {}
    for c in d["csm_cells"]:
        if c["item"] == 6:
            cs[(c["code"], c["q"])] = (c["old"], c["new"])
    for k, b in d["buckets"].items():
        code, q = k.split("|")
        s = b["screen_eok"]
        short = {nm: v[2] for nm, v in s.items()}
        csm6 = cs.get((code, q))
        print(f"  {k} pl={b['n_pl']} csm={b['n_csm']} dEOK={short}" + (f" CSM기말 {csm6[0]}->{csm6[1]} ({csm6[1]-csm6[0]:+.1f}억)" if csm6 and csm6[0] is not None else ""))
