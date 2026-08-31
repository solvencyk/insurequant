"""For each of the 16 target patch files, list which 항목번호 (item numbers) are already present,
so we know what's free to add without creating duplicate cell entries within the same patch file."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

CODES = ["KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0080", "KR0082", "KR0083",
         "KR0087", "KR0094", "KR0097", "KR0099", "KR0100", "KR0104", "KR1010", "KR1011"]

for code in CODES:
    f = ROOT / "data" / "_derived" / f"_patch_2026q2_{code}.json"
    if not f.exists():
        print(f"{code}: NO FILE")
        continue
    data = json.loads(f.read_text(encoding="utf-8"))
    items = sorted(c.get("항목번호") for c in data.get("cells", []))
    has_post = [c.get("항목번호") for c in data.get("cells", []) if "값_적용후" in c]
    print(f"{code}: items={items}")
    print(f"        with 값_적용후 key={sorted(has_post)}")
