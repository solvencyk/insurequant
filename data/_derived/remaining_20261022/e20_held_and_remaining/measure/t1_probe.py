"""t1_probe: what does the production HTML Tier-1 extractor return for a filing? (root-cause check for KR0104 2023.1Q/2Q) READ-ONLY"""
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import prod as P, fsapi as F, mlib as M
sys.stdout.reconfigure(encoding="utf-8")
code = sys.argv[1]
for fy in sys.argv[2].split(","):
    tabs = P.tables_for(code, fy)
    t1 = P.extract_tier1(tabs, code=code)
    api, div = F.same(code, fy.replace("FY", "").replace("_Q", ".") + "Q")
    print(fy, "tables:", len(tabs), "| HTML tier1 ->", None if t1 is None else {k: (round(v, 1) if isinstance(v, float) else v) for k, v in list(t1.items())[:12]}, "| FS-API same ->", None if api is None else "present", "| FS-API cache file exists:", F.load(code, fy[2:6], F.fdf.REPRT[fy[-1] + "Q"], "OFS") is not None)
