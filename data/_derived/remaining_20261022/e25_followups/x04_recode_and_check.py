# -*- coding: utf-8 -*-
"""(1) Recode the console-captured pytest outputs (cp949 bytes from the Windows console) to UTF-8, content unchanged.  (2) Show that the U+FFFD in docs/todo_archive_parser_ifrs17.md pre-dates this batch (backup copy)."""
from pathlib import Path
EV = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups")
for rel in ("gates/master_tables_golden_update.txt", "gates/tests_all1/test_master_tables_golden.txt", "gates/tests_all1/test_rule_coverage_manifest.txt", "gates/tests_final/test_rule_coverage_manifest.txt",
            "gates/tests_t1_4/test_master_tables_golden.txt", "gates/tests_t1_4/test_rule_coverage_manifest.txt"):
    p = EV / rel
    b = p.read_bytes()
    try:
        b.decode("utf-8")
        print("already UTF-8:", rel)
        continue
    except UnicodeDecodeError:
        pass
    t = b.decode("cp949", errors="replace")
    p.write_bytes(t.replace("\r\n", "\n").encode("utf-8"))
    print("recoded cp949 -> utf-8:", rel, "replacement chars:", t.count("\ufffd"))
old = (EV / "backup_before_apply/docs/todo_archive_parser_ifrs17.md").read_bytes().decode("utf-8")
new = Path("C:/Users/sangwook.cho/Desktop/insurequant/docs/todo_archive_parser_ifrs17.md").read_bytes().decode("utf-8")
print("U+FFFD count in the archive BEFORE the rotation:", old.count("\ufffd"), "| after:", new.count("\ufffd"))
