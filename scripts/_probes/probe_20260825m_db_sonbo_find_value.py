# -*- coding: utf-8 -*-
"""DB손해보험(KR0011) 2023.2Q raw 에서 현재 item1(971,297.908122) 이 실제로 어느 라벨
행에서 왔는지 숫자로 역추적한다 (read-only)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

d = ROOT / "data/dart/FY2023_Q2/raw/KR0011_DB손해보험"
targets = ["971,297", "971,298", "971297", "758,440", "978,167"]
for x in sorted(d.glob("*.xml")):
    raw = x.read_bytes()
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        t = raw.decode("cp949", errors="replace")
    t2 = re.sub(r"<[^>]+>", " ", t)
    t2 = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", t2)
    t2 = re.sub(r"\s+", " ", t2)
    for tgt in targets:
        for m in re.finditer(re.escape(tgt), t2):
            ctx = t2[max(0, m.start() - 150): m.start() + 50]
            print(f"[{tgt}] @{m.start()}: ...{ctx}...")
            print()

print("="*80)
print("WIDER CONTEXT around 보험서비스결과")
for x in sorted(d.glob("*.xml")):
    raw = x.read_bytes()
    try:
        t = raw.decode("utf-8")
    except UnicodeDecodeError:
        t = raw.decode("cp949", errors="replace")
    t2 = re.sub(r"<[^>]+>", " ", t)
    t2 = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", t2)
    t2 = re.sub(r"\s+", " ", t2)
    for m in re.finditer(r"보험서비스결과", t2):
        print(f"@{m.start()}:")
        print(t2[max(0, m.start()-900):m.start()+700])
        print()
