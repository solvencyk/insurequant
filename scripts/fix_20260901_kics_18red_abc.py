# -*- coding: utf-8 -*-
"""과거분기 blocking RED 18건 정정 (2026-09-01, kics 레인 — AIG/ABL/흥국생명, orchestrator 발주).

셀 단위만 건드린다. 마스터 통째 read-modify-write 금지 원칙에 따라 대상 (회사,분기,항목,컬럼)
밖은 한 글자도 바꾸지 않고, 실행 직전에 마스터를 다시 읽는다(동시 세션 lost-update 방지).

## A) AIG손해보험(KR0029) 2025.2Q · 2025.3Q — 경과조치 전면 미적용사의 값_적용후 결측 (추출갭)

두 분기 모두 raw(md_inbox) 가 "당사는 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이
동일함" 을 4회 이상 반복 명시하고, "경과조치의 종류/적용여부" 표는 공통(TFI·보고연장) + 선택
(TAC·TIR·TER·TIRR·적기시정조치유예) 7종 전부 X(미적용) 다. 즉 값_적용후 는 정의상 값(적용전)과
정확히 같아야 하는데, 두 분기 다 파싱 단계에서 값_적용후 필드 자체가 안 쓰였다(추출갭 —
POST_TRANSITION_PARENT_MISSING/CHILD_MISSING 이 정확히 이 형태로 잡는다).

같은 회사 2024.4Q·2025.1Q·2026.1Q 는 전부 값==값_적용후 로 이미 정상 적재돼 있어 대조군이 된다.

**2025.2Q** (md_inbox/FY2025_Q2/KR0029_AIG손해보험.md L232·L347-372) — "[지급여력비율의 경과조치
적용에 관한 사항] (1) 공통적용 경과조치 관련" 표가 지급여력비율/지급여력금액/기본자본/보완자본/
보완자본한도/지급여력기준금액 적용전=적용후 를 백만원 단위로 명시(636,284=636,284 등). 15개
RED 항목(1,2,3,14,15,16,17,18,19,20,21,22,23,27,28) 전부 값을 그대로 값_적용후 에 미러.
+ **부수(collateral)**: item19 를 채우면 `_parent_present_child_incomplete_after`(parent=19→
children 36-40) 가 활성화된다 — 2025.2Q 는 36-40 적용전이 이미 존재(147.24/12.3/0/40.55/282.32)
하므로 그대로 두면 새 RED 4건(36·37·39·40, 38 은 <5 플로어라 제외)이 열린다. 같은 "경과조치
미적용" 근거로 36-40 도 같이 미러한다.

**2025.3Q** (md_inbox/FY2025_Q3/KR0029_AIG손해보험.md L219-372) — 이 분기는 item3(보완자본)=59 가
비영(非零)이라 item2(기본자본)=6304 ≠ item1(가용자본)=6362 인 유일 분기다(2_tier1_bridge 축과
무관 — 5회차 세션이 이미 원문 자기모순으로 재확인 종결한 별개 축). "(1)공통적용 경과조치 관련"
표가 3컬럼(적용전|경과조치|적용후) 로 오분절 돼 있지만(docling 아티팩트), 값이 col1 과 col2 또는
col1 과 col3 중 한쪽에 중복 인쇄되고 나머지 컬럼은 공백이다 — 보완자본(5,870=5,870)·보완자본한도
(127,776=127,776)·해약환급금초과분(5,870=5,870)·지급여력기준금액(255,552=255,552) 넷 다 두
숫자가 일치해 컬럼이 어느 쪽이든 "전=후" 라는 결론은 불변. 원 RED(POST_TRANSITION_CHILD_MISSING)
는 item16,17,18,19,20,21 만 지목했지만, **부수**: item1,2,27,28(가용자본측 continuity core)을 안
채우면 2025.2Q 를 고친 뒤 그 자체가 SANDWICHED 로 새로 RED 가 된다(직전분기 2025.2Q 가 이제
적용후 존재 + 다음분기 2026.1Q 도 존재 = 이 분기만 비면 break). item22,23 은 core 가 이 분기에서
전부 닫히면 census 상 `review`(비차단)로 내려가 굳이 필요는 없지만, 같은 근거(경과조치 미적용
문구가 이 분기에도 반복)로 이미 확보했으므로 같이 채워 상태를 일관되게 둔다.
item3·14·15후는 이미 마스터에 있다(59/2556/3297.52) — 건드리지 않는다.
item17→29-35, item19→36-40 하위 census 는 두 분기 다 29-35·36-40 적용전 행 자체가 없어(간이
공시 아님에도 이 회사가 그 세부표를 못 잡은 기존 갭, 이 라운드 범위 밖) "기대" 목록에서 빠진다
— collateral 불필요(전수 확인함, scripts/_probes/probe_20260901_aig_grandchildren.py).

## B) 에이비엘생명보험(KR0070) 2025.3Q — item16(분산효과) 값_적용후 계산 오류

당분기부터 TAC(자본감소분)·TIR·TER 를 신규 적용한 진짜 적용사. item15·17·18·19·20·21_적용후는
서로 다른 세부표(①②③, md_inbox L268-350)에서 각각 채워졌지만, 정식 상관행렬 공식으로 교차
검산하면(scripts/_probes/probe_20260901_abl_mmult_check.py, kics_json_rules.R4 를 import) item15
= sqrt(V'R4V)+item21 잔차가 -0.15(반올림 수준)로 닫힌다 — 즉 15/17/18/19/20/21 은 전부 맞다.
분산효과는 원문 자신이 "- 분산효과 : (1+2+3+4+5) - Ⅰ" 라고 라벨을 붙인 정의값이라(md_inbox
L251) 그 정의 그대로 Σ(17..21)-15 를 다시 계산해 넣는다: 7471.13+0+4391.01+3499+1302-12459.99
= **4203.15**(부동소수 오차 없이 정확히 떨어짐). 기존 값 5639.87 은 item19 를 적용후(4391.01)
대신 적용전(5828)으로 잘못 섞어 계산한 결과와 -0.27 차이로 거의 일치해 오염 경로까지 특정됨
(파생값으로 갈아끼우는 게 아니라, 원문이 정의한 항등식 자체를 원문이 확정한 다른 5개 입력으로
다시 계산하는 것 — 발행사 총괄표 대 세부표 불일치 사안이 아니다).

## C) 흥국생명보험(KR0071) 2023.4Q — item24 값(적용전) 오염 (형제분기와 동일한 대시-오독)

md_inbox/FY2023_Q4/KR0071_흥국생명보험.md L366-369, [경과조치 적용 전 지급여력비율 세부] 표
(당분기 23.4Q/직전분기 23.3Q/전전분기 23.2Q 3컬럼):
    Ⅲ. 기타 요구자본 (1+2+3)                | 7,976 | 8,313 | 8,313 |
    1. 종속회사의 요구자본 환산치            |   -   |   -   |   -   |
    2. 비례성원칙을 적용한 종속회사의 요구자본 대응치 | - | - | - |
    3. 관계회사의 요구자본 환산치            | 7,976 | 8,313 | 8,313 |
당분기(1열) item24="-"=0 인데 마스터엔 7976(=item23·item26 복사)이 들어가 있다. 같은 회사
2023.3Q 에 있었던 **동일 패턴**이 이미 fix_20260821_kr0071_item24_fabricated_dash.py 로 수정된
바 있다("-" 를 0 으로) — 이번은 그 스윕이 못 잡은 인접 분기의 같은 버그. item25(0)·item26(7976)
은 원문과 이미 일치하므로 손대지 않는다. 값_적용후 는 세 항목 다 원래도 결측(형제와 동일)이라
새로 만들지 않는다.

## 시뮬레이션 실측 (--dry-run, 라이브 마스터 대비)
    RED 18 -> 0 (AIG 16 + ABL 1 + 흥국생명 1) · 새로 생긴 RED 0건 · 범위 밖 콤보 변화 0 ·
    행수 변화 0(전부 기존 행의 필드 추가/수정, 신규 행 없음) · 중복 콤보 0

Usage:
  ...python scripts/fix_20260901_kics_18red_abc.py            # dry-run
  ...python scripts/fix_20260901_kics_18red_abc.py --apply    # write
"""
from __future__ import annotations
import argparse, collections, io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "kics_disclosure.json"

# (code, quarter, item) -> new 값_적용후 string. "MIRROR" 는 같은 레코드의 값(적용전) 문자열을
# **그대로** 복사한다(재포맷/재계산 없음 — 부동소수 표기 어긋남 방지).
MIRROR_POST: set[tuple[str, str, int]] = set()
for it in (1, 2, 3, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 27, 28,
           36, 37, 38, 39, 40):
    MIRROR_POST.add(("KR0029", "2025.2Q", it))
for it in (1, 2, 16, 17, 18, 19, 20, 21, 22, 23, 27, 28):
    MIRROR_POST.add(("KR0029", "2025.3Q", it))

# 명시값 SET (계산/원문 대사로 확정된 값 — 미러가 아님)
SET_EXPLICIT: dict[tuple[str, str, int], dict[str, str]] = {
    ("KR0070", "2025.3Q", 16): {"값_적용후": "4203.15"},
    ("KR0071", "2023.4Q", 24): {"값": "0"},
}
# item24 를 지우기 전 반드시 만족해야 하는 지문(아니면 중단)
GUARD_BEFORE: dict[tuple[str, str, int], dict[str, str]] = {
    ("KR0070", "2025.3Q", 16): {"값_적용후": "5639.87"},
    ("KR0071", "2023.4Q", 24): {"값": "7976"},
}


def key(r):
    try:
        return (r.get("원보험사코드"), r.get("공시분기"), int(r.get("항목번호")))
    except (TypeError, ValueError):
        return (r.get("원보험사코드"), r.get("공시분기"), None)


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write (default: dry-run)")
    a = ap.parse_args(argv)

    rows = json.loads(TARGET.read_text(encoding="utf-8"))
    assert isinstance(rows, list), type(rows)
    before_n = len(rows)
    before_combo = collections.Counter(key(r) for r in rows)

    by = {key(r): r for r in rows}

    # --- guard: 명시 SET 대상이 정말 기대한 이전값인가 ---
    for k, want in GUARD_BEFORE.items():
        r = by.get(k)
        if r is None:
            print(f"  ABORT {k}: 레코드 자체가 없다 — 전제 변경"); return 2
        for col, wv in want.items():
            cur = r.get(col)
            if str(cur) != wv:
                print(f"  ABORT {k} [{col}]: 현재값 {cur!r} != 기대 {wv!r} — 전제 변경")
                return 2

    changed: list[tuple] = []
    missing: list[tuple] = []

    # --- mirror: 값_적용후 를 같은 레코드의 값(적용전)으로 채운다 ---
    for k in sorted(MIRROR_POST):
        r = by.get(k)
        if r is None:
            missing.append((*k, "값_적용후", None, "<RECORD MISSING>")); continue
        pre = r.get("값")
        if pre is None:
            missing.append((*k, "값_적용후", None, "<값(적용전) MISSING>")); continue
        old_post = r.get("값_적용후")
        if old_post is not None:
            print(f"  SKIP(이미 있음) {k} 값_적용후={old_post!r} (미러 대상 아님, 건드리지 않음)")
            continue
        changed.append((*k, "값_적용후", old_post, pre))
        if a.apply:
            r["값_적용후"] = pre

    # --- explicit set ---
    for k, cols in SET_EXPLICIT.items():
        r = by.get(k)
        if r is None:
            for col in cols: missing.append((*k, col, None, "<RECORD MISSING>"))
            continue
        for col, new in cols.items():
            old = r.get(col)
            if str(old) != new:
                changed.append((*k, col, old, new))
                if a.apply:
                    r[col] = new

    print(f"변경 {len(changed)} · 대상없음 {len(missing)}")
    for x in changed: print("   CHG", x)
    for x in missing: print("   !! MISSING", x)

    if not a.apply:
        print("\n(dry-run; --apply 로 기록)")
        return 0

    after_combo = collections.Counter(key(r) for r in rows)
    lost = {k: (before_combo[k], after_combo.get(k, 0)) for k in before_combo
            if after_combo.get(k, 0) != before_combo[k]}
    gained = {k: after_combo[k] for k in after_combo if k not in before_combo}
    dups = [k for k, v in after_combo.items() if v > 1]
    print(f"\nrows {before_n} -> {len(rows)}")
    print(f"  콤보 변화(행수증감): {lost or '없음'}")
    print(f"  신규 콤보: {gained or '없음'}")
    print(f"  중복 콤보: {dups or '없음'}")
    if lost or gained or dups or len(rows) != before_n:
        print("  !! 예상 밖 변화 — 기록하지 않는다"); return 2

    TARGET.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
