"""Read-only: list the tables of the separate FS section of a filing (start line, caption, first row labels)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stmt_lines as S
sys.stdout.reconfigure(encoding="utf-8")
fy = sys.argv[1]
path = S.main_xml(fy)
tabs, titles = S.parse_tables(str(path))
s, e = S.sep_range(titles)
print(path.name, s, e)
for t in tabs:
    if s < t["start"] < e:
        labels = [r[1][0] for r in t["rows"][:5] if r[1]]
        print(f"L{t['start']}-{t['end']} rows={len(t['rows'])} cap={t['caption'][:40]!r} first={labels}")
