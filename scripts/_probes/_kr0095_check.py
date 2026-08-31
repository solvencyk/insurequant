# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

d = json.load(open("data/_derived/_patch_2026q2_KR0095.json", encoding="utf-8"))
for c in d["cells"]:
    if c["항목번호"] in (16,17,18,19,20,21,36,37):
        print(c["항목번호"], c["항목명"], "값=", c["값"], "값_적용후=", c["값_적용후"])
print()
print("notes snippet:", d.get("notes","")[:400])
