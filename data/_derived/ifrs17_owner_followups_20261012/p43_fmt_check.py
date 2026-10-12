# -*- coding: utf-8 -*-
import sys
for p in ("TODO_parser_ifrs17.md", "docs/todo_archive_parser_ifrs17.md", "docs/changelog_parser_ifrs17.md"):
    b = open("C:/Users/sangwook.cho/Desktop/insurequant/" + p, "rb").read()
    print(p, len(b), "CRLF" if b"\r\n" in b else "LF", "BOM" if b[:3] == b"\xef\xbb\xbf" else "noBOM", "endsNL" if b.endswith(b"\n") else "noEndNL")
