import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/apply")
import e20_read as R
sys.stdout.reconfigure(encoding="utf-8")
for code, fy in (("KR0003", "FY2024_Q2"), ("KR0079", "FY2025_Q1")):
    st = R.Stmt(code, fy)
    print("#####", code, fy, st.fmt, st.unit, st.rel, "rows", len(st.rows))
    for r in st.rows:
        vals = [(c["text"]) for c in r.cells if c["text"] not in ("",)]
        print(f"  L{r.line} {r.raw.strip()[:40]!r} -> {r.lab!r} oci={r.oci} sect={r.sect} | {vals[:6]}")
