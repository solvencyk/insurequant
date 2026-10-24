# -*- coding: utf-8 -*-
"""the --update console log was captured in cp949; re-encode it to UTF-8 (no data change)."""
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/gates/master_tables_golden_update.txt")
b = p.read_bytes()
t = b.decode("cp949", errors="replace")
p.write_text(t, encoding="utf-8", newline="\n")
print("re-encoded", len(b), "->", len(t.encode("utf-8")), "replacement chars:", t.count("\ufffd"))
