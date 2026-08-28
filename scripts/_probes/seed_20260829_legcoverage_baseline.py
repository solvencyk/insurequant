"""Seed data/_gold/pl_bridge_baseline.json with the 40 failures newly EXPOSED (not caused)
by the 2026-08-29 보험손익 leg-coverage rule.

Ticket: inbox/validation/20260829T1500Z__orchestrator__MULTI__insurance_result_closure_missing.md

These cells were failing all along; before today the gate SKIPped them because a LOB leg was
None. Registering them per-cell (not a blanket skip) keeps the repo's established contract:
they still count as F in SUMMARY and keep exit=2, and any failure NOT listed here shows up as
`pl_bridge:...NEW` so the golden blocks the push.

Run once. Re-running is idempotent (existing keys are left untouched).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "data" / "_gold" / "pl_bridge_baseline.json"
SEED = ROOT / "scripts" / "_probes" / "_tmp_legcoverage_seed.json"

FIRST_SEEN = "2026-08-29"
DEADLINE = "2026-10-31"

# 이미 owner/parser 가 "LOB 분해 자체를 미공시" 로 확정한 회사들
# (validate_master_tables._check_pl_bridge 의 ZLEG_LEGIT "ALL" 과 같은 집합).
ZLEG_ALL = {"서울보증보험", "AIG손해보험", "신한이지손해보험", "교보라이프플래닛생명보험"}

CLASS_NOTE = {
    "lob_split_not_extracted":
        "item2·13·14 세 다리가 모두 결측이라 item1 을 분해하는 성분이 마스터에 하나도 없다"
        " — 잔차가 item1 전액과 같다(0-fill 하면 우변이 기타영업수익/기타사업비용만 남는다)."
        " 즉 '등식이 깨졌다'기보다 '분해가 통째로 없다'에 가깝지만, 종전처럼 SKIP 으로 감추지"
        " 않고 건별로 세운다. 원천이 정말 미공시인지(=documented exception 승격 대상인지)"
        " 아니면 추출 누락인지는 raw 로 확정해야 한다.",
    "single_leg_gap_자동차":
        "item13(자동차)만 결측이고 item14(일반)는 정상 추출돼 있다. 같은 표에서 형제 다리가"
        " 나오는데 이것만 없다 — 회사 카테고리로 '자동차 미영위' 라 단정하지 말고 raw 확인 요망"
        " (코리안리재보험은 13분기 내내 동일 패턴).",
    "single_leg_gap_생명장기":
        "item2(생명장기)만 결측. 상위 item1 은 있는데 그 최대 성분이 없다.",
    "single_leg_gap_자동차_일반":
        "item13·14 가 함께 결측(item2 는 정상). 현대해상 2024.1Q~2025.2Q 는 같은 사유로"
        " ZLEG_LEGIT_CQ 에 이미 분기단위 legit 등재돼 있다 — 2023.3Q 도 같은 OLD form 인지"
        " 확인 요망.",
}


def classify(missing: list[str]) -> str:
    s = set(missing)
    if s == {"생명장기손익", "자동차손익", "일반손익"}:
        return "lob_split_not_extracted"
    if s == {"자동차손익"}:
        return "single_leg_gap_자동차"
    if s == {"생명장기손익"}:
        return "single_leg_gap_생명장기"
    if s == {"자동차손익", "일반손익"}:
        return "single_leg_gap_자동차_일반"
    return "single_leg_gap_기타"


def main() -> None:
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    entries = base["entries"]

    added = 0
    for key, row in sorted(seed.items()):
        if key in entries:
            continue
        co = key.split("|")[0]
        cls = classify(row["missing_legs"])
        reason = (
            f"2026-08-29 보험손익 leg-coverage 룰 신설로 **처음 검사 대상이 된** 셀"
            f"(종전에는 결측 다리 때문에 통째 SKIP — 356 버킷 중 71 이 그 상태였다). "
            f"결측 다리 = {', '.join(row['missing_legs'])}. 그 다리를 0 으로 채우면 "
            f"1 = 2+13+14(+15-16) 이 {row['diff']:+.1f} 백만원 만큼 안 닫힌다 — 즉 결측 다리가 "
            f"최소 그만큼의 금액을 싣고 있고, 그 금액을 지금까지 어떤 룰도 보지 않았다. "
            f"{CLASS_NOTE[cls]}"
        )
        if co in ZLEG_ALL:
            reason += (
                f" | 참고: {co} 는 이미 _check_pl_bridge 의 ZLEG_LEGIT 에 'ALL'(생명장기 분해 "
                f"미공시)로 등재된 회사다. 그 등재는 생명장기 sub-leg 에 대한 것이고 이 등식의 "
                f"13/14 결측까지 면제하지는 않는다 — 승격하려면 LOB 분해 미공시를 raw 로 확인해 "
                f"별도로 문서화해야 한다."
            )
        entries[key] = {
            "class": cls,
            "reason": reason,
            "route": "parser/ifrs17",
            "lhs": row["lhs"],
            "diff": row["diff"],
            "missing_legs": row["missing_legs"],
            "first_seen": FIRST_SEEN,
            "deadline": DEADLINE,
        }
        added += 1

    # counts
    counts: dict[str, int] = {}
    for e in entries.values():
        counts[e["class"]] = counts.get(e["class"], 0) + 1
    counts["entries"] = len(entries)
    base["_counts"] = counts

    base["_round_20260829_legcoverage"] = (
        "inbox/validation/20260829T1500Z__orchestrator__MULTI__insurance_result_closure_missing.md "
        "처리(validation). 발주는 '보험손익 폐쇄식(1=2+13+14+15-16)이 PL_EQS 에 없다'였는데 "
        "실측하면 **있다** — PL_EQS 밖의 dual-form 블록이 파일 최초 커밋(135e6ff)부터 그 등식을 "
        "검사하고 있고, 그 실패 10건은 이미 이 등재부에 있었다(라벨 '보험손익(dual)'). "
        "진짜 사각은 등식의 부재가 아니라 **결측 시 통째 SKIP** 이었다: item1/2/13/14 중 하나라도 "
        "None 이면 그 버킷의 보험손익은 무검사였고, 356 버킷 중 71(19.9%)이 그 상태였다. "
        "게다가 coverage census 의 key_items 는 보험손익/생명장기손익/당기순이익 셋뿐이라 "
        "**13(자동차)·14(일반)의 결측은 세지도 않는다** — 두 검사가 같은 구멍을 공유했다. "
        "실측 대표사례: 코리안리재보험은 13분기 내내 item13 이 없는 채로 두 검사를 모두 통과했고, "
        "0-fill 로 재보면 2024+ 10분기가 전부 안 닫힌다(잔차 1,456~41,051백만). "
        "조치: 결측 LOB 다리를 0 으로 채워 판정하는 leg-coverage 룰 신설(라벨 "
        "'보험손익(leg-coverage)'). 닫히면 PASS(그 다리는 정말 0), 깨지면 FAIL. "
        "전 버킷 시뮬레이션(scripts/_probes/probe_20260829_item1_legcoverage_final.py): "
        "오늘 검사받던 285 버킷 판정 변화 0건(regression 0), SKIP 71->18 · PASS 275->288 · "
        "FAIL 10->50. 남은 SKIP 18 은 item1 자체가 결측이라 좌변이 없는 경우(전건 2023 분기, "
        "coverage census 소관)이며 NOLHS 로 건별 인쇄한다. 아래 40 개 leg-coverage 엔트리는 "
        "**이 룰이 만든 결함이 아니라 드러낸 결함**이다 — 전건 parser/ifrs17 라우팅, "
        "발주 티켓 inbox/parser/20260829T1700Z__validation__MULTI__pl_item1_leg_coverage.md."
    )

    BASELINE.write_text(json.dumps(base, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"added={added}  entries={len(entries)}")
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
