import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R
st = R.Stmt("KR0032", "FY2025_Q4")
print(st.rel, st.fmt, st.unit, len(st.rows))
for r in st.rows: print(r.line, repr(r.lab), [(c["text"], (c["ctx"] or "")[:12]) for c in r.cells][:4])
