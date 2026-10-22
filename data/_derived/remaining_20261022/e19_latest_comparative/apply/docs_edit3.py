from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/TODO_parser_ifrs17.md")
raw = p.read_bytes(); crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")
old = "rule_coverage 102/104(실패 2 = xlsx 청결 1 + 새 22칸을 반영하도록 고친 tax22 테스트는 수정 후 통과)"
new = "rule_coverage 103/104(실패 1 = xlsx 청결; tax22 테스트는 교보 4칸 고정이라 실측 22칸으로 확장 후 통과)"
assert s.count(old) == 1
p.write_bytes((s.replace(old, new).replace("\n", "\r\n") if crlf else s.replace(old, new)).encode("utf-8"))
