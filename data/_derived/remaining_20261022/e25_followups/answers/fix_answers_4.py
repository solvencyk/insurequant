# -*- coding: utf-8 -*-
from pathlib import Path
bad = '""" + "게이트·테스트 결과는'
good = '**게이트·테스트**: 결과는'
for p in (Path("kr0003_lotte_csm.md"), Path("C:/Users/sangwook.cho/Desktop/insurequant/inbox/parser/20261023T1215Z__validation__KR0099-KR0003__2023.4Q__single_quarter_vintage_seam_not_blanked.md")):
    s = p.read_text(encoding="utf-8")
    assert s.count(bad) == 1, p
    s = s.replace(bad, good)
    p.write_bytes(s.encode("utf-8"))
    print("fixed", p.name)
