# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("docs/changelog_publishing.md")
t = p.read_text(encoding="utf-8")
i = t.index("(a) census 최종본")
j = t.index("(b) 하나생명·교보는")
new = ("(a) census 최종본 `census_securities_final.csv`(20:02 생성, 작업 중간에 도착)를 등재부와 대조했다(`vs_final_census.txt`): 43건 중 같음 37, "
       "「다름」 6건은 전부 이 라운드 이전 등재부 기준이고 최종본 type 이 지금 등재부(tier2)와 일치한다 - 교보 2024-11(스텝업, 발행사 표 상충 병기)·"
       "푸본 600·하나생명 제1회·농협생명 제5회·코리안리 제5/6회. DB손보 5건 tier1·하나손해 2건 tier2 도 최종본과 같아 등재부 추가 변경 없음. ")
p.write_text(t[:i] + new + t[j:], encoding="utf-8", newline="\n")
print("ok")
