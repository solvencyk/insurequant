"""Read-only: byte length of every line (doc_rotate.py --check flags a TODO line over 1200 BYTES) -- usage: linelen.py <file> [<file> ...]  (prints lines over 1000 bytes)"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
for f in sys.argv[1:]:
    data = Path(f).read_bytes().split(b"\n")
    print(f"== {f}: {len(data)} lines, longest {max(len(x) for x in data)} bytes")
    for i, ln in enumerate(data, 1):
        if len(ln) > 1000:
            print(f"   L{i}: {len(ln)} bytes | {ln[:70].decode('utf-8', 'replace')}")
