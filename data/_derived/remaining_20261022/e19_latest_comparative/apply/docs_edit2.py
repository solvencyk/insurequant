from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/docs/changelog_parser_ifrs17.md")
raw = p.read_bytes(); crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")
a = s.index("- **효과**: 총포괄손익은")
b = s.index("\n", a)
new = ("- **효과(누계, 억원)**: 투자손익 −417.2~+585.8 · 당기순이익 −320.8~+450.5 · 기타포괄손익 −33.5~+320.8(총 19버킷, 버킷별 전후 표 `onscreen_eok.txt`). 보험금융손익 배분 변경 4사(NH농협손보·동양·ABL·푸본현대)와 DB생명은 순이익↔OCI 이동 또는 보험서비스↔투자영업비용 재분류라 총포괄손익 불변, "
       "오류 정정인 흥국화재(총포괄 +43.2/+78.6/−11.6/−24.5)와 농협생명(순이익 +450.5)만 총포괄손익이 움직인다. 인접 분기 단일분기도 같이 정리됐다(흥국 2024.3Q · NH·ABL·동양 2024.4Q · DB생명·농협생명 2023.4Q · 푸본현대 2024.3Q).")
s = s[:a] + new + s[b:]
p.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
