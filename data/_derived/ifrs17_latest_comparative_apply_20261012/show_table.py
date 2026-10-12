"""usage: show_table.py <xml> <table_index[,idx...]> [maxrows=60] [maxcols=12]  -- echo a raw table with XML line numbers (read-only)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xmltab as X  # noqa: E402

xml = Path(sys.argv[1])
idxs = {int(x) for x in sys.argv[2].split(",")}
maxrows = int(sys.argv[3]) if len(sys.argv) > 3 else 60
maxcols = int(sys.argv[4]) if len(sys.argv) > 4 else 12
for t in X.load_tables(str(xml)):
    if t.index in idxs:
        print(f"--- table #{t.index} line {t.line} unit={t.unit!r} captions={t.captions[-3:]!r}")
        for r in t.rows[:maxrows]:
            print(f"   L{r.line:<6}", [c[:34] for c in r.cells[:maxcols]])
