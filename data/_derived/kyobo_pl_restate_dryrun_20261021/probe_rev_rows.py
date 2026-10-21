"""Read-only: print every row of the Kyobo 보험수익 (rev) and 보험서비스비용 (cost) note tables of a filing with its numeric cells."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plib
C = plib.C
sys.stdout.reconfigure(encoding="utf-8")
for q in sys.argv[1:]:
    tables = plib.parse_tables(plib.raw_dirs(q))
    picks = plib.kyobo_picks(tables)
    for k in ("rev",):
        t = picks[k]
        print("=" * 100)
        print(q, k, (t.caption or "")[:80] if t else None)
        if t is None:
            continue
        print("header:", " / ".join("|".join(str(c) for c in row)[:80] for row in (t.header or [])[:3]))
        for r in t.rows:
            print("   ", C._life_label_flat(r)[:60].ljust(60), C._row_nums(r))
