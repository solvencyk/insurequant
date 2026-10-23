# -*- coding: utf-8 -*-
"""e23 probe (read-only): dump the separate comprehensive income statement rows (label, line, cells) of a filing.  usage: q05_dump_stmt.py <code> <FYxxxx_Qn> [maxrows]"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
code, fy = sys.argv[1], sys.argv[2]
mx = int(sys.argv[3]) if len(sys.argv) > 3 else 200
st = R.Stmt(code, fy)
print(st.rel, "fmt", st.fmt, "unit", st.unit, "title", st.title)
for k, r in enumerate(st.rows[:mx]):
    cells = [(c["text"], c["line"], (c["ctx"] or "")[:20]) for c in r.cells]
    print(f"{k:3d} L{r.line} {'OCI' if r.oci else '   '} {'SUB' if r.subtotal else '   '} {r.raw!r} -> {cells}")
