import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq

code = sys.argv[1] if len(sys.argv) > 1 else "KR0010"
period = sys.argv[2] if len(sys.argv) > 2 else "FY2026_Q2"

md_path = aq.find_md(period, code)
print("md_path:", md_path)
lines = aq._md_window_lines(md_path)
print(f"{len(lines)} flattened lines")
for idx, l in enumerate(lines):
    print(f"{idx:3d}: {l!r}  [compact={aq._compact(l)!r}]")

merged = aq._merge_fragments(lines)
print(f"\nafter merge: {len(merged)} lines")

vals32, status32, detail32 = aq._parse_32_lines(merged)
print("\nstatus32:", status32, detail32)
print("vals32 keys:", sorted(vals32.keys()))
