# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/b01_backup_preload.py")
s = p.read_text(encoding="utf-8")
old = "inbox/parser/20261024T0600Z__orchestrator__MULTI__2023.2Q-2026.2Q__neighbor_stale_cells_pass4_abl_dongyang_nhfire.md"
new = "inbox/parser/20261024T1000Z__orchestrator__KR0087-KR0032__2023.1Q-2024.4Q__complete_blocks_dongyang_nhfire.md\ndocs/todo_archive_parser_ifrs17.md"
assert s.count(old) == 1
p.write_text(s.replace(old, new), encoding="utf-8", newline="\n")
print("fixed")
