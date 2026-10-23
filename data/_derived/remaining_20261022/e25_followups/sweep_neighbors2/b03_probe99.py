import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R
st = R.Stmt("KR0099", sys.argv[1])
print(st.rel, st.fmt, st.unit)
for r in st.rows:
    if r.oci: continue
    print(r.line, repr(r.lab), [(c["text"], (c["ctx"] or "")[:16]) for c in r.cells][:6])
