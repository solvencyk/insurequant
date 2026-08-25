# -*- coding: utf-8 -*-
"""`_CSM_CONTINUITY_EXCEPTIONS`(하나생명 2024.4Q) **변이시험** — 이빨이 있는가.

이 저장소의 다른 면제(`_TIER2_ISSUER_INCONSISTENT`)는 두 겹으로 박제돼 있고
`tests/test_tier2_issuer_inconsistent_exemption.py` 가 "박제를 흔들면 RED 가 돌아온다"를
증명한다. 새로 들어온 continuity 면제가 같은 잣대를 통과하는지 실측한다.

흔드는 것:
  M1  기초 CSM 을 크게 밀어 Δ 를 +73 -> +1073 으로 만든다        (기대: RED 복귀)
  M2  기초 CSM 을 결측으로 만든다                                (기대: 최소한 조용하지 않기)
  M3  경계가 닫히도록 되돌린다(Δ=0)                              (기대: 죽은 면제라고 알려주기)
  M4  같은 회사 **다른 분기**(2025.4Q)를 깨뜨린다                 (기대: RED — 스코프 확인)
  M5  **다른 회사**(라이나생명)를 같은 크기로 깨뜨린다            (기대: RED — 전염 없음)

read-only. 마스터를 디스크에 쓰지 않는다(메모리 사본만 변형).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_data_contract as gate  # noqa: E402


class FakeEnv:
    def __init__(self, wf):
        self.wf = wf


def load_wf() -> dict:
    """env.wf 와 같은 모양 — {(회사, 분기): {항목명(공백제거): 값}}."""
    recs = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
    recs = recs["records"] if isinstance(recs, dict) else recs
    wf: dict = {}
    for r in recs:
        co = r.get("원수사명")
        q = r.get("공시분기")
        item = str(r.get("항목명") or "").replace(" ", "")
        v = r.get("값")
        if co is None or q is None:
            continue
        wf.setdefault((co, q), {})[item] = v
    return wf


def run(wf) -> list:
    res = gate.GateResult()
    gate.check_csm_continuity(res, FakeEnv(wf))
    return res.findings


def show(tag: str, finds, focus=("하나생명보험", "라이나생명보험")) -> None:
    rows = [f for f in finds if f.company in focus]
    print(f"\n--- {tag} ---")
    if not rows:
        print("    (해당 회사 finding 없음 = 조용함)")
    for f in rows:
        print(f"    [{f.severity:6}] {f.company} {f.quarter} {f.rule}")
        print(f"             {str(f.message)[:150]}")
    tot = {"RED": 0, "YELLOW": 0}
    for f in finds:
        tot[f.severity] = tot.get(f.severity, 0) + 1
    print(f"    전체: RED={tot.get('RED', 0)} YELLOW={tot.get('YELLOW', 0)}")


BASE = load_wf()
print("=" * 100)
print("BASELINE (라이브 마스터)")
print("=" * 100)
b = run(BASE)
show("baseline", b)
print(f"\n등재 키: {list(gate._CSM_CONTINUITY_EXCEPTIONS)}")
print(f"하나생명 2023.4Q 기말={BASE[('하나생명보험','2023.4Q')]['기말CSM']} "
      f"/ 2024.4Q 기초={BASE[('하나생명보험','2024.4Q')]['기초CSM']}")

print()
print("=" * 100)
print("변이")
print("=" * 100)

# M1 — 등재 버킷의 기초를 +1000 밀기 (Δ +73 -> +1073)
m = copy.deepcopy(BASE)
m[("하나생명보험", "2024.4Q")]["기초CSM"] += 1000.0
show("M1  등재 버킷 기초 +1000억 (Δ가 등재 근거와 전혀 달라짐)", run(m))

# M2 — 등재 버킷의 기초 결측
m = copy.deepcopy(BASE)
m[("하나생명보험", "2024.4Q")]["기초CSM"] = None
show("M2  등재 버킷 기초 결측", run(m))

# M3 — 경계가 닫히도록 되돌리기 (Δ=0) -> 면제가 죽었는데 알려주나
m = copy.deepcopy(BASE)
m[("하나생명보험", "2024.4Q")]["기초CSM"] = m[("하나생명보험", "2023.4Q")]["기말CSM"]
show("M3  경계 복원(Δ=0) — 죽은 면제를 알려주나", run(m))

# M4 — 같은 회사 다른 분기
m = copy.deepcopy(BASE)
m[("하나생명보험", "2025.4Q")]["기초CSM"] += 500.0
show("M4  같은 회사 2025.4Q 파괴 (스코프 확인)", run(m))

# M5 — 다른 회사
other = None
for (co, q) in BASE:
    if co != "하나생명보험" and q == "2024.4Q" and (co, "2023.4Q") in BASE:
        if BASE[(co, q)].get("기초CSM") is not None and BASE[(co, "2023.4Q")].get("기말CSM") is not None:
            other = co
            break
m = copy.deepcopy(BASE)
m[(other, "2024.4Q")]["기초CSM"] += 5000.0
show(f"M5  다른 회사({other}) 2024.4Q 파괴 (전염 확인)", run(m), focus=(other,))

# M6 — 인용 마커를 깨뜨린다 (등재 근거가 raw 에 없다고 주장하게)
spec = copy.deepcopy(gate._CSM_CONTINUITY_EXCEPTIONS[("하나생명보험", "2024.4Q")])
saved = gate._CSM_CONTINUITY_EXCEPTIONS[("하나생명보험", "2024.4Q")]
broken = copy.deepcopy(spec)
broken["verify"]["present_markers"] = broken["verify"]["present_markers"] + ["999,999,999"]
gate._CSM_CONTINUITY_EXCEPTIONS[("하나생명보험", "2024.4Q")] = broken
show("M6  인용 마커가 raw 에 없다 (근거 반증)", run(BASE))

# M7 — 있으면 안 되는 대조군 마커가 실제로는 그 파일에 있다고 선언
broken2 = copy.deepcopy(spec)
broken2["verify"]["absent_markers"] = ["308,905,720"]   # 실제로는 있는 문자열
gate._CSM_CONTINUITY_EXCEPTIONS[("하나생명보험", "2024.4Q")] = broken2
show("M7  대조군 마커가 실제로 존재 (두 기준 혼재 지문)", run(BASE))

# M8 — 인용 파일 경로가 없는 클론
broken3 = copy.deepcopy(spec)
broken3["verify"]["file"] = "data/dart/NOPE/does_not_exist.xml"
gate._CSM_CONTINUITY_EXCEPTIONS[("하나생명보험", "2024.4Q")] = broken3
show("M8  인용 파일 부재(raw 없는 클론) — RED 가 아니라 정직한 YELLOW 여야", run(BASE))

# M9 — 산문만 남기고 박제를 다 빼면 (등재 후퇴 방지)
gate._CSM_CONTINUITY_EXCEPTIONS[("하나생명보험", "2024.4Q")] = {"why": "산문만"}
show("M9  박제 없는 산문 등재로 후퇴", run(BASE))

gate._CSM_CONTINUITY_EXCEPTIONS[("하나생명보험", "2024.4Q")] = saved

print()
print("=" * 100)
print("판정")
print("=" * 100)
print("M1/M2 에서 하나생명 2024.4Q 가 여전히 YELLOW 면 -> 이 면제는 '잔차 박제'가 아니라")
print("(회사,분기) 통째 무조건 통과다. 값이 어떻게 바뀌어도 이 버킷은 다시 RED 가 되지 않는다.")
