"""a34: original-vintage print of the gold-overlapping READY cells (own Tier-1 statement reader on the ORIGINAL filing, current cumulative column) vs the gold values (READ-ONLY)"""
import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_plan_lib as P
import e21_read as R
sys.stdout.reconfigure(encoding="utf-8")
gold = P.head_json("data/_gold/user_pl_cells.json")
G = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
for code, q, i in (("KR0010", "2023.1Q", 16), ("KR0010", "2023.2Q", 16), ("KR0010", "2024.2Q", 16), ("KR0003", "2023.2Q", 19), ("KR0001", "2023.1Q", 16), ("KR0001", "2023.2Q", 16), ("KR0068", "2023.1Q", 20), ("KR0068", "2023.2Q", 21)):
    try:
        st = R.Stmt(code, P.orig_fy(q))
        v = R.read_vector(st, "cur", "cum")
        c = v[i]
        parts = [(p.label[:20], p.line, p.printed, p.sign) for p in c["parts"]]
        print(f"{code} {q} i{i}: gold={G[(code, i, q)]['값']} orig-print={round(sum(p.sign * p.val_mn for p in c['parts']), 6)} unit={st.unit} fmt={st.fmt} file={st.rel} parts={parts}")
    except Exception as e:
        print(f"{code} {q} i{i}: ERROR {type(e).__name__}: {str(e)[:200]}")
