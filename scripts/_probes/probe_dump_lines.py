import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq

code = sys.argv[1]
period = sys.argv[2] if len(sys.argv) > 2 else "FY2026_Q2"
lo = int(sys.argv[3]) if len(sys.argv) > 3 else 0
hi = int(sys.argv[4]) if len(sys.argv) > 4 else 999

pdf_path = aq.find_pdf(period, code)
if pdf_path:
    lines, p_start, p_end, total_chars = aq._pdf_window_text(pdf_path)
    print(f"PDF path={pdf_path} window p{p_start}-{p_end} total_chars={total_chars}")
else:
    lines = None
    print("no pdf")

if not lines:
    md_path = aq.find_md(period, code)
    lines = aq._md_window_lines(md_path)
    print(f"MD fallback path={md_path}")

lines = aq._normalize_aliases(aq._merge_fragments(lines))
print(f"{len(lines)} lines total\n")
for idx, l in enumerate(lines):
    if lo <= idx <= hi:
        print(f"{idx:3d}: {l!r}")
