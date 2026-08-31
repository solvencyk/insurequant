import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq

code = sys.argv[1]
period = sys.argv[2]

pdf_path = aq.find_pdf(period, code)
print("pdf_path:", pdf_path)
t31, t32, pinfo, total_chars = aq._pdf_window_text(pdf_path)
print("page_info:", pinfo, "total_chars:", total_chars)
if t32 is None:
    print("t32 is None -- trying MD fallback")
    md_path = aq.find_md(period, code)
    print("md_path:", md_path)
    if md_path:
        m31, m32 = aq._md_window_lines(md_path)
        t32 = m32
        print("md m32 len:", len(m32) if m32 else None)

if t32:
    lines = aq._normalize_aliases(aq._merge_fragments(aq._dedupe_doubled_lines(t32)))
    print(f"{len(lines)} lines")
    for idx, l in enumerate(lines):
        print(f"{idx:3d}: {l!r}")
    vals32, status32, detail32, extra32 = aq._parse_32_lines(lines)
    print("\nstatus32:", status32, detail32)
