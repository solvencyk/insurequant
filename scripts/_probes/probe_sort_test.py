import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz

code_path = sys.argv[1]
page_no = int(sys.argv[2])  # 1-indexed

doc = fitz.open(code_path)
page = doc[page_no - 1]
text_sorted = page.get_text(sort=True)
print("=== sort=True ===")
print(text_sorted[:3000])
doc.close()
