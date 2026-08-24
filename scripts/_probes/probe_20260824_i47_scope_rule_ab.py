"""item47 스코프 인식 `_tier2_branch` 의 **룰엔진 전층 A/B 시뮬레이션**.

`probe_20260824_scope_aware_bridge_sim.py` 는 다리(축 A)만 재구현해 셌다. 그 방식은
갈래 함수를 공유하는 **축 B(3_tier2_composition)·축 F(51_tfi_tier2_composition)** 의
부수효과를 못 본다 — 새 읽기를 받아들이면 그 축들이 조용히 더 관대해질 수 있다.

여기서는 룰 파일을 고치지 않고 `kics_json_rules._tier2_branch` 를 **런타임 치환**해
`run_validation` 을 두 번 돌리고, (회사, 분기, 룰) 단위로 status 전이를 전수로 센다.
게이트가 실제로 쓰는 입력(tfi_applicability 사이드카)을 그대로 쓴다.

스코프 판정은 회사 하드코딩이 아니라 **그 회사 자신의 결정적 버킷 투표**다:
  · EXCL 표 : `i3 == min(i47, i48) + i49` 만 성립  (i47 은 채무성 자본만)
  · INCL 표 : `i3 == min(i47 - i49, i48) + i49` 만 성립 (i47 이 i49 를 포함)
둘 다 성립(모호)하거나 둘 다 실패(NEITHER)면 투표에서 뺀다.

변형 3가지를 각각 돌린다:
  V1 pre-only  투표 · CONFLICT → EXCL
  V2 pre+post  투표 · CONFLICT → EXCL
  V3 pre+post  투표 · CONFLICT → INCL   (민감도: CONFLICT 처리가 결과를 바꾸는지)
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.solvency.validation import kics_json_rules as R  # noqa: E402

OUT = ROOT / "artifacts" / "validation" / "probe_20260824_i47_scope_rule_ab.txt"
TIER2_RULES = ("2_tier1_bridge", "3_tier2_composition", "51_tfi_tier2_composition")

_ORIG_BRANCH = R._tier2_branch


def _tfi_map():
    from validate_kics_disclosure import _load_tfi_applicability
    return _load_tfi_applicability()


def _decisive_votes(rows, tol_default: float):
    """(code -> Counter) 결정적 버킷만 세어 스코프 투표. pre/post 각각 따로 센다."""
    buckets = R._group_records(rows)
    vote_pre: dict[str, Counter] = defaultdict(Counter)
    vote_post: dict[str, Counter] = defaultdict(Counter)
    for b in buckets:
        # 룰엔진과 **같은** 허용오차를 쓴다(이미지 OCR 회사는 10.0). 다르면 투표가
        # 검사와 다른 잣대로 갈린다.
        tol = R.IMAGE_OCR_TOLERANCE if b.code in R.IMAGE_OCR_COMPANIES else tol_default
        for post, vote in ((False, vote_pre), (True, vote_post)):
            src = b.values_post if post else b.values
            i3, i47, i48, i49 = src.get(3), src.get(47), src.get(48), src.get(49)
            if None in (i3, i47, i48, i49):
                continue
            if max(abs(i47), abs(i48), abs(i49)) <= R.TIER2_ZERO_EPS:
                continue  # TFI_NA — 한도 메커니즘 자체가 없다
            excl = abs(i3 - (min(i47, i48) + i49)) <= tol
            incl = abs(i3 - (min(i47 - i49, i48) + i49)) <= tol
            if excl and not incl:
                vote[b.code]["EXCL"] += 1
            elif incl and not excl:
                vote[b.code]["INCL"] += 1
    return vote_pre, vote_post


def _scope_map(vote_pre, vote_post, use_post: bool, conflict: str):
    codes = set(vote_pre) | (set(vote_post) if use_post else set())
    out, conflicts = {}, []
    for code in codes:
        c = Counter(vote_pre[code])
        if use_post:
            c.update(vote_post[code])
        if c["INCL"] and not c["EXCL"]:
            out[code] = "INCL"
        elif c["EXCL"] and not c["INCL"]:
            out[code] = "EXCL"
        elif c["INCL"] or c["EXCL"]:
            out[code] = conflict
            conflicts.append((code, c["EXCL"], c["INCL"]))
    return out, conflicts


def _make_scope_branch(scope_map):
    def _branch(bucket, post, tol, target_item=3):
        src = bucket.values_post if post else bucket.values
        i3 = src.get(target_item)
        i47, i48, i49 = src.get(47), src.get(48), src.get(49)
        if None in (i3, i47, i48, i49):
            return _ORIG_BRANCH(bucket, post, tol, target_item)
        if scope_map.get(bucket.code) != "INCL":
            return _ORIG_BRANCH(bucket, post, tol, target_item)
        debt = i47 - i49
        capped = abs(i3 - (min(debt, i48) + i49)) <= tol
        uncapped = abs(i3 - i47) <= tol
        if capped and uncapped:
            return "BOTH", max(0.0, debt - i48)
        if capped:
            return "CAPPED_INCL", max(0.0, debt - i48)
        if uncapped:
            return "UNCAPPED", 0.0
        return _ORIG_BRANCH(bucket, post, tol, target_item)
    return _branch


def _sig(findings):
    return {(f["원보험사코드"], f["공시분기"], f["rule"]):
            (f["status"], f.get("diff"), f.get("detail", "")) for f in findings}


def main():
    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    tfi = _tfi_map()
    tol = R.DEFAULT_TOLERANCE if hasattr(R, "DEFAULT_TOLERANCE") else 2.0

    base = _sig(R.run_validation(rows, tfi_applicability=tfi)["findings"])
    vote_pre, vote_post = _decisive_votes(rows, tol)

    lines = [f"tolerance = {tol}", ""]
    lines.append("=== 회사별 결정적 투표 (pre / post) ===")
    lines.append(f"{'code':<8}{'pre EXCL':>9}{'pre INCL':>9}{'post EXCL':>10}{'post INCL':>10}")
    for code in sorted(set(vote_pre) | set(vote_post)):
        p, q = vote_pre[code], vote_post[code]
        if not (p["EXCL"] or p["INCL"] or q["EXCL"] or q["INCL"]):
            continue
        lines.append(f"{code:<8}{p['EXCL']:>9}{p['INCL']:>9}{q['EXCL']:>10}{q['INCL']:>10}")
    lines.append("")

    for label, use_post, conflict in (("V1 pre-only, CONFLICT->EXCL", False, "EXCL"),
                                      ("V2 pre+post, CONFLICT->EXCL", True, "EXCL"),
                                      ("V3 pre+post, CONFLICT->INCL", True, "INCL")):
        smap, conflicts = _scope_map(vote_pre, vote_post, use_post, conflict)
        incl = sorted(c for c, s in smap.items() if s == "INCL")
        lines.append(f"=== {label} ===")
        lines.append(f"  INCL 사 {len(incl)}: {incl}")
        lines.append(f"  CONFLICT 사 {len(conflicts)}: "
                     f"{[(c, e, i) for c, e, i in sorted(conflicts)]} -> {conflict}")
        R._tier2_branch = _make_scope_branch(smap)
        try:
            new = _sig(R.run_validation(rows, tfi_applicability=tfi)["findings"])
        finally:
            R._tier2_branch = _ORIG_BRANCH

        assert set(base) == set(new), "finding 키 집합이 달라졌다 — 룰 발화 자체가 변했다"
        trans = Counter()
        detail_only = Counter()
        changes = []
        for k in sorted(base):
            (s0, d0, t0), (s1, d1, t1) = base[k], new[k]
            rule = k[2]
            if s0 != s1:
                trans[(rule, s0, s1)] += 1
                changes.append(f"    {k[0]} {k[1]:<8} {rule:<28} {s0} -> {s1}  "
                               f"diff {d0} -> {d1}")
            elif (d0 or 0) != (d1 or 0):
                detail_only[(rule, s0)] += 1
                changes.append(f"    {k[0]} {k[1]:<8} {rule:<28} {s0} (동일)  "
                               f"diff {d0} -> {d1}")
        lines.append(f"  status 전이 {sum(trans.values())} 건:")
        for (rule, s0, s1), n in sorted(trans.items()):
            lines.append(f"    {rule:<30} {s0:>6} -> {s1:<6} {n}")
        lines.append(f"  status 동일 + diff 변화 {sum(detail_only.values())} 건:")
        for (rule, s0), n in sorted(detail_only.items()):
            lines.append(f"    {rule:<30} {s0:>6} {n}")
        lines.append("  변화 셀 전량:")
        lines.extend(changes if changes else ["    (없음)"])

        agg0 = Counter(v[0] for k, v in base.items() if k[2].split("_post")[0] in
                       [r for r in TIER2_RULES])
        agg1 = Counter(v[0] for k, v in new.items() if k[2].split("_post")[0] in
                       [r for r in TIER2_RULES])
        lines.append(f"  tier2 축 3종 status 집계  before={dict(agg0)}  after={dict(agg1)}")
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    print("\n".join(lines[-40:]))


if __name__ == "__main__":
    main()
