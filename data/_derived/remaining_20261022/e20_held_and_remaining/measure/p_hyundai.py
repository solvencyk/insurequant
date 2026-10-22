"""p_hyundai: run the production 현대해상 Tier-2 handler on a filing's tables normally and with the 당기/전기 markers swapped (prior mode prototype).  READ-ONLY.
usage: p_hyundai.py <FY_Q> [<FY_Q> ...] -> p_hyundai.txt"""
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import prod as P
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
C = P.C
orig = C._hyundai_period_marker
txt = []
for fy in sys.argv[1:]:
    tabs = P.tables_for("KR0009", fy)
    C._hyundai_period_marker = orig
    cur = C.extract_tier2_hyundai(tabs)
    C._hyundai_period_marker = lambda tables, ti: {"cur": "prev", "prev": "cur"}.get(orig(tables, ti))
    pri = C.extract_tier2_hyundai(tabs)
    C._hyundai_period_marker = orig
    summ_t, summ_r = C._hyundai_lob_summary(tabs)
    fmt = lambda d: {str(k): (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()}
    txt.append(f"=== {fy}\n  current-mode: {fmt(cur)}\n  prior-mode  : {fmt(pri)}\n  lob_summary row: {None if summ_r is None else [c for c in summ_r]}")
    del tabs
M.MEASURE.joinpath("p_hyundai.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt))
