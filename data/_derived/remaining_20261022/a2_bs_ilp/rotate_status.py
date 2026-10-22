R = "C:/Users/sangwook.cho/Desktop/insurequant/"
tp = R + "TODO_parser_ifrs17.md"; ap = R + "docs/todo_archive_parser_ifrs17.md"
t = open(tp, "rb").read(); a = open(ap, "rb").read()
start = t.index("- **2026-10-22 14차:".encode("utf-8"))
end = t.index("\n## 열린 일".encode("utf-8"))
block = t[start:end]                                   # ends with "\n" of the last line? keep bytes as they are
block = block.rstrip(b"\n") + b"\n"
t2 = t[:start] + t[end:].lstrip(b"\n") if False else t[:start].rstrip(b"\n") + b"\n\n" + t[end:].lstrip(b"\n")
h = "## 2026-10-22 밀린 Status (최신 3개 밖, 문서 정리로 이동)\n\n".encode("utf-8")
i = a.index(h) + len(h)
a2 = a[:i] + block + a[i:]
assert block in a2 and block not in t2
open(tp, "wb").write(t2); open(ap, "wb").write(a2)
print("moved", len(block), "bytes")
