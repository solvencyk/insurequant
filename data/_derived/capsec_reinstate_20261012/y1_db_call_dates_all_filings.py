# -*- coding: utf-8 -*-
"""Audit-follow-up (ticket 20261012T2235Z req 1): list every DB손해보험 hybrid call-date sentence in every filing on disk."""
import re, glob, os, io, zipfile, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "data/dart"
pat = re.compile(r"(제\s*\d+\s*회\s*(?:공모|사모)?\s*신종자본증권).{0,400}?발행일로부터 5년이 경과된\s*(\d{4}년\s*\d+월\s*\d+일)", re.S)
pat2 = re.compile(r"발행일\s*(\d{4}년\s*\d+월\s*\d+일).{0,80}?(?:발행금액\s*([\d,]+)백만원)", re.S)
def texts(d):
    for p in glob.glob(os.path.join(d, "**", "*.xml"), recursive=True):
        if os.path.getsize(p) > 3_000_000:
            yield p, open(p, encoding="utf-8", errors="replace").read()
    for z in glob.glob(os.path.join(d, "*.zip")):
        try:
            zf = zipfile.ZipFile(z)
        except Exception as e:
            continue
        for n in zf.namelist():
            if n.endswith(".xml"):
                b = zf.read(n)
                if len(b) > 3_000_000:
                    yield z + "!" + n, b.decode("utf-8", "replace")
seen = set()
for d in sorted(glob.glob(os.path.join(ROOT, "FY20*", "raw", "KR0011*"))):
    for src, t in texts(d):
        t2 = re.sub(r"<[^>]+>", " ", t)
        t2 = re.sub(r"&nbsp;", " ", t2)
        t2 = re.sub(r"\s+", " ", t2)
        for m in re.finditer(r"(구분\s*제\s*(\d)\s*회\s*(공모|사모)?\s*신종자본증권\s*발행일\s*(\d{4}년\s*\d+월\s*\d+일)).{0,900}?발행일로부터 5년이 경과된\s*(\d{4}년\s*\d+월\s*\d+일)", t2):
            key = (d.split(os.sep)[-3], m.group(2), m.group(4), m.group(5))
            if key in seen: continue
            seen.add(key)
            print(f"{key[0]} {os.path.basename(src)[:40]} | 제{m.group(2)}회 issue {m.group(4)} -> call {m.group(5)}")
