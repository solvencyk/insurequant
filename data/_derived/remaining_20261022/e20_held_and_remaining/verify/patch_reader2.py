# -*- coding: utf-8 -*-
from pathlib import Path
p = Path('C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/verify/vx_reader.py')
s = p.read_text(encoding='utf-8')
s = s.replace("        tt = RE_TAG.sub('', t)\n        if re.search(title_pat, tt)", "        tt = t if t.startswith('<!--') else RE_TAG.sub('', t)\n        if re.search(title_pat, tt)")
s = s.replace("cm = RE_CTX.search(attrs)\n                    vals.append((cm.group(1) if cm else None,", "cmx = RE_CTX.search(attrs)\n                    vals.append((cmx.group(1) if cmx else None,")
p.write_text(s, encoding='utf-8')
