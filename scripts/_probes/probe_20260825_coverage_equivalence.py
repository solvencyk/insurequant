# -*- coding: utf-8 -*-
"""휴리스틱 룰 쳐내기 **커버리지 불변 증명** 하니스 (read-only, 2026-08-25).

## 수용기준

쳐내기 전/후로 **산술·구조 층의 실효 커버리지가 단 1셀도 줄지 않았음**을 변이시험으로 보인다.
쳐내기 전에 한 번(`--out before.json`), 후에 한 번(`--out after.json`) 돌리고
`--compare before.json after.json` 으로 대조한다.

## 하니스 자신의 함정 3개 (2026-08-24 에 두 번 데인 자리)

1. **마스터의 `값`·`값_적용후` 는 대부분 문자열이다.** 실측(`probe_20260825_value_types.py`):
   `kics_disclosure.json` 의 `값` 22,658칸 중 **진짜 숫자는 724칸**(3.2%)이고 21,924칸이
   숫자문자열이다. `isinstance(v,(int,float))` 로 거르면 40,655칸 중 1,434칸(3.5%)만 흔들고
   "전부 눈멀었다" 는 거짓 결과가 나온다. 그래서 `_shake()` 는 쉼표·△·괄호까지 파싱한다.
2. **게이트 리포트 공유폴더(`artifacts/kics_validation/`)를 읽지 않는다.** 다른 프로세스의
   리포트를 자기 것으로 읽으면 항상 "변화 없음" 이 된다. 이 하니스는 `main()` 을 아예 안 부르고
   `run_validation` / `run_gate` 를 **in-process** 로 호출해 반환값만 쓴다 — 파일을 한 개도
   안 쓰고 안 읽는다.
3. **음성대조군을 양방향으로 넣는다.** "예상대로 안 잡힘" 만 확인하는 대조군을 넣으면 아무것도
   안 흔들어도 통과한다. 여기서는 ① 반드시 반응해야 하는 표적(item1·14 · PL 항등식 버킷)이
   반응하는지 ② 아무것도 안 흔든 사본이 **무반응**인지(비결정성 탐지) 둘 다 본다.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_data_contract as dc          # noqa: E402
import validate_kics_disclosure as kg        # noqa: E402

NUMLIKE = re.compile(r"^-?[\d,]+(\.\d+)?$")


def _shake(v):
    """값을 흔든 새 값. 문자열·△·괄호·쉼표 전부 처리. 못 흔들면 None."""
    if v is None or v == "" or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v) * 1.5 + 1234.0
    s = str(v).strip()
    neg = False
    if s.startswith("△") or s.startswith("▲"):
        s, neg = s[1:].strip(), True
    if s.startswith("(") and s.endswith(")"):
        s, neg = s[1:-1].strip(), True
    if not NUMLIKE.match(s):
        return None
    try:
        x = float(s.replace(",", ""))
    except ValueError:
        return None
    if neg:
        x = -x
    return str(x * 1.5 + 1234.0)


# ---------------------------------------------------------------------------
# 지문 (fingerprint) — 게이트가 무엇을 어떻게 판정했는가
# ---------------------------------------------------------------------------
def dc_fingerprint(res, drop_anomaly: bool = False) -> set:
    """`message` 까지 넣는다 — 룰 이름만 보면 **같은 룰의 값이 바뀐 것**을 못 잡는다
    (실측: findings 297건이 (check,sev,master,co,q,rule) 만으로는 177개 튜플로 뭉개진다)."""
    return {(f.check, f.severity, f.master, f.company, f.quarter, f.rule, f.message)
            for f in res.findings
            if not (drop_anomaly and f.check == "anomaly")}


def kics_fingerprint(records) -> set:
    """K-ICS 룰엔진 matrix + main() 이 인쇄하는 메타층을 **파일 없이** 직접 계산."""
    rep = kg.run_validation(records,
                            source_has_breakdown=kg._scan_breakdown_presence(records),
                            tfi_applicability=kg._load_tfi_applicability())
    out = {("rule", f.get("원보험사코드"), f.get("공시분기"), f.get("rule"), f.get("status"))
           for f in rep.get("findings", [])}
    ac = kg._axis_evaluation_census(records)
    ared, arev = kg._axis_eval_findings(ac)
    out |= {("axis_red", r["axis"], r["column"], None, None) for r in ared}
    out |= {("axis_low", r["axis"], r["column"], None, None) for r in arev}
    out |= {("axis_mirror", f["code"], f["quarter"], f["axis"], f["column"])
            for f in kg._axis_mirror_findings(ac)}
    tc, _ = kg._identity_tautology_census(records)
    tred, texempt, trev = kg._identity_tautology_findings(tc)
    for tag, bucket in (("taut_red", tred), ("taut_exempt", texempt), ("taut_review", trev)):
        out |= {(tag, r.get("axis"), r.get("column"), r.get("rule"), None) for r in bucket}
    return out


# ---------------------------------------------------------------------------
# 스윕 A — CSM_waterfall / PL_breakdown 버킷 (쳐내는 CHECK 5 가 읽는 유일한 마스터)
# ---------------------------------------------------------------------------
def sweep_pl_csm(env, base: set, base_noanom: set, limit: int | None) -> dict:
    """각 (회사,분기) 버킷의 값을 전부 흔들고 게이트 반응을 기록한다.

    한 번의 게이트 실행에서 **두 지문**을 뽑는다 — `reacts`(현행) 와 `reacts_sim_pruned`
    (CHECK 5 findings 를 뺀 가상 상태). `check_generic_anomalies` 는 `res` 에 append 만
    하고 다른 검사와 상태를 공유하지 않으므로 후자는 쳐낸 뒤의 게이트와 **정의상 같다**.
    그 동치가 진짜인지는 쳐낸 뒤 이 하니스를 다시 돌려 `reacts` 와 대조해 확인한다."""
    buckets = sorted(set(env.wf) | set(env.pl))
    if limit:
        buckets = buckets[:limit]
    orig_wf, orig_pl = env.wf, env.pl
    out = {}
    t0 = time.perf_counter()
    for i, b in enumerate(buckets, 1):
        wf2, pl2 = copy.deepcopy(orig_wf), copy.deepcopy(orig_pl)
        n = 0
        for d in (wf2, pl2):
            for k, v in list(d.get(b, {}).items()):
                nv = _shake(v)
                if nv is not None:
                    d[b][k] = nv
                    n += 1
        if n == 0:
            continue
        env.wf, env.pl = wf2, pl2
        try:
            res = dc.run_gate(env)
            full, noanom = dc_fingerprint(res), dc_fingerprint(res, drop_anomaly=True)
        finally:
            env.wf, env.pl = orig_wf, orig_pl
        diff, diff2 = base ^ full, base_noanom ^ noanom
        out["|".join(b)] = {"cells": n,
                            "reacts": bool(diff),
                            "reacts_sim_pruned": bool(diff2),
                            "rules": sorted({d[5] for d in diff}),
                            "rules_sim_pruned": sorted({d[5] for d in diff2})}
        if i % 25 == 0:
            print(f"    ...{i}/{len(buckets)} ({time.perf_counter()-t0:.0f}s)", flush=True)
    return out


# ---------------------------------------------------------------------------
# 스윕 B — kics_disclosure (항목 x 컬럼). 산술·구조 층의 본체.
# ---------------------------------------------------------------------------
def sweep_kics(env, records, dc_base: set, dc_base_noanom: set, kg_base: set) -> dict:
    items = sorted({int(r["항목번호"]) for r in records
                    if str(r.get("항목번호", "")).isdigit()})
    orig = env.kics_records
    out = {}
    t0 = time.perf_counter()
    for item in items:
        for col in ("값", "값_적용후"):
            mut, n = copy.deepcopy(records), 0
            for r in mut:
                if str(r.get("항목번호")) == str(item):
                    nv = _shake(r.get(col))
                    if nv is not None:
                        r[col] = nv
                        n += 1
            if n == 0:
                continue
            kg_after = kics_fingerprint(mut)
            env.kics_records = mut
            try:
                res = dc.run_gate(env)
                dc_after = dc_fingerprint(res)
                dc_after_noanom = dc_fingerprint(res, drop_anomaly=True)
            finally:
                env.kics_records = orig
            kg_diff = kg_base ^ kg_after
            dc_diff = dc_base ^ dc_after
            dc_diff2 = dc_base_noanom ^ dc_after_noanom
            out[f"item{item}|{col}"] = {
                "cells": n,
                "reacts": bool(kg_diff or dc_diff),
                "reacts_sim_pruned": bool(kg_diff or dc_diff2),
                "engine_rules": sorted({d[3] for d in kg_diff if d[0] == "rule"}),
                "meta": sorted({d[0] for d in kg_diff if d[0] != "rule"}),
                "gate_rules": sorted({d[5] for d in dc_diff}),
                "gate_rules_sim_pruned": sorted({d[5] for d in dc_diff2}),
            }
        print(f"    item{item} done ({time.perf_counter()-t0:.0f}s)", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    ap.add_argument("--limit", type=int, default=None, help="PL/CSM 버킷 상한(빠른 확인용)")
    ap.add_argument("--skip-kics", action="store_true")
    a = ap.parse_args()

    if a.compare:
        return compare(Path(a.compare[0]), Path(a.compare[1]))

    records = kg._load_records(ROOT / "kics_disclosure.json")
    env = dc.Env()
    _res0 = dc.run_gate(env)
    dc_base = dc_fingerprint(_res0)
    dc_base_noanom = dc_fingerprint(_res0, drop_anomaly=True)
    kg_base = kics_fingerprint(records)
    print(f"BASE: data-contract findings={len(dc_base)} "
          f"(CHECK5 제외 {len(dc_base_noanom)}) · kics fingerprint={len(kg_base)}")

    # ---- 음성대조군 1: 아무것도 안 흔든 사본은 **무반응**이어야 한다(비결정성 탐지) ----
    keep_wf, keep_pl = env.wf, env.pl
    env.wf, env.pl = copy.deepcopy(keep_wf), copy.deepcopy(keep_pl)
    try:
        noop = dc_fingerprint(dc.run_gate(env)) ^ dc_base
    finally:
        env.wf, env.pl = keep_wf, keep_pl
    ctrl = {"noop_stable": not noop, "noop_diff": sorted({d[5] for d in noop})}
    print(f"CONTROL noop(무변이) 반응={len(noop)} → {'OK(안정)' if not noop else '★비결정★'}")

    print("SWEEP A — CSM_waterfall / PL_breakdown 버킷")
    a_res = sweep_pl_csm(env, dc_base, dc_base_noanom, a.limit)
    react_a = sum(1 for v in a_res.values() if v["reacts"])
    sim_a = sum(1 for v in a_res.values() if v["reacts_sim_pruned"])
    print(f"  버킷 {len(a_res)} 중 반응 {react_a} · 쳐낸 뒤 모의 반응 {sim_a}")

    b_res = {}
    if not a.skip_kics:
        print("SWEEP B — kics_disclosure (항목 x 컬럼)")
        b_res = sweep_kics(env, records, dc_base, dc_base_noanom, kg_base)
        react_b = sum(1 for v in b_res.values() if v["reacts"])
        sim_b = sum(1 for v in b_res.values() if v["reacts_sim_pruned"])
        print(f"  표적 {len(b_res)} 중 반응 {react_b} · 쳐낸 뒤 모의 반응 {sim_b}")

    # ---- 음성대조군 2: 반드시 반응해야 하는 표적 (한쪽만 넣으면 아무것도 안 흔들어도 통과한다) ----
    must = ["item1|값", "item14|값", "item19|값", "item15|값",
            "item1|값_적용후", "item15|값_적용후"]
    if b_res:
        ctrl["must_react"] = {k: b_res.get(k, {}).get("reacts") for k in must if k in b_res}
        ctrl["must_react_ok"] = bool(ctrl["must_react"]) and all(ctrl["must_react"].values())
        print(f"CONTROL must-react {ctrl['must_react']} → "
              f"{'OK' if ctrl['must_react_ok'] else '★하니스 고장★'}")
    else:
        ctrl["must_react_ok"] = None
        print("CONTROL must-react: N/A (--skip-kics)")
    # ---- 음성대조군 3: 흔들어도 반응하면 안 되는 표적 (선언된 사각 item12/13) ----
    if b_res:
        blind = {k: b_res.get(k, {}).get("reacts")
                 for k in ("item12|값_적용후", "item13|값_적용후") if k in b_res}
        ctrl["declared_blind"] = blind
        print(f"CONTROL 선언된 사각(반응하면 커버리지가 는 것) {blind}")

    payload = {"base_dc": len(dc_base), "base_kics": len(kg_base),
               "controls": ctrl, "sweep_pl_csm": a_res, "sweep_kics": b_res}
    if a.out:
        Path(a.out).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"WROTE {a.out}")
    return 0


def compare(bp: Path, ap_: Path) -> int:
    b = json.loads(bp.read_text(encoding="utf-8"))
    a = json.loads(ap_.read_text(encoding="utf-8"))
    bad = []
    print("=" * 74)
    print("커버리지 불변 대조  (before -> after)")
    print("=" * 74)
    for sweep in ("sweep_pl_csm", "sweep_kics"):
        B, A = b.get(sweep, {}), a.get(sweep, {})
        print(f"\n[{sweep}] 표적 {len(B)} -> {len(A)}")
        if set(B) != set(A):
            bad.append(f"{sweep}: 표적 집합이 다르다 "
                       f"(before-only={sorted(set(B)-set(A))[:5]} "
                       f"after-only={sorted(set(A)-set(B))[:5]})")
        went_dark, rule_lost, sim_wrong = [], [], []
        for k in sorted(set(B) & set(A)):
            if B[k]["reacts"] and not A[k]["reacts"]:
                went_dark.append(k)
            lost = set(B[k].get("gate_rules", [])) - set(A[k].get("gate_rules", []))
            lost |= set(B[k].get("engine_rules", [])) - set(A[k].get("engine_rules", []))
            lost -= PRUNED_RULES
            if lost:
                rule_lost.append(f"{k}: {sorted(lost)}")
            # 모의(before 실행 중에 계산한 '쳐낸 뒤') 가 실제 after 와 맞는가.
            # 안 맞으면 "append 만 하므로 정의상 같다" 는 전제가 틀린 것이다.
            if B[k].get("reacts_sim_pruned") != A[k].get("reacts"):
                sim_wrong.append(k)
        resolved = [k for k in went_dark if k in RESIDUAL_COVERED_BY_MASTER_TABLES]
        went_dark = [k for k in went_dark if k not in RESIDUAL_COVERED_BY_MASTER_TABLES]
        print(f"  반응하다 눈먼 표적 : {len(went_dark)}  {went_dark[:8]}")
        if resolved:
            print(f"  └ 이 층에서만 눈멈, **다른 층(validate_master_tables pl_bridge)이 봄**: "
                  f"{len(resolved)}  {resolved}")
        print(f"  쳐낸 룰 외 손실   : {len(rule_lost)}  {rule_lost[:8]}")
        print(f"  모의≠실제         : {len(sim_wrong)}  {sim_wrong[:8]}")
        if went_dark:
            bad.append(f"{sweep}: {len(went_dark)}개 표적이 눈멀었다 — {went_dark[:8]}")
        if rule_lost:
            bad.append(f"{sweep}: 쳐내지 않은 룰이 반응을 잃었다 — {rule_lost[:8]}")
        if sim_wrong:
            bad.append(f"{sweep}: 모의와 실제가 {len(sim_wrong)}개 표적에서 다르다 "
                       f"— 쳐내기가 CHECK 5 제거 이상의 일을 했다: {sim_wrong[:8]}")
    print(f"\n대조군: before={b.get('controls')}\n        after ={a.get('controls')}")
    print("\n" + "=" * 74)
    if bad:
        print("★ 커버리지 손실 ★")
        for x in bad:
            print("  - " + x)
        return 2
    print("커버리지 불변 확인 — 반응 집합 동일, 쳐낸 룰 외 손실 0")
    return 0


# 이번 라운드에 게이트에서 뺀 룰. 이 이름으로 반응하던 것이 사라지는 것은 **의도된 변화**다.
PRUNED_RULES = {"ANOMALY_PEER_OUTLIER", "ANOMALY_COHORT_ZERO"}

# ---------------------------------------------------------------------------
# ⚠️ 이 하니스의 **측정 범위 한계** (2026-08-25 자기정정)
# ---------------------------------------------------------------------------
# 이 하니스는 `validate_data_contract` + K-ICS 룰엔진 두 층만 잰다. 그런데 PL 항등식(브리지)·
# CSM closing identity·plausibility 는 **`scripts/validate_master_tables.py`** 에 있고, 그
# 게이트는 `tests/test_master_tables_golden.py` 를 통해 **push 경로 안에서 돈다**.
#
# 그래서 첫 측정에서 아래 4버킷이 "쳐내면 아무 룰도 안 본다" 로 나왔다 — **오판이었다.**
# 네 버킷 모두 `CSM_waterfall` 행이 아예 없어서(보증보험·소액단기 디지털손보 = PAA, CSM 워터폴
# 미공시) CSM 계열 룰이 안 도는 것뿐이고, PL 항등식은 멀쩡히 본다. 실측으로 확인:
# `scripts/_probes/probe_20260825_dark_buckets_mastertables.py`
#   서울보증보험 2026.2Q      11칸 흔듦 → 반응 [pl_bridge]
#   신한이지손해보험 2024.4Q   11칸 흔듦 → 반응 [pl_bridge]
#   신한이지손해보험 2025.4Q   23칸 흔듦 → 반응 [pl_bridge]
#   하나생명보험 2025.4Q      24칸 흔듦 → 반응 [pl_bridge]
#   (음성대조군: DB생명 2025.2Q·삼성생명 2025.4Q 는 pl_bridge+closing+plausibility 로 반응)
#
# **교훈은 이 저장소의 반복 주제 그대로다** — "룰이 0이라고 말한다 ≠ 그 축이 깨끗하다" 의
# 거울상: **"내 하니스가 무반응이라고 말한다 ≠ 아무도 안 본다."** 하니스의 검사범위부터 의심할 것.
# 새 버킷이 여기 들어오려면 반드시 같은 방식으로 **다른 층이 본다는 실측**을 붙여라.
RESIDUAL_COVERED_BY_MASTER_TABLES = {
    "서울보증보험|2026.2Q", "신한이지손해보험|2024.4Q",
    "신한이지손해보험|2025.4Q", "하나생명보험|2025.4Q",
}


if __name__ == "__main__":
    raise SystemExit(main())
