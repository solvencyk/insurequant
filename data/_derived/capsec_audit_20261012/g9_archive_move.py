# -*- coding: utf-8 -*-
"""g9: move the third Status entry of TODO_validation.md (the 2 lines starting '- **2026-10-12 재보사 PL 계보 허용') verbatim to the top of docs/todo_archive_validation.md
(under its title), then insert the new 27th-round Status entry at the top of the Status list.  Byte-exact for the moved text; newline style preserved."""
import re

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
tp, ap = ROOT + "TODO_validation.md", ROOT + "docs/todo_archive_validation.md"
with open(tp, "rb") as f:
    traw = f.read()
with open(ap, "rb") as f:
    araw = f.read()
nl = b"\r\n" if b"\r\n" in traw[:4000] else b"\n"
anl = b"\r\n" if b"\r\n" in araw[:4000] else b"\n"
print("TODO newline", nl, "archive newline", anl, "BOM TODO", traw[:3] == b"\xef\xbb\xbf", "BOM archive", araw[:3] == b"\xef\xbb\xbf")
tl = traw.split(nl)
# locate the entry to move
idx = [i for i, l in enumerate(tl) if l.decode("utf-8").startswith("- **2026-10-12 재보사 PL 계보 허용 + 마감 골든 3종")]
assert len(idx) == 1, idx
i = idx[0]
block = [tl[i], tl[i + 1]]
assert tl[i + 2] == b"" and tl[i + 1].decode("utf-8").startswith("  변이시험 pytest 14건"), tl[i + 1][:60]
print("moving lines", i + 1, "-", i + 2)
# 1) archive: insert under the title
al = araw.split(anl)
assert al[0].decode("utf-8").startswith("# TODO archive"), al[0]
head = al[0:2]            # title + blank
rest = al[2:]
section = [("## 2026-10-12 Status 밀림 (27차 독립 감사 항목 추가로 밀려난 항목, 무수정)").encode("utf-8"), b""] + block + [b""]
new_a = anl.join(head + section + rest)
# 2) TODO: remove the block (the 2 lines) - keep the blank line that follows
del tl[i:i + 2]
new_t = nl.join(tl)
with open(ap, "wb") as f:
    f.write(new_a)
with open(tp, "wb") as f:
    f.write(new_t)
print("done")
