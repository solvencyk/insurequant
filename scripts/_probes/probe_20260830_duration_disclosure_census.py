# -*- coding: utf-8 -*-
"""듀레이션 census 2차 — 태그를 벗기고 본다.

1차는 `듀레이션[^<]{0,80}(\\d+\\.\\d+)` 로 찾아 0사가 나왔는데, DART 표는 라벨과 값이 서로
다른 `<TD>` 에 있어 `[^<]` 가 태그 경계를 못 넘는다. **탐지기 결함이지 원천 부재가 아니다**
(이 저장소가 두 번 데인 함정 — "키워드 0회 = 원문 없음" 결론 금지).
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(".")
DART = ROOT / "data" / "dart"
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
# 태그를 ' | ' 로 바꾼 뒤: 듀레이션 라벨 근처의 '년' 단위 실수
DUR_NEAR = re.compile(r"듀레이션.{0,120}?(\d{1,2}\.\d{1,2})")


def latest_annual(frag):
    c = [(p.parts[-3], p) for p in DART.glob("FY*_Q4/raw/*")
         if frag in p.name and list(p.rglob("*.xml"))]
    c.sort(reverse=True)
    return c[0] if c else (None, None)


def flat(d):
    t = ""
    for p in sorted(d.rglob("*.xml"), key=lambda x: x.stat().st_size, reverse=True)[:2]:
        t += p.read_text(encoding="utf-8", errors="replace")
    return WS.sub(" ", TAG.sub(" | ", t))


rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
companies = {}
for r in rows:
    companies.setdefault(r["원보험사코드"], r["원수사명"])

have_num, no_num, samples = [], [], {}
for code in sorted(companies):
    name = companies[code]
    fy, d = latest_annual(code + "_")
    if d is None:
        continue
    txt = flat(d)
    nums = DUR_NEAR.findall(txt)
    if nums:
        have_num.append(name)
        # 첫 3개 문맥
        ctx = []
        for m in list(re.finditer(r"듀레이션", txt))[:60]:
            seg = txt[m.start() - 60:m.start() + 160]
            if re.search(r"\d{1,2}\.\d{1,2}", seg):
                ctx.append(seg.strip())
            if len(ctx) >= 2:
                break
        samples[name] = ctx
    elif "듀레이션" in txt:
        no_num.append(name)

print(f"듀레이션 숫자 동반: {len(have_num)}사")
print(f"듀레이션 언급만(숫자 없음): {len(no_num)}사 -> {no_num}")
print("\n[문맥 표본]")
for n in list(samples)[:12]:
    print(f"\n### {n}")
    for c in samples[n]:
        print("   ", c[:230])
