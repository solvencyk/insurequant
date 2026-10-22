import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R
sys.stdout.reconfigure(encoding="utf-8")
for code, fy in (("KR0104", "FY2024_Q1"), ("KR0068", "FY2024_Q1"), ("KR0099", "FY2024_Q1")):
    st = R.Stmt(code, fy)
    print("#####", code, fy, st.fmt, st.unit, st.rel, "rows", len(st.rows))
    n = 0
    for r in st.rows:
        if r.oci:
            break
        n += 1
        vals = [c["text"] for c in r.cells if c["text"] != ""]
        if n <= 40:
            print(f"  L{r.line} {r.raw.strip()[:46]!r} | {vals[:4]}")
