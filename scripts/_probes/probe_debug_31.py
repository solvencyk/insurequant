import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
from extract_asset_quality import find_pdf, _pdf_window_text, _parse_31_lines, _compact

code = sys.argv[1] if len(sys.argv) > 1 else "KR0011"
period = sys.argv[2] if len(sys.argv) > 2 else "FY2026_Q2"

pdf_path = find_pdf(period, code)
print("pdf_path:", pdf_path)
lines, p_start, p_end, total_chars = _pdf_window_text(pdf_path)
print(f"window p{p_start}-{p_end}, {len(lines)} lines")
for idx, l in enumerate(lines[:60]):
    print(f"{idx:3d}: {l!r}  [compact={_compact(l)!r}]")

vals, ev = _parse_31_lines(lines)
print("\nvals:", vals)
print("evidence:", ev)
