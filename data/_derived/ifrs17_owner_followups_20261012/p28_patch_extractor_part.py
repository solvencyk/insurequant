# -*- coding: utf-8 -*-
p = "C:/Users/sangwook.cho/Desktop/insurequant/scripts/extract_chubb_d2_20261012.py"
s = open(p, encoding="utf-8", newline="").read()
a = '            part = "KR0100_agent_gran.json" if q == "2023.1Q" else "KR0100_agent_followup.json"\n'
assert s.count(a) == 1
s = s.replace(a, '''            # 2023.1Q lives in KR0100_agent_gran.json (other_agent class; sorted AFTER KR0100_agent_followup.json in merge_bs_disclosure_parts.py, so it must be updated
            # where it is held); the other five keys are held only by the engine part KR0100.json -> the default part KR0100_agent_followup.json (other_agent class)
            # outranks the engine part and an engine re-run cannot bring the general-account value back
''')
b = '                method="d2_general_account_plus_special_account", scale="원 -> 백만원", part_file=part,\n'
assert s.count(b) == 1
s = s.replace(b, '                method="d2_general_account_plus_special_account", scale="원 -> 백만원",\n')
c = '''            bs_cells.append(dict(
                key=f"{CODE}|20|{q}", action="replace", old=old20, new=new20, pdf="data/disclosure/" + rel, page=d1_pages[0], pdf_sha256=sha_file(p),'''
assert s.count(c) == 1
s = s.replace(c, c)
d = "                       f\"보험계약부채는 특별계정 변액 \"\n"
open(p, "w", encoding="utf-8", newline="").write(s)
print("patched")
