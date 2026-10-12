"""b3_show_page.py PDF PAGE [KEYWORD ...] -- print table rows of one PDF page (READ-ONLY).
With keywords: only rows containing a keyword plus 1 row before/after.  Without: all rows."""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from pdfcheck import rows_of_page, row_text, utf8_stdout  # noqa: E402

utf8_stdout()
pdf, page = sys.argv[1], int(sys.argv[2])
kws = sys.argv[3:]
rows = rows_of_page(pdf, page)
print(f"{pdf.split('/')[-1]} p{page}: {len(rows)} rows")
if not kws:
    for r in rows:
        print(f"y{r[0]:>6}: {row_text(r)[:220]}")
else:
    keep = set()
    for i, r in enumerate(rows):
        if any(k in row_text(r) for k in kws):
            keep.update({i - 1, i, i + 1})
    for i, r in enumerate(rows):
        if i in keep:
            print(f"y{r[0]:>6}: {row_text(r)[:220]}")
