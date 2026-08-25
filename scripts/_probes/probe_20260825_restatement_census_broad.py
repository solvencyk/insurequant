# -*- coding: utf-8 -*-
"""'같은 병'(소급재작성으로 FY 경계가 안 닫힘) **전수 census 재검** (validation iter4).

parser iter3 은 raw 를 `"소급 재작성으로 재무상태표에 미치는 영향"` **한 문구**로 검색해
2개사(하나생명·푸본현대)만 매칭됐다고 보고했다. 이 저장소는 고정밀 문구 매칭으로 변형
라벨을 놓친 전례가 반복돼 있어, 두 방향으로 다시 잰다.

  A. **키워드 축 — 넓힌다.** 재작성/소급/오류수정/회계정책변경 계열 라벨 변형 다수로 전수 grep.
  B. **키워드 없는 축(이쪽이 본선).** 라벨을 아예 안 쓴다 — 마스터의 FY 경계 자체가 이 병의
     직접 탐지기다. 빌더가 각 filing 의 <당기> 표를 쓰므로, 후속 filing 이 전기를 재작성하면
     그 filing 의 기초가 직전 filing 의 기말과 갈라진다 = 경계 break. 게이트 tol 을 무시하고
     **모든 경계의 잔차 분포**를 인쇄해 tol 밑에 숨은 것이 있는지 본다.

read-only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

TAG = re.compile(r"<[^>]+>")

# 라벨 변형 — 좁은 문구 하나가 아니라 계열 전체
PATTERNS = {
    "재무제표 재작성(제목형)": r"재무제표\s*(?:의\s*)?재작성",
    "재작성(일반)": r"재작성",
    "소급적용": r"소급\s*적용",
    "소급하여 수정/재작성": r"소급하여",
    "전기오류수정": r"전기\s*오류\s*수정|오류\s*수정",
    "회계정책의 변경": r"회계정책\s*(?:의\s*)?변경",
    "수정후/수정전 대조표": r"수정\s*후|수정\s*전",
    "비교표시 재작성": r"비교\s*표시.{0,20}재작성|재작성.{0,20}비교\s*표시",
    "K-IFRS 1008": r"1008\s*호|기업회계기준서\s*제?\s*1008",
}
# 실제 '영향표' 를 든 filing 만 좁히는 2차 조건
QUANT = r"수정\s*후|수정\s*전|재작성\s*후|재작성\s*전|미치는\s*영향"

print("=" * 100)
print("A. 키워드 축 — 라벨 변형을 넓혀 전수 grep")
print("=" * 100)
files = sorted(ROOT.glob("data/dart/FY*/raw/*/*.xml"))
print(f"  대상 XML: {len(files)}개")
hits: dict = {}
for p in files:
    try:
        s = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    flat = re.sub(r"\s+", " ", TAG.sub(" ", s))
    got = {name: len(re.findall(pat, flat)) for name, pat in PATTERNS.items()}
    got = {k: v for k, v in got.items() if v}
    if not got:
        continue
    parts = p.parts
    fy = next((x for x in parts if x.startswith("FY")), "?")
    co = p.parent.name.split("_")[1] if "_" in p.parent.name else p.parent.name
    code = p.parent.name.split("_")[0]
    quant = bool(re.search(QUANT, flat))
    hits.setdefault((code, co), []).append((fy, got, quant))

strong, weak = [], []
for (code, co), rows in sorted(hits.items()):
    for fy, got, quant in rows:
        # '영향표를 든 진짜 재작성' 후보 = 재작성/소급/오류수정 계열 + 수정전후 대조 어휘
        core = sum(got.get(k, 0) for k in
                   ("재무제표 재작성(제목형)", "전기오류수정", "소급하여 수정/재작성"))
        if core and quant:
            strong.append((code, co, fy, got))
        elif got.get("재작성") or got.get("회계정책의 변경"):
            weak.append((code, co, fy, got))

print(f"\n  [강한 후보] 재작성/오류수정 계열 + 수정전후 대조 어휘 동반 : {len(strong)}건")
for code, co, fy, got in strong:
    print(f"     {code} {co:<14} {fy}  {got}")
print(f"\n  [약한 후보] '재작성' 또는 '회계정책의 변경' 만 등장 : {len(weak)}건 "
      f"(대부분 주석 제목·보일러플레이트)")
seen = set()
for code, co, fy, got in weak:
    if (code, co) in seen:
        continue
    seen.add((code, co))
    print(f"     {code} {co:<14} {fy}  {got}")

print()
print("=" * 100)
print("B. 키워드 없는 축 — 마스터 FY 경계 잔차 전수 분포 (본선)")
print("=" * 100)
recs = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
recs = recs["records"] if isinstance(recs, dict) else recs
wf: dict = {}
for r in recs:
    co, q = r.get("원수사명"), r.get("공시분기")
    if co is None or q is None:
        continue
    wf.setdefault((co, q), {})[str(r.get("항목명") or "").replace(" ", "")] = r.get("값")
by_co: dict = {}
for (co, q), m in wf.items():
    by_co.setdefault(co, {})[q] = m

rows = []
for co, qmap in by_co.items():
    for q in qmap:
        try:
            fy = int(str(q)[:4])
        except ValueError:
            continue
        prev = qmap.get(f"{fy - 1}.4Q")
        if prev is None:
            continue
        pc, op = prev.get("기말CSM"), (qmap.get(q) or {}).get("기초CSM")
        if pc is None or op is None:
            continue
        rows.append((abs(op - pc), co, q, pc, op, op - pc))
rows.sort(reverse=True)
print(f"  평가된 경계: {len(rows)}")
print(f"  게이트 tol = max(0.5% * |직전기말|, 2.0억)")
print("\n  [잔차 큰 순 상위 15]")
for a, co, q, pc, op, gap in rows[:15]:
    tol = max(0.005 * abs(pc), 2.0)
    mark = "  <-- tol 초과(RED/면제)" if a > tol else ""
    rel = (a / abs(pc) * 100) if pc else 0.0
    print(f"     {co:<16} {q}  {pc:>10,.1f} -> {op:>10,.1f}  Δ{gap:>+9,.1f} "
          f"({rel:5.2f}%)  tol={tol:,.1f}{mark}")
exact = sum(1 for a, *_ in rows if a == 0.0)
sub = [r for r in rows if 0.0 < r[0] <= max(0.005 * abs(r[3]), 2.0)]
print(f"\n  잔차 정확히 0        : {exact} / {len(rows)}")
print(f"  0 < 잔차 <= tol      : {len(sub)}  <-- tol 밑에 숨은 불일치")
for a, co, q, pc, op, gap in sorted(sub, reverse=True)[:15]:
    print(f"     {co:<16} {q}  Δ{gap:+,.2f}")
