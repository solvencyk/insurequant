import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DISC = ROOT / "data" / "disclosure"
MD_INBOX = ROOT / "md_inbox"

periods = sorted(p.name for p in DISC.iterdir() if p.is_dir() and p.name.startswith("FY"))
for period in periods:
    pdf_dir = DISC / period / "pdf"
    raw_dir = DISC / period / "raw"
    n_pdf = len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0
    n_pdf_zip = len(list(pdf_dir.glob("*.zip"))) if pdf_dir.exists() else 0
    n_raw = len(list(raw_dir.glob("*.pdf"))) if raw_dir.exists() else 0
    md_dir = MD_INBOX / period
    n_md = len(list(md_dir.glob("*.md"))) if md_dir.exists() else 0
    print(f"{period}: pdf/={n_pdf} (+{n_pdf_zip} zip)  raw/={n_raw}  md_inbox={n_md}")
