# -*- coding: utf-8 -*-
import io
p = "C:/Users/sangwook.cho/Desktop/insurequant/TODO_parser_ifrs17.md"
s = io.open(p, encoding="utf-8", newline="").read()
old = "박제·핀·잔차·예외 0 (티켓 `20261024T0300Z`, 미커밋)** — ABL 35("
new = "박제·핀·잔차·예외 0 (티켓 `20261024T0300Z`, 미커밋)**\n  ABL 35("
assert s.count(old) == 1
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("split")
