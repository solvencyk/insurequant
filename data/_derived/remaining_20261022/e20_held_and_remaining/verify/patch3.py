# -*- coding: utf-8 -*-
from pathlib import Path
p = Path('C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/verify/v3_check_cum.py')
s = p.read_text(encoding='utf-8')
s = s.replace("""def norm(l):
    l = STRIP.sub('', l.replace(' ', ''))
    return STRIP.sub('', l)""", """def norm(l):
    l = re.sub(r'\([^)]*\)', '', l.replace(' ', ''))
    l = STRIP.sub('', l)
    return STRIP.sub('', l)""")
s = s.replace("25: r'^(총)?기타포괄(손익|이익)$'", "25: r'^(법인세비용차감후|당기)?(총)?기타포괄(손익|이익)$'")
s = s.replace("31: r'^(분기|반기|당기)?총포괄(손익|이익)$'", "31: r'^(분기|반기|당기)?총포괄(손익|이익)$'")
p.write_text(s, encoding='utf-8')
