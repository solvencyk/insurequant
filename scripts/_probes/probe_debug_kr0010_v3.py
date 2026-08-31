import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq

md_path = aq.find_md("FY2026_Q2", "KR0010")
raw_lines = aq._md_window_lines(md_path)
print(f"raw flattened: {len(raw_lines)}")
lines = aq._normalize_aliases(aq._merge_fragments(raw_lines))
print(f"after merge+alias: {len(lines)}")
for idx, l in enumerate(lines):
    print(f"{idx:3d}: {l!r}")

vals32, status32, detail32 = aq._parse_32_lines(lines)
print("\nstatus32:", status32, detail32)
