# -*- coding: utf-8 -*-
"""TODO_parser_ifrs17.md: shorten the 25차 후속 item ① line below the 1,200-byte doc_rotate limit."""
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/TODO_parser_ifrs17.md")
raw = p.read_bytes()
crlf = b"\r\n" in raw
lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
idx = [i for i, l in enumerate(lines) if l.startswith("  - ① 결정: 동양 재보험 항목 9·10 부호 규약.")]
assert len(idx) == 1, idx
lines[idx[0]] = ("  - ① 결정: 동양 재보험 항목 9·10 부호 규약. 지금은 생산 정의 −|값|(2024.1Q~3Q 9 = −1,936 / −2,528 / −3,079 · 10 = −425 / −824 / −1,180; 2025.2Q 이후 마스터도 같음)이고, "
                 "owner 손입력 gold(2024.4Q −1,711 / +1,559 · 2025.1Q +461 / +295)는 순자산(부채) 관점 인쇄 부호를 뒤집은 값이다(FY2024 사업보고서 별도 L54016·L54027 인쇄 +1,711 / (1,559)). "
                 "인쇄는 RA 가 전 분기 음수, CSM 이 2024 에 + · 2025 에 − 로 방향이 바뀐다. 통일 방향에 따라 2024.1Q~3Q 항목 10 · 2025.2Q·3Q 항목 9·10 · 2024.2Q 9·12 가 움직인다(합 동일).")
out = "\n".join(lines)
p.write_bytes((out.replace("\n", "\r\n") if crlf else out).encode("utf-8"))
print("shortened; bytes of the line:", len(lines[idx[0]].encode("utf-8")))
