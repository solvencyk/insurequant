# -*- coding: utf-8 -*-
"""룰 커버리지를 **선언하고 기계로 대조한다** (owner 2026-08-21).

## 왜 필요한가

골든 테스트는 `있는 것`을 박제한다. `있어야 하는데 없는 것`은 모른다 — 룰을 아예 안 쓰면
골든은 그 부재까지 같이 고정한다. 실제로 그렇게 됐다: 항목 12·13·24·25·26 은 **어떤 룰도
참조하지 않는데** 게이트는 몇 달간 RED=0 이었고, 2026-08-21 에 손으로 뒤져서야 발견됐다
(흥국생명 2023.3Q item24=8,313 이 원문에 없는 날조값이었다).

owner 지적: "validator가 매번 검증룰 까먹거나 몇개 빼먹는 것도 비슷한 이유 아니냐."
맞다. 그런데 원인은 "룰이 git 에 없어서"가 아니다 — 룰은 이미 코드로 git 에 있다.
없는 것은 **'무엇이 검사돼야 하는가'라는 선언**이고, 선언이 없으면 빠진 것을 셀 수가 없다.

## 어떻게 재나 — 변이(mutation)

각 (항목, 컬럼)의 값을 전부 흔들어 놓고 룰엔진을 다시 돌려, **finding 의 status 가 하나라도
바뀌는지** 본다. 안 바뀌면 그 칸은 어떤 룰도 안 보는 것이다. 정적 분석(어느 룰이 어느 item 을
참조하나)과 달리 이건 속일 수 없다 — 룰이 있어도 실제로 안 걸리면 무방비로 잡힌다.
`run_validation` 1회 0.03초, 전수 46항목 x 2컬럼 ≈ 3초.

## 이 테스트가 실패하면

- **GUARDED 로 선언했는데 무방비로 측정됨** = 룰이 사라졌거나 약해졌다. 심각. 되돌려라.
- **무방비로 선언했는데 GUARDED 로 측정됨** = 누가 커버리지를 늘렸다. 좋은 일이다.
  아래 MANIFEST 에서 그 항목을 지워 반영하라(그래야 다시 없어질 때 이 테스트가 잡는다).

## 이 테스트가 증명하지 **못하는** 것 — 동어반복

변이시험은 "룰이 이 칸을 본다"를 증명한다. **"룰이 실패할 수 있다"는 증명하지 않는다.**
값을 파이프라인이 항등식에 맞게 되맞춰(reconcile) 저장하면, 룰은 실데이터에서 영원히 통과하고
변이시험은 여전히 GUARDED 로 나온다. 실측 반례(2026-08-21): `item4`(Ⅰ 순자산)가
`fill_period_to_disclosure._reconcile_item4_from_components` / `recalc_kics_derived.py` 때문에
공시값이 아니라 자식합으로 덮여 있어, **rule 2 의 잔차가 484건 중 452건에서 정확히 0** 이다
(억원 반올림 표에서 7개 항목 합이 93% 확률로 딱 떨어질 수는 없다). 즉 rule 2 는 GUARDED 로
측정되지만 실데이터에서는 구조적으로 못 터진다.

동어반복 탐지는 **잔차 분포**를 봐야 한다(정확히 0 비율이 비정상적으로 높으면 입력이 공시값이
아니라 파생값이다). 그건 이 테스트가 아니라 게이트 룰의 몫이다 — 티켓 발주됨.

## 두 층을 다 잰다

룰이 두 파일에 흩어져 있다 — 일반 항등식은 `kics_json_rules.run_validation`(적용전 위주),
`적용후` 검사의 상당 부분은 `scripts/validate_kics_disclosure.py` 의 별도 축(mmult15/17/19 ·
R1 · R2 · R5 · R6 · R7 · R8 · 36_irr · 기타요구자본 합)에 나중에 덧댄 것이다. 그래서 **층별로
따로 잰다**:

1. `test_item_coverage_matches_manifest` — 룰엔진만. 빠르다(~10초). 아래 PRE/POST 매니페스트.
2. `test_full_gate_coverage_matches_manifest` — 게이트 전체를 서브프로세스 없이 in-process 로
   돌려(`--master` 로 흔든 사본을 물린다) **엔진이 못 보는 칸을 게이트는 보는지** 확인한다.
   엔진 무방비 48칸만 검사하므로 ~40초.

실측(2026-08-21): 엔진 무방비 48칸 중 **44칸은 게이트 전체가 잡는다.** 진짜 사각은 **4칸**
= `item12`·`item13` 의 적용전·적용후. 즉 "적용후 43칸 무방비"는 엔진만 본 과장이었다.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
MASTER = ROOT / "kics_disclosure.json"

# 룰엔진이 내보내야 하는 룰 id 전량. 추가·개명·삭제하면 여기도 고쳐야 테스트가 통과한다.
DECLARED_RULES = {
    "1",          # item1 = item2 + item3
    "2",          # item4 = sum(items 5-11)
    "3",          # 영구 SKIP (item4-item12+item13 다리 — 대상을 item1 로 잡아 2.7% 밖에 안 닫힌다.
                  #            item2 로 잡으면 88.8%. 티켓 inbox/validation/20260821T1100Z)
    "4",          # item15 = sqrt(R4[17-20]) + item21
    "5",          # item14 = item15 - item22 + item23
    "6",          # item16 = sum(17..21) - item15
    "7",          # item27 = item1 / item14 * 100
    "8",          # item28 = item2 / item14 * 100
    "8_life",     # item17 = sqrt(R7[29-35])
    "8_post",     # item28 적용후
    "9",          # 경과조치 방향성 (item2 적용후)
    "10",         # 경과조치 방향성 (item14 적용후)
    "19_market",  # item19 = sqrt(MARKET_M[36-40])
    "36_irr",     # item36 = f(41-46)
}

# 적용전(값)에서 **어떤 룰도 보지 않는** 항목. 빈 dict 가 목표다.
PRE_UNGUARDED = {
    12: "item2 = item4 - item12 - item13 다리 미배선. 실측 88.8%(420/473), 잔차 53건은 "
        "회사-체계적(푸본현대 13/13 · IBK연금 13/13). 티켓 inbox/validation/20260821T1100Z",
    13: "위와 같은 다리. rule 3 의 SKIP 사유가 대상을 item1 로 잘못 잡고 있어 영원히 안 닫혔다.",
    24: "item23 = item24 + item25 + item26 룰 미배선. 실측 오탐 0(적용전 401검사/400통과). "
        "이 구멍 때문에 흥국생명 2023.3Q item24=8,313(원문은 '-') 날조값이 안 잡혔다.",
    25: "위와 같은 룰.",
    26: "위와 같은 룰.",
}

# 적용후(값_적용후)에서 룰엔진이 보는 항목. 나머지는 전부 엔진 사각(모듈 docstring 참조).
POST_GUARDED = {2, 14, 28}

# **게이트 전체(엔진 + validate_kics_disclosure 축)로도** 못 잡는 항목. 여기가 진짜 사각이다.
# 빈 dict 가 목표. 값을 흔들어도 게이트 출력이 한 글자도 안 바뀌는 칸들이다.
GATE_BLIND = {
    12: "Ⅱ 지급여력금액 불인정 항목 — 어떤 항등식에도 안 들어간다. rule 3 이 SKIP 이고 "
        "그 사유가 대상을 item1 로 잘못 잡았다(2.7%). 올바른 다리는 item2 = item4 - item12 - item13 "
        "(실측 88.8%)인데, 잔차 53건의 원인이 **마스터에 자리 없는 값**이라 아직 못 건다: "
        "원문 각주가 '기본자본 = 순자산 - (불인정항목 - 보완자본한도초과) - 재분류' 라고 정의하는데 "
        "'보완자본 한도초과액' 항목이 스키마에 없다(푸본현대 2026.1Q 3,447.4억 등 백만원 단위로 일치 확인). "
        "티켓 inbox/validation/20260821T1100Z.",
    13: "Ⅲ 보완자본으로 재분류하는 항목 — 위와 같은 다리에 걸린 같은 원인.",
}


def _findings(rows):
    from solvency.validation.kics_json_rules import run_validation
    r = run_validation(rows)
    return r["findings"] if isinstance(r, dict) else r


def _sig(findings):
    return {(f["원보험사코드"], f["공시분기"], f["rule"]): f["status"] for f in findings}


@pytest.fixture(scope="module")
def rows():
    if not MASTER.exists():
        pytest.skip(f"master 없음: {MASTER}")
    return json.loads(MASTER.read_text(encoding="utf-8"))


def test_rule_id_set_matches_manifest(rows):
    """엔진이 내보내는 룰 id == 선언된 집합. 양방향."""
    emitted = {f["rule"] for f in _findings(rows)}
    missing = DECLARED_RULES - emitted
    extra = emitted - DECLARED_RULES
    assert not missing, (
        f"선언된 룰이 엔진에서 안 나온다: {sorted(missing)}. "
        "룰이 삭제·개명됐거나 조건이 좁아져 한 번도 발화하지 않는다.")
    assert not extra, (
        f"엔진이 선언되지 않은 룰을 내보낸다: {sorted(extra)}. "
        "DECLARED_RULES 에 목적 한 줄과 함께 추가하라 — 선언 없는 룰은 아무도 그 존재를 모른다.")


def test_item_coverage_matches_manifest(rows):
    """각 (항목, 컬럼)을 오염시켜 룰이 알아채는지 전수 확인하고 MANIFEST 와 대조한다."""
    base = _sig(_findings(rows))
    items = sorted({int(r["항목번호"]) for r in rows if str(r.get("항목번호", "")).isdigit()})

    wrong_guarded, wrong_unguarded = [], []
    for item in items:
        for col in ("값", "값_적용후"):
            perturbed = copy.deepcopy(rows)
            n = 0
            for r in perturbed:
                if str(r.get("항목번호")) == str(item) and r.get(col) not in (None, ""):
                    try:
                        r[col] = str(float(str(r[col]).replace(",", "")) * 1.5 + 1234.0)
                        n += 1
                    except ValueError:
                        pass
            if n == 0:
                continue                      # 그 컬럼에 셀이 없으면 검사할 것도 없다
            after = _sig(_findings(perturbed))
            guarded = any(base[k] != after.get(k) for k in base)

            if col == "값":
                expected = item not in PRE_UNGUARDED
            else:
                expected = item in POST_GUARDED

            if expected and not guarded:
                wrong_guarded.append(f"item{item}[{col}] {n}칸 오염 → 아무 룰도 반응 없음")
            elif not expected and guarded:
                wrong_unguarded.append(f"item{item}[{col}] 이제 검사된다")

    assert not wrong_guarded, (
        "검사되고 있어야 할 칸이 무방비다 — 룰이 사라졌거나 약해졌다:\n  "
        + "\n  ".join(wrong_guarded))
    assert not wrong_unguarded, (
        "커버리지가 늘었다. MANIFEST 를 갱신하라(안 그러면 다시 없어질 때 못 잡는다):\n  "
        + "\n  ".join(wrong_unguarded))


def _mutate(rows, item, col):
    """(항목, 컬럼) 을 통째로 흔든 사본과 흔든 셀 수."""
    out, n = copy.deepcopy(rows), 0
    for r in out:
        if str(r.get("항목번호")) == str(item) and r.get(col) not in (None, ""):
            try:
                r[col] = str(float(str(r[col]).replace(",", "")) * 1.5 + 1234.0)
                n += 1
            except ValueError:
                pass
    return out, n


def test_full_gate_coverage_matches_manifest(rows, tmp_path):
    """엔진이 못 보는 칸을 **게이트 전체**는 보는지. 진짜 사각은 GATE_BLIND 뿐이어야 한다."""
    import contextlib
    import io
    import re

    sys.path.insert(0, str(ROOT / "scripts"))
    import validate_kics_disclosure as gate

    # main() 은 실행마다 artifacts/kics_validation/ 에 report_<ts>.json 을 쓰고
    # **report_latest.json 을 덮어쓴다**. 변이 데이터의 결과가 그 stable-name 포인터에 남으면
    # 다음에 그 파일을 읽는 사람·스크립트가 쓰레기를 보게 된다 — 원본을 떠 놨다가 되돌린다.
    artifacts = ROOT / "artifacts" / "kics_validation"
    artifacts.mkdir(parents=True, exist_ok=True)
    before = set(artifacts.glob("*"))
    latest = artifacts / "report_latest.json"
    latest_backup = latest.read_bytes() if latest.exists() else None
    master = tmp_path / "master.json"

    def gate_output(rs):
        master.write_text(json.dumps(rs, ensure_ascii=False), encoding="utf-8")
        buf, argv = io.StringIO(), sys.argv[:]
        sys.argv = ["gate", "--master", str(master)]
        try:
            with contextlib.redirect_stdout(buf):
                gate.main()
        finally:
            sys.argv = argv
        # 매 실행 달라지는 타임스탬프·리포트 파일명은 지운다
        return re.sub(r"\d{8}T\d{6}Z", "T", buf.getvalue())

    # 게이트 1회가 세션 초 0.79초에서 룰이 늘며 ~4초가 됐다. 48칸 전수는 그만큼 선형으로 늘어
    # 훅을 84초 -> 267초로 밀어올렸다. 그래서 두 속도로 나눈다:
    #   기본(로컬 pytest)  = GATE_BLIND 선언분만 셀 단위 + 나머지는 한 번에 묶어 확인. 게이트 6회.
    #   FULL_COVERAGE_SWEEP=1 = 48칸 전수. **훅이 이 모드로 돌린다** — push 는 드물고,
    #                           "한 칸이 조용히 사각이 되는 것"을 놓치면 이 테스트의 존재 이유가 없다.
    full = os.environ.get("FULL_COVERAGE_SWEEP") == "1"
    targets = ([(i, "값") for i in sorted(PRE_UNGUARDED)]
               + [(i, "값_적용후") for i in range(1, 47) if i not in POST_GUARDED])
    try:
        base = gate_output(rows)
        blind, caught = [], []
        declared = [(i, c) for i, c in targets if i in GATE_BLIND]
        others = [(i, c) for i, c in targets if i not in GATE_BLIND]

        for item, col in (targets if full else declared):
            mutated, n = _mutate(rows, item, col)
            if n == 0:
                continue
            (caught if gate_output(mutated) != base else blind).append((item, col, n))

        if not full:
            # 나머지는 한꺼번에 흔든다. 게이트가 **아무 반응도 안 하면** 그 축들이 통째로
            # 죽은 것이므로 잡힌다. 한 칸만 조용히 사각이 되는 경우는 이 묶음으로 못 잡는다 —
            # 그래서 훅은 FULL_COVERAGE_SWEEP=1 로 돈다.
            batch, total = rows, 0
            for item, col in others:
                batch, n = _mutate(batch, item, col)
                total += n
            if total and gate_output(batch) == base:
                blind.extend((i, c, 0) for i, c in others)
    finally:
        for f in set(artifacts.glob("*")) - before:
            with contextlib.suppress(OSError):
                f.unlink()
        if latest_backup is not None:
            latest.write_bytes(latest_backup)
        elif latest.exists():
            with contextlib.suppress(OSError):
                latest.unlink()

    unexpected_blind = [f"item{i}[{c}] {n}칸" for i, c, n in blind if i not in GATE_BLIND]
    now_covered = sorted({i for i, _c, _n in caught} & set(GATE_BLIND))

    assert not unexpected_blind, (
        "게이트 전체로도 못 잡는 칸이 새로 생겼다 — 축이 사라졌거나 좁아졌다:\n  "
        + "\n  ".join(unexpected_blind))
    assert not now_covered, (
        f"item{now_covered} 가 이제 검사된다. GATE_BLIND 에서 지워라 — "
        "안 지우면 다시 사각이 될 때 이 테스트가 못 잡는다.")
