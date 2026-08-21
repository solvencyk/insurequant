# -*- coding: utf-8 -*-
"""원문 '생명·장기손해보험위험액 현황' 표엔 값이 있는데 마스터가 0 으로 적재한 하위위험 셀.

validation inbox `20260821T0010Z` 축 A 감사 중 발견. 전수 스캔
(`scripts/_probes/probe_item29_zero.py`: item29전=0 인 전 셀에 대해 원문 충격후평가금액 표의
사망위험 행을 확인)에서 **1건**만 나왔다.

  KR0010 KB손해보험 2023.2Q item29(사망위험액) = 0
    raw p16 [생명・장기손해보험위험액-대재해위험 이외] 충격후평가금액 사망위험
    Ⅰ.생명보험 0 / Ⅱ.장기손해보험 258,369 / Ⅲ.총계 258,369 (백만원) = 2,583.69억
    반영 시 R7 재현 55,288.99 → 55,786.88 (공시 55,948). 잔차 161억(0.29%)은 원문 자체가
    안 닫히는 부분이라 더 줄지 않는다. KB손해는 비적용사이므로 적용후도 같은 값.

Usage: ...python scripts/fix_20260821_missing_life_subs.py [--dry-run]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TARGET = REPO / "kics_disclosure.json"

# (code, quarter, item) -> (컬럼, 기대 현재값, 새 값). 현재값이 다르면 건너뛴다(이미 고쳐진 셀 보호).
#   "값" 을 고치는 비적용사 셀은 적용후도 같이 맞춘다(전=후).
FIXES = {
    ("KR0010", "2023.2Q", 29): ("값", "0", "2583.69"),
    # KB라이프생명 2026.1Q — 공통TFI(기발행 자본증권 인정범위 확대)가 보완자본 2,307,119 →
    # 2,257,319 백만으로 재분류하는데(raw p21) item3후가 적용전 그대로였다. item2후는 이미
    # 38,163(=37,665+498)로 반영돼 있어 R1(item1후 = item2후 + item3후)이 498억 안 맞았다.
    ("KR0099", "2026.1Q", 3): ("값_적용후", "23071", "22573.19"),
    # 삼성화재 2023.2Q item29(사망위험) = 0 저장. raw p16 [생명·장기손해보험위험액-대재해위험
    # 이외] 충격후평가금액 사망위험 554,466백만 = 5,544.66억. R7 재현 57,050.44 → 58,127.4978
    # (공시 58,127) 로 **정확히** 닫힌다.
    ("KR0008", "2023.2Q", 29): ("값", None, "5544.66"),   # 행 자체가 없었다
    # 동양생명 2024.2Q item35(대재해위험) 행 자체가 없었다. raw p17 [생명·장기손해보험위험액-
    # 대재해위험] 익스포져 88,493,883 / 대재해위험액 88,494백만 = 884.94억. R7 재현
    # 17,747.18 → 18,084.73 (공시 18,090, 잔차 5.27 = 원문 자체 반올림).
    ("KR0087", "2024.2Q", 35): ("값", None, "884.94"),
}


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    done, skip = [], []
    # guard 가 None 인 항목은 '행 자체가 없어야 정상' — 없으면 형제 행에서 메타를 복사해 신설한다.
    present = {(r.get("원보험사코드"), r.get("공시분기"), int(r.get("항목번호", -1))) for r in data}
    label_of = {}
    for r in data:
        try:
            label_of.setdefault(int(r["항목번호"]), r.get("항목명", ""))
        except (TypeError, ValueError, KeyError):
            pass
    for key, (col, guard, new) in FIXES.items():
        if guard is not None or key in present:
            continue
        c, q, it = key
        sib = next((r for r in data if r["원보험사코드"] == c and r["공시분기"] == q), None)
        if sib is None:
            skip.append((*key, "형제 행 없음(회사·분기 미존재)"))
            continue
        row = {"원보험사코드": c, "원수사명": sib.get("원수사명", c), "티커": sib.get("티커", "X"),
               "생손보여부": sib.get("생손보여부", ""), "항목번호": it,
               "항목명": label_of.get(it, ""), "공시분기": q, "값": new, "값_적용후": new}
        idxs = [i for i, r in enumerate(data)
                if r["원보험사코드"] == c and r["공시분기"] == q]
        at = max(idxs) + 1
        for i in idxs:
            if int(data[i]["항목번호"]) > it:
                at = i
                break
        data.insert(at, row)
        done.append((*key, "(행 신설)", new, col))
    for r in data:
        key = (r.get("원보험사코드"), r.get("공시분기"), int(r.get("항목번호", -1)))
        if key not in FIXES:
            continue
        col, guard, new = FIXES[key]
        if guard is None:
            continue                    # 위에서 신설 처리됨
        cur = r.get(col)
        if cur != guard:
            skip.append((*key, f"{col} 현재값 {cur!r} != guard {guard!r}"))
            continue
        done.append((*key, cur, new, col))
        if not dry:
            r[col] = new
            if col == "값":
                r["값_적용후"] = new      # 비적용사 → 적용후 = 적용전
    print(f"{'DRY-RUN ' if dry else ''}적용 {len(done)} · 건너뜀 {len(skip)}")
    for c, q, it, cur, new, col in done:
        print(f"  {c} {q} item{it} [{col}]: {cur} -> {new}")
    for c, q, it, why in skip:
        print(f"  skip {c} {q} item{it}: {why}")
    if not dry and done:
        TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
