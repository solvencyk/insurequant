# -*- coding: utf-8 -*-
from pathlib import Path
p = Path('C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/verify/vx_reader.py')
s = p.read_text(encoding='utf-8')
s = s.replace("""    res = []
    for i,(pos, t) in enumerate(titles):""", """    res = []
    cm = [(m.start(), m.group(0)) for m in re.finditer(r'<!-- =====[^>]*===== -->', text)]
    if not titles or not any(re.search(title_pat, RE_TAG.sub('', t)) for _, t in titles):
        titles = cm
    for i,(pos, t) in enumerate(titles):""")
s = s.replace("RE_TE = re.compile(r'<T[EDH]([^>]*)>(.*?)</T[EDH]>', re.S)", "RE_TE = re.compile(r'<T[EDH]([^>]*)>(.*?)</T[EDH]>', re.S | re.I)")
s = s.replace("re.finditer(r'<TR[^>]*>(.*?)</TR>', seg, re.S)", "re.finditer(r'<TR[^>]*>(.*?)</TR>', seg, re.S | re.I)")
s = s.replace("RE_CTX = re.compile(r'ACONTEXT=\"([^\"]*)\"')", "RE_CTX = re.compile(r'ACONTEXT=\"([^\"]*)\"')")
p.write_text(s, encoding='utf-8')
