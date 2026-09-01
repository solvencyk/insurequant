# -*- coding: utf-8 -*-
"""신설 룰 `KICS_RESTATEMENT_*` 전 버킷 시뮬레이션 + 변이시험.

**룰을 배선하기 전에 반드시 돌린다**(저장소 규율: 1건 고치려다 129건 깨뜨릴 뻔한 실측).
두 방향을 다 센다:
  ① 닫힘 — 지금 데이터에서 이 룰이 RED 를 내는가(내면 안 된다: baseline RED=0)
  ② 깨짐 — 잡아야 할 것을 변이로 만들었을 때 **실제로 잡는가**(못 잡으면 무검사)

변이는 전부 **메모리 안**에서 한다 — 마스터 파일도 등재부도 건드리지 않는다.
"""
import copy
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_data_contract as gate      # noqa: E402


def run(records, ledger):
    env = gate.Env()
    env.kics_records = records
    env.restatement_ledger = ledger
    res = gate.GateResult()
    gate.check_kics_restatement(res, env)
    return res


def summarize(res):
    return (Counter(f.rule for f in res.findings if f.severity == "RED"),
            Counter(f.rule for f in res.findings if f.severity == "YELLOW"))


def main():
    base_env = gate.Env()
    records = base_env.kics_records
    ledger = base_env.restatement_ledger
    assert ledger and ledger.get("entries"), "등재부가 비었다 — 시뮬레이션 의미 없음"
    keys = sorted(ledger["entries"])
    print(f"등재 셀 {len(keys)}칸 · 마스터 레코드 {len(records):,}행")

    def mrec(records, co, q, item):
        for r in records:
            if (r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) == (co, q, item):
                return r
        return None

    print("\n" + "=" * 78)
    print("① 닫힘 — 현행 데이터에서 RED 이 나오면 안 된다")
    print("=" * 78)
    red, yel = summarize(run(records, ledger))
    print(f"  RED={sum(red.values())} {dict(red)}")
    print(f"  YELLOW={sum(yel.values())} {dict(yel)}")
    ok_closed = sum(red.values()) == 0
    print(f"  -> {'PASS' if ok_closed else 'FAIL'}")

    print("\n" + "=" * 78)
    print("② 깨짐 — 변이시험. 각 변이가 **의도한 룰**을 켜야 한다")
    print("=" * 78)
    results = []

    # M1: 마스터가 재작성값을 채택 (기준이 갈라지는 그 사고)
    for k in keys[:3] + keys[-1:]:
        e = ledger["entries"][k]
        recs = copy.deepcopy(records)
        r = mrec(recs, e["company"], e["quarter"], int(e["item"]))
        assert r is not None, k
        r["값"] = str(int(e["restated"]))
        red, _ = summarize(run(recs, ledger))
        hit = red.get("KICS_RESTATEMENT_MASTER_ADOPTED_RESTATED", 0) == 1 and sum(red.values()) == 1
        results.append(("M1 마스터가 재작성값 채택", k, "MASTER_ADOPTED_RESTATED", hit, dict(red)))

    # M2: 제3의 값으로 드리프트
    e = ledger["entries"][keys[0]]
    recs = copy.deepcopy(records)
    mrec(recs, e["company"], e["quarter"], int(e["item"]))["값"] = "999999"
    red, _ = summarize(run(recs, ledger))
    results.append(("M2 제3의 값으로 드리프트", keys[0], "PIN_DRIFT",
                    red.get("KICS_RESTATEMENT_PIN_DRIFT", 0) == 1 and sum(red.values()) == 1,
                    dict(red)))

    # M2b: tol 안(±0.5) 이면 켜지면 안 된다 — 밴드가 아니라 반올림 폭만 허용
    recs = copy.deepcopy(records)
    mrec(recs, e["company"], e["quarter"], int(e["item"]))["값"] = str(
        float(e["as_filed"]) + 0.4)
    red, _ = summarize(run(recs, ledger))
    results.append(("M2b tol 안 변이(+0.4)는 켜지면 안 됨", keys[0], "(none)",
                    sum(red.values()) == 0, dict(red)))

    # M3: 등재 셀이 마스터에서 사라짐 → 결측은 SKIP 이 아니라 RED
    recs = [r for r in copy.deepcopy(records)
            if (r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호"))
            != (e["company"], e["quarter"], int(e["item"]))]
    red, _ = summarize(run(recs, ledger))
    results.append(("M3 등재 셀 행 삭제", keys[0], "CELL_MISSING",
                    red.get("KICS_RESTATEMENT_CELL_MISSING", 0) == 1 and sum(red.values()) == 1,
                    dict(red)))

    # M3b: 값만 null
    recs = copy.deepcopy(records)
    mrec(recs, e["company"], e["quarter"], int(e["item"]))["값"] = None
    red, _ = summarize(run(recs, ledger))
    results.append(("M3b 등재 셀 값 null", keys[0], "CELL_MISSING",
                    red.get("KICS_RESTATEMENT_CELL_MISSING", 0) == 1 and sum(red.values()) == 1,
                    dict(red)))

    # M4: 등재부 필드 누락
    led2 = copy.deepcopy(ledger)
    del led2["entries"][keys[0]]["as_filed_source"]
    red, _ = summarize(run(records, led2))
    results.append(("M4 등재부 근거 필드 삭제", keys[0], "FIELD_MISSING",
                    red.get("KICS_RESTATEMENT_FIELD_MISSING", 0) == 1, dict(red)))

    # M5: 키/본문 불일치
    led2 = copy.deepcopy(ledger)
    led2["entries"][keys[0]]["item"] = 99
    red, _ = summarize(run(records, led2))
    results.append(("M5 키-본문 불일치", keys[0], "KEY_MISMATCH",
                    red.get("KICS_RESTATEMENT_KEY_MISMATCH", 0) == 1, dict(red)))

    # M6: 등재부 깨짐
    red, _ = summarize(run(records, {"_unreadable": "JSONDecodeError: x"}))
    results.append(("M6 등재부 파싱 불가", "-", "LEDGER_UNREADABLE",
                    red.get("KICS_RESTATEMENT_LEDGER_UNREADABLE", 0) == 1, dict(red)))

    # M7: 등재부 부재 → 조용히 꺼지면 안 된다(YELLOW 로 말해야 한다)
    _r, yel = summarize(run(records, None))
    results.append(("M7 등재부 부재(침묵 금지)", "-", "LEDGER_ABSENT(YELLOW)",
                    yel.get("KICS_RESTATEMENT_LEDGER_ABSENT", 0) == 1, dict(yel)))

    # M8: 새 분기가 들어왔는데 스캔은 옛 분기까지 → STALE 로 재라고 말해야 한다
    led2 = copy.deepcopy(ledger)
    led2["_scanned"]["restating_period"] = "FY2026_Q1"
    _r, yel = summarize(run(records, led2))
    results.append(("M8 새 분기 미스캔", "-", "SCAN_STALE(YELLOW)",
                    yel.get("KICS_RESTATEMENT_SCAN_STALE", 0) == 1, dict(yel)))

    # M9: 스캔이 회사를 못 읽었는데 CLEAN 인 척 → COVERAGE_GAP
    led2 = copy.deepcopy(ledger)
    led2["_scanned"]["uncovered"] = ["KR0010", "KR0087"]
    _r, yel = summarize(run(records, led2))
    results.append(("M9 미판독 회사 존재", "-", "COVERAGE_GAP(YELLOW)",
                    yel.get("KICS_RESTATEMENT_COVERAGE_GAP", 0) == 1, dict(yel)))

    # M10: 등재부를 통째로 비우면 → RED 0 이지만 census 는 계속 인쇄돼야 한다(침묵 아님)
    led2 = copy.deepcopy(ledger)
    led2["entries"] = {}
    red, yel = summarize(run(records, led2))
    results.append(("M10 등재 전삭제(침묵 금지)", "-", "CENSUS 유지",
                    yel.get("KICS_RESTATEMENT_CENSUS", 0) == 1 and sum(red.values()) == 0,
                    dict(yel)))

    npass = 0
    for name, key, want, hit, got in results:
        npass += bool(hit)
        print(f"  [{'PASS' if hit else 'FAIL'}] {name:34s} {key:22s} want={want:32s} got={got}")
    print(f"\n변이시험 {npass}/{len(results)} PASS")

    print("\n" + "=" * 78)
    print("③ 오탐 — 등재 안 된 셀을 흔들어도 이 축은 조용해야 한다")
    print("=" * 78)
    ledkeys = {(x["company"], x["quarter"], int(x["item"])) for x in ledger["entries"].values()}
    touched = 0
    fired = 0
    for r in records:
        k = (r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호"))
        if k in ledkeys or not isinstance(k[2], int) or not (1 <= k[2] <= 27):
            continue
        touched += 1
    # 200칸을 무작위가 아니라 결정적으로 고른다(재현성)
    import random
    rng = random.Random(20260901)
    cand = [r for r in records
            if (r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) not in ledkeys
            and isinstance(r.get("항목번호"), int) and 1 <= r["항목번호"] <= 27]
    for r0 in rng.sample(cand, min(200, len(cand))):
        recs = copy.deepcopy(records)
        t = mrec(recs, r0["원보험사코드"], r0["공시분기"], r0["항목번호"])
        t["값"] = "12345678"
        red, _ = summarize(run(recs, ledger))
        fired += sum(red.values())
    print(f"  등재 밖 셀 {touched:,}칸 중 200칸 변이 → 이 축 신규 RED = {fired}")
    print(f"  -> {'PASS' if fired == 0 else 'FAIL'}")

    print("\n" + "=" * 78)
    ok = ok_closed and npass == len(results) and fired == 0
    print("SIMULATION", "ALL PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
