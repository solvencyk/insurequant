# -*- coding: utf-8 -*-
"""Write the answer into the ticket's '## 답변' section and set status: answered (the ticket stays in inbox/parser/, not moved to _resolved)."""
import io
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
t = f"{ROOT}/inbox/parser/20261024T1000Z__orchestrator__KR0087-KR0032__2023.1Q-2024.4Q__complete_blocks_dongyang_nhfire.md"
raw = io.open(t, encoding="utf-8", newline="").read()
crlf = "\r\n" in raw
s = raw.replace("\r\n", "\n")
ans = io.open(f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass4/answer_ticket.md", encoding="utf-8").read().replace("\r\n", "\n").strip("\n")
assert s.count("\nstatus: open\n") == 1
s = s.replace("\nstatus: open\n", "\nstatus: answered\n")
mark = "## 답변 (recipient 작성 — 처리 후)"
assert s.count(mark) == 1
head = s[: s.index(mark) + len(mark)]
out = head + "\n\n" + ans + "\n"
if crlf:
    out = out.replace("\n", "\r\n")
io.open(t, "w", encoding="utf-8", newline="").write(out)
print("ticket filled; crlf =", crlf, "chars", len(out))
