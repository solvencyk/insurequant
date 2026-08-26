import re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
p = Path(sys.argv[1]); txt = p.read_text(encoding="utf-8", errors="replace")
flat = re.sub(r"<[^>]+>", " ", txt)
flat = re.sub(r"\s+", " ", flat)
for needle in sys.argv[2:]:
    print("=" * 100); print("NEEDLE", needle)
    for m in re.finditer(re.escape(needle), flat):
        a = max(0, m.start() - 500); b = min(len(flat), m.end() + 160)
        print("  ...", flat[a:b].strip(), "...")
        print("  " + "-" * 90)
