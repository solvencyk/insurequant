# -*- coding: utf-8 -*-
"""현재 상태를 **측정해서** 인쇄한다. "뭐가 남았냐" 에 대한 정본 답변기.

## 왜 이 스크립트가 있나

2026-08-30 하루에 같은 사고가 **세 번** 났다. owner 가 "남은 일 뭐냐" 고 물을 때마다
`TODO_*.md` 를 읽어서 답했고, 그때마다 owner 가 "이미 끝낸 것들이잖아" 라고 잡아냈다:

  · KICS-IMG / OCR 3사      -> 실측 항목1/14/27 **39셀 중 결측 0**
  · 시장위험 분해(MLG-2)     -> 실측 하위 36~40 **356/488**, 유도식은 이미 구현·불일치 0
  · designer P1            -> 실측 Pretendard·tabular-nums·favicon **3/4 이미 배포**

원인은 "문서가 낡았다" 가 아니다. **잴 수 있는데 읽어서 답한 것**이 원인이다. 이 저장소는
마스터 JSON·게이트·테스트로 현재 상태를 수십 초 만에 잴 수 있다. 그래서 그 측정을 한 곳에
모아 두고, 상태 질문에는 **이 출력으로만** 답한다.

TODO 는 "무엇을 하기로 했나"(의도)의 기록이고, 이 스크립트는 "지금 무엇이 사실인가"(상태)다.
둘이 어긋나면 **이 스크립트가 맞고 TODO 를 고쳐야 한다.**

사용:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/status_report.py
    ... --fast   게이트 실행을 건너뛰고 데이터 census 만 (수 초)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
FAST = "--fast" in sys.argv


def rule(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def load(rel: str):
    p = ROOT / rel
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------- 1) 게이트
GATES = [
    ("validate_data_contract", "데이터계약 (push #0)"),
    ("validate_kics_disclosure", "K-ICS 룰게이트"),
    ("validate_live_artifacts", "라이브 아티팩트"),
    ("validate_golden_input_fingerprints", "골든 입력지문"),
]


def gates() -> None:
    rule("1. 게이트 — 지금 push 가 되는가")
    if FAST:
        print("  (--fast: 건너뜀)")
        return
    for name, label in GATES:
        p = ROOT / "scripts" / f"{name}.py"
        if not p.exists():
            print(f"  {label:<22} (스크립트 없음)")
            continue
        r = subprocess.run([sys.executable, str(p)], cwd=str(ROOT), capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        tail = [ln for ln in (r.stdout or "").splitlines() if "SUMMARY" in ln or "RED=" in ln]
        verdict = "clear" if r.returncode == 0 else f"BLOCK(exit {r.returncode})"
        print(f"  {label:<22} {verdict}")
        if tail:
            print(f"      {tail[-1].strip()[:150]}")


# --------------------------------------------------------------------------- 2) inbox
def inbox() -> None:
    rule("2. inbox — 진행 중인 스레드")
    active = []
    for d in ("downloader", "parser", "validation", "publishing", "designer"):
        folder = ROOT / "inbox" / d
        if not folder.exists():
            continue
        for f in sorted(folder.glob("*.md")):
            t = f.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^status:\s*(\S+)", t, re.M)
            active.append((d, f.name, m.group(1) if m else "?"))
    if not active:
        print("  활성 0건")
    for d, n, st in active:
        print(f"  [{d}] {st:<9} {n}")


# --------------------------------------------------------------------------- 3) 마스터 커버리지
def masters() -> None:
    rule("3. 마스터 — 행수 · 회사 · 분기범위")
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from build_master_xlsx import FLATTEN, MASTERS
    except Exception as e:  # noqa: BLE001
        print(f"  MASTERS 를 못 읽었다: {e}")
        return
    for jname, sheet, *_ in MASTERS:
        rows = load(jname)
        if rows is None:
            print(f"  {sheet:<14} (파일 없음: {jname})")
            continue
        # 3개 마스터는 디스크에서 long-format 이 아니다(회사별 스냅샷/연도 중첩) —
        # xlsx 빌더의 FLATTEN 을 그대로 태워야 시트와 같은 것을 센다.
        fl = FLATTEN.get(jname)
        if fl is not None:
            try:
                rows = fl(rows)
            except Exception as e:  # noqa: BLE001
                print(f"  {sheet:<14} FLATTEN 실패: {e}")
                continue
        if not isinstance(rows, list):
            print(f"  {sheet:<14} rows=? (예상치 못한 형태)")
            continue
        cos = {r.get("원수사명") for r in rows if r.get("원수사명")}
        qs = sorted({r.get("공시분기") for r in rows
                     if isinstance(r.get("공시분기"), str) and re.match(r"^\d{4}\.\dQ$", r["공시분기"])})
        span = f"{qs[0]}~{qs[-1]}" if qs else "-"
        print(f"  {sheet:<14} {len(rows):>6}행  {len(cos):>3}사  {span}")


# --------------------------------------------------------------------------- 4) 화면 ↔ 마스터
def screen_coverage() -> None:
    rule("4. 화면 ↔ 마스터 — owner 상시 규칙(화면 그래프는 전부 마스터에)")
    sys.path.insert(0, str(ROOT / "tests"))
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import test_push_gate_wiring as T
        from build_master_xlsx import MASTERS
    except Exception as e:  # noqa: BLE001
        print(f"  검사 모듈을 못 읽었다: {e}")
        return
    fetched = T._origin_main_fetches()
    if fetched is None:
        print("  origin/main 배포본을 못 읽었다(슬림 워크트리)")
        return
    sheet_of = {j: s for j, s, *_ in MASTERS}
    gaps = []
    n = 0
    for f in sorted(fetched):
        base = f.lstrip("./")
        if base.startswith("public_exports/"):
            continue
        n += 1
        master = base if base in sheet_of else T.PANEL_DERIVED_FROM.get(base)
        if not master or master not in sheet_of:
            gaps.append(base)
    print(f"  화면 fetch {n}개 · 마스터 시트 없는 것 {len(gaps)}개")
    for g in gaps:
        print(f"    GAP {g}")


# --------------------------------------------------------------------------- 5) 축별 커버리지
def axis_coverage() -> None:
    rule("5. 축별 커버리지 — '얼마나 채워져 있나'")

    k = load("kics_disclosure.json")
    if k:
        idx = defaultdict(dict)
        names = {}
        for r in k:
            idx[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r.get("값")
            names[r["원보험사코드"]] = r["원수사명"]
        qs = sorted({r["공시분기"] for r in k})
        even = [q for q in qs if q.endswith(("2Q", "4Q"))]
        # 금리 시나리오 41~46 (짝수분기만 공시)
        full = sum(1 for c in names for q in even
                   if all(idx.get((c, q), {}).get(i) is not None for i in range(41, 47)))
        print(f"  K-ICS         {len(names)}사 × {len(qs)}분기 ({qs[0]}~{qs[-1]})")
        print(f"    금리시나리오 41~46  완비 {full}/{len(names) * len(even)} "
              f"({full / (len(names) * len(even)):.1%})  [짝수분기만 공시]")
        for it in (36, 37, 38, 39, 40):
            have = sum(1 for m in idx.values() if m.get(it) is not None)
            print(f"    시장위험 항목{it}      {have}/{len(idx)} 버킷")

    bs = load("IFRS17_BS.json")
    if bs:
        q5 = defaultdict(dict)
        allco = {r["원수사명"] for r in bs}
        for r in bs:
            if r["항목번호"] == 5:
                q5[r["공시분기"]][r["원수사명"]] = r.get("값")
        print(f"  17BS 항목5(해약환급금준비금) — 업권 합계(조) / 실값사 / 구멍사  [모집단 {len(allco)}사]")
        for q in sorted(q5)[-4:]:
            v = q5[q]
            tot = sum(x for x in v.values() if x) / 1_000_000
            realv = sum(1 for x in v.values() if x)
            hole = len(allco) - len(v) + sum(1 for x in v.values() if x is None)
            print(f"    {q}  {tot:>6.1f}조   실값 {realv:>2}사   구멍 {hole:>2}사")

    pl = load("PL_breakdown.json")
    if pl:
        nn = sum(1 for r in pl if r.get("값") is not None)
        print(f"  PL_breakdown  {len(pl)}행 · 값 있는 셀 {nn} ({nn / len(pl):.1%})")

    nulls = load("data/_derived/pl_intentional_nulls.json")
    if nulls:
        print(f"    의도적 null(0-fill 억제)  {len(nulls.get('cells', []))}칸")


# --------------------------------------------------------------------------- 6) 최신 분기
def latest_quarter() -> None:
    rule("6. 최신 분기 — 어디까지 적재됐나")
    for jname, label in (("kics_disclosure.json", "K-ICS 공시"),
                         ("CSM_waterfall.json", "CSM 워터폴"),
                         ("PL_breakdown.json", "손익분해 PL"),
                         ("IFRS17_BS.json", "재무상태표")):
        rows = load(jname)
        if not rows:
            continue
        qs = sorted({r.get("공시분기") for r in rows
                     if isinstance(r.get("공시분기"), str) and re.match(r"^\d{4}\.\dQ$", r["공시분기"])})
        if not qs:
            continue
        last = qs[-1]
        n = len({r["원수사명"] for r in rows if r.get("공시분기") == last})
        print(f"  {label:<12} 최신 {last}  ({n}사)")
    disc = ROOT / "data" / "disclosure"
    if disc.exists():
        fys = sorted(p.name for p in disc.glob("FY*") if p.is_dir())
        if fys:
            pdfs = list((disc / fys[-1]).rglob("*.pdf"))
            print(f"  정기경영공시   최신 폴더 {fys[-1]}  (PDF {len(pdfs)}개)")


def main() -> int:
    print("#" * 78)
    print("INSUREQUANT STATUS — 문서가 아니라 데이터를 잰 결과")
    print("  TODO 와 어긋나면 이쪽이 맞다. TODO 를 고쳐라.")
    print("#" * 78)
    gates()
    inbox()
    masters()
    screen_coverage()
    axis_coverage()
    latest_quarter()
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
