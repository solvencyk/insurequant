# -*- coding: utf-8 -*-
from pathlib import Path
root = Path(__file__).resolve().parents[3]
td = root / "TODO_publishing.md"
s = td.read_text(encoding="utf-8")
start = s.index("- **2026-10-11 \uc7ac\ubcf4\uc0ac 8\uacf3(KR1101~1108) Forward Outlook")
end = s.index("\n\n## \uc5f4\ub9b0 \uc77c")
block = s[start:end].rstrip("\n")
s2 = s[:start].rstrip("\n") + "\n" + s[end:]
td.write_text(s2, encoding="utf-8")
ar = root / "docs/todo_archive_publishing.md"
a = ar.read_text(encoding="utf-8")
lines = a.split("\n")
# insert right after the first heading line (and following blank line)
i = 1
while i < len(lines) and lines[i].strip() == "":
    i += 1
# keep any blockquote header lines directly under the title
j = i
while j < len(lines) and lines[j].startswith(">"):
    j += 1
while j < len(lines) and lines[j].strip() == "":
    j += 1
lines[j:j] = [block, ""]
ar.write_text("\n".join(lines), encoding="utf-8")
print("moved", len(block))
