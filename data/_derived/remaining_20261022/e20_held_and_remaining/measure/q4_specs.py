import json, sys
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
for scn in ("R0_KBlife_2024Q1_fix", "R1", "R1b_KB_siblings", "R2", "R2b_Lotte_2023_1Q2Q", "N1_KBlife_A", "N2_KBlife_B", "N4_ABL_FY2023", "N5_KDB_FY2023", "N6_HD_FY2023", "N7_Lotte_FY2023Q4", "ALL_latest", "X_mirae2023"):
    d = json.loads(open(M + f"cands_{scn}.json", encoding="utf-8").read())
    print(scn, ",".join(f"{s['code']}:{s['q']}:{s['prov']}{':csm' if s['csm'] else ''}" for s in d["specs"]))
