# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("KR0104_gate_bridge.py")
s = p.read_text(encoding="utf-8")
s = s.replace('pl_old.setdefault(key, {})[r["항목명"]] = r["값"]', 'pl_old.setdefault(key, {})[r["항목명"].replace(" ", "")] = r["값"]')
s = s.replace('pl_new.setdefault(key, {})[r["항목명"]] =', 'pl_new.setdefault(key, {})[r["항목명"].replace(" ", "")] =')
p.write_text(s, encoding="utf-8", newline="\n")
