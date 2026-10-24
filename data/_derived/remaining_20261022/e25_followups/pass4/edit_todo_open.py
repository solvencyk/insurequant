# -*- coding: utf-8 -*-
"""TODO_parser_ifrs17.md: replace the '24차 후속' open item (lines ①-④) by the '25차 후속' item (24차 ② ③ are done by this load)."""
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/TODO_parser_ifrs17.md")
raw = p.read_bytes()
crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")
a = s.index("- [ ] **24차 후속(이웃 옛 판 칸 점검 3차 뒤)")
b = s.index("- [ ] **21차 후속(D1~D3 4사 적재 뒤)")
new = """- [ ] **25차 후속(동양 재보험 블록 · NH농협손보 2023 블록 마무리 뒤): owner 결정 2 · publishing** — 적재 완료·미커밋, 답변은 티켓 `20261024T1000Z`(answered), 근거 `data/_derived/remaining_20261022/e25_followups/pass4/answer_ticket.md`. (24차 후속 ② 동양 2024.1Q·3Q 항목 11 비움 · ③ NH농협손보 2023 항목 1·16~21·19 는 25차에서 처리했다.)
  - ① 결정: 동양 재보험 항목 9·10 부호 규약. 지금 생산 정의 −|값|(2024.1Q~3Q 9 = −1,936 / −2,528 / −3,079, 10 = −425 / −824 / −1,180; 2025.2Q~2026.2Q 마스터도 같은 방식)이고, owner 손입력 gold(2024.4Q −1,711 / +1,559 = FY2024 사업보고서 별도 L54016·L54027 인쇄 +1,711 / (1,559)의 부호를 뒤집은 값, 2025.1Q +461 / +295 = 인쇄 (461) / (295)를 뒤집은 값)는 순자산(부채) 관점 인쇄의 반대 부호다. 인쇄(순자산(부채) 관점)는 RA 가 전 분기 음수, CSM 은 2024 에 + · 2025 에 − 로 방향이 바뀐다. 어느 쪽으로 통일하느냐에 따라 2024.1Q~3Q 항목 10 · 2025.2Q·3Q 항목 9·10 · 2024.2Q 9·12 가 움직인다(합 동일).
  - ② 결정: 동양 2024.4Q owner gold 9·10(−1,711 / +1,559, 연간 원본)이 FY2025 분기 전기 열 3Q 누계(−3,079 / −1,180)와 공시 판·부호 규약이 달라 4Q 단일분기를 null_dangi 로 비웠다. 4Q 항목 11(5,758 = 항목 8, owner gold 12 가 이를 끼고 닫힘) · 2025.1Q gold 11(3,361)·12 와 같이 재검토. FY2025 사업보고서의 2024 비교열 롤포워드는 행 이름을 못 찾아 읽지 못했다(`pass4/kr0087_dongyang/d28_*`).
  - ③ publishing: xlsx `손익분해PL` 389칸 · `CSM워터폴` 3칸 동기화, panel, public_exports.
"""
s = s[:a] + new + s[b:]
p.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
print("TODO open item replaced; crlf =", crlf)
