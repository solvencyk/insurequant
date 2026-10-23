# -*- coding: utf-8 -*-
"""KR0099 probe (read-only): dump the separate comprehensive income statement of a filing with ALL value cells (blank ones included).  usage: dump_stmt23.py <code> <FYxxxx_Qn>"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife")
import e23_read as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
code, fy = sys.argv[1], sys.argv[2]
st = X.Stmt23(code, fy)
print(st.rel, "fmt", st.fmt, "unit", st.unit, "title", st.title)
for k, r in enumerate(st.rows):
    a = getattr(r, "allcells", None) or []
    cells = [(c["text"], c["line"]) for c in a]
    print(f"{k:3d} L{r.line} {'OCI' if r.oci else '   '} {'SUB' if r.subtotal else '   '} {r.raw!r} n={len(a)} -> {cells}")
