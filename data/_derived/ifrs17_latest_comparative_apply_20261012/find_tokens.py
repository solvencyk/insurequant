"""usage: find_tokens.py <xml> <value_in_master_unit> [scale=100] [tol_master=0.051]
Print every table row of the XML that prints a numeric cell within tol of value*scale (abs values compared)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xmltab as X  # noqa: E402

xml = Path(sys.argv[1])
vals = [float(x) for x in sys.argv[2].split(",")]
sc = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
tol = float(sys.argv[4]) if len(sys.argv) > 4 else 0.051
for t in X.load_tables(str(xml)):
    for r in t.rows:
        for ci, c in enumerate(r.cells[1:], 1):
            pv = X.printed_to_float(c)
            if pv is None:
                continue
            for v in vals:
                if abs(abs(pv) - abs(v) * sc) <= tol * sc:
                    print(f"v={v} table#{t.index} L{r.line} unit={t.unit!r} cap={t.caption[:50]!r} row={r.cells[0][:40]!r} col={ci} printed={c!r} | hdr={' '.join(t.rows[0].cells)[:80]!r}")
