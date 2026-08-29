"""Drop the 12 코리안리재보험 leg-coverage entries from pl_bridge_baseline.json.

They were registered on 2026-08-29 when the leg-coverage rule was created, on the
belief that a missing item13(자동차) leg was carrying real money.  It was not: the
source has no 자동차 LOB at all (parser verified every quarter's raw XML, commit
15a61d1) and the residual was entirely the validator's own missing term — the
extra-LOB slot item"2-1"(장기재보험 손익), which the builder already published and
already folded into its Tier-2 RC gate.  With that term wired into the equation the
gate prints all 12 as FIXED?, so the `_promote` contract says delete the rows.

Also recomputes `_counts` from the actual entries — it had drifted (declared 52 vs
actual 47 after the parser's 서울보증 round removed 5 without updating it).

Run once:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/fix_20260829_baseline_drop_coreanre.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "data/_gold/pl_bridge_baseline.json"

NOTE = (
    "inbox/parser/20260829T1700Z__validation__MULTI__pl_item1_leg_coverage.md §2 회신 처리"
    "(validation). **어제 신설한 leg-coverage 룰의 오탐이었다.** 룰은 코리안리재보험 12분기를 "
    "'item13(자동차) 결측이 1,456~53,464백만원을 싣고 있다'고 찍었지만, parser 가 전 분기 원문 "
    "XML 을 grep 한 결과 '자동차'는 재무제표 표 안에 단 한 번도 없다(전부 관계기업 펀드명·임원 "
    "이력 문장의 우연한 문자열 일치) — 코리안리는 재보험사라 LOB 이 생명/장기/일반 3종이고 "
    "자동차를 영위하지 않는다. 결함은 데이터가 아니라 **등식**이었다: 코리안리의 네 번째 LOB "
    "다리인 item'2-1'(장기재보험 손익)이 마스터에 정상 발행돼 있고 빌더의 Tier-2 RC 게이트도 "
    "이미 `_extra_lob` 으로 더하고 있었는데, validate_master_tables 의 leg-coverage 등식만 "
    "표준 3슬롯(2/13/14)이 LOB 의 전부라고 가정했다 — **빌더와 검증기가 서로 다른 등식을 "
    "쓰고 있었다.** 조치: `load_pl_extra_lob()` 신설 + 등식에 Σ항목번호 `2-N` 가산(회사명 "
    "하드코딩이 아니라 번호 패턴 — 다음 재보험사에서 같은 사각이 재발하지 않게). 자식 "
    "`3-N`~`12-N` 은 그 다리의 하위 분해라 더하지 않는다(이중계상). 실측: 12분기 전부 "
    "|잔차| ≤ 2.8백만원(대부분 <1.3), 2023.1Q/2Q 는 item1 자체가 결측이라 NOLHS 유지. "
    "전 버킷 시뮬레이션(scripts/_probes/probe_20260829_extra_lob_simulation.py, 356 버킷): "
    "새로 깨지는 버킷 0건, leg-coverage 닫힘 18->30 · 깨짐 34->22, pl_bridge 3045P/47F -> "
    "3057P/35F. 그래서 아래 12줄을 `_promote` (1) 에 따라 삭제한다."
)


def main() -> None:
    d = json.loads(P.read_text(encoding="utf-8"))
    entries = d["entries"]
    drop = [k for k in entries if k.startswith("코리안리재보험|")
            and k.endswith("|보험손익(leg-coverage)")]
    print(f"entries before: {len(entries)}")
    for k in drop:
        print("  DROP", k, "->", entries[k].get("class"))
        del entries[k]
    print(f"entries after:  {len(entries)}  (dropped {len(drop)})")

    counts = Counter(v.get("class", "?") for v in entries.values())
    old = d.get("_counts")
    d["_counts"] = {**dict(sorted(counts.items())), "entries": len(entries)}
    print(f"_counts  old={old}\n         new={d['_counts']}")

    d["_round_20260829_legcoverage_fix"] = NOTE
    # indent=1 은 이 파일의 기존 서식이다 — indent=2 로 쓰면 전 줄이 재들여쓰기돼
    # 12줄 삭제가 415+/559- 짜리 리뷰 불가 diff 로 부풀었다(실측 후 되돌림).
    P.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {P}")


if __name__ == "__main__":
    main()
