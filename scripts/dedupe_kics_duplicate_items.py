# -*- coding: utf-8 -*-
"""같은 (회사, 분기, 항목번호) 에 행이 두 개 생긴 것을 하나로 합친다.

**왜 생겼나.** 이 저장소의 알려진 함정 — 항목명에 표기 변형이 있다.
`다. 지급여력비율 : 가 ÷ 나 × 100`(489행)과 `지급여력비율`(68행)이 같은 item27 이고,
`7. 조정준비금`(537행)과 `6. 조정준비금`(2행)이 같은 item11 이다. 로더가 라벨로 기존 행을
찾다 못 찾으면 **갱신 대신 새 행을 만든다.** 2026.2Q 라운드 실측 20콤보.

**왜 지금 고쳐야 하나.** 중복이 있으면 `apply_2026q2_patches.py` 의 범위감사가 오탐한다 —
`before` 스냅샷이 dict 라 중복 콤보는 마지막 행만 남고, 적용 후 비교에서 다른 행이
"범위 밖 변경" 으로 잡혀 **저장 자체를 거부한다.** 실제로 KR0079 OCR 정정 패치가 이것 때문에
반영되지 않았다(범위 밖 변경 19건 전부 item27 중복).

**병합 규칙** (삭제가 아니라 병합이다):
  1. `값` 의 유효숫자가 더 많은 행을 남긴다 — 반올림본(223.5)보다 원값(223.48759875).
  2. 남긴 행에 `값_적용후` 가 없고 버릴 행에 있으면 가져온다.
  3. 둘 다 `값_적용후` 가 있는데 다르면 **건드리지 않고 보고만 한다**(사람 판단).
  4. 항목명은 남긴 행 것을 그대로 둔다 — 회사별 표기 변형은 정당하다.

사용:
  python scripts/dedupe_kics_duplicate_items.py            # dry-run, 전건 열거
  python scripts/dedupe_kics_duplicate_items.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "kics_disclosure.json"
VAL, VAL_POST = "값", "값_적용후"


def sig(v) -> int:
    """유효숫자 개수. 반올림본과 원값을 가른다."""
    if v in (None, "", "None"):
        return -1
    s = str(v).replace("-", "").replace(",", "")
    return len(s.replace(".", "").lstrip("0"))


def has_post(r) -> bool:
    return r.get(VAL_POST) not in (None, "", "None")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    before_n = len(rows)
    groups = defaultdict(list)
    for i, r in enumerate(rows):
        groups[(r.get("원보험사코드"), r.get("공시분기"), int(r["항목번호"]))].append(i)

    drop, conflicts = set(), []
    for key, idxs in sorted(groups.items()):
        if len(idxs) < 2:
            continue
        cand = sorted(idxs, key=lambda i: (sig(rows[i].get(VAL)), has_post(rows[i])), reverse=True)
        keep, rest = cand[0], cand[1:]
        k = rows[keep]
        print("%s %s item%d  (%d행)" % (key[0], key[1], key[2], len(idxs)))
        print("   KEEP  %-34s 값=%-16s 후=%s" % (str(k.get("항목명"))[:34], k.get(VAL), k.get(VAL_POST)))
        for i in rest:
            r = rows[i]
            print("   DROP  %-34s 값=%-16s 후=%s" % (str(r.get("항목명"))[:34], r.get(VAL), r.get(VAL_POST)))
            if not has_post(k) and has_post(r):
                k[VAL_POST] = r[VAL_POST]
                print("         -> 값_적용후 %s 를 KEEP 행으로 이관" % r[VAL_POST])
            elif has_post(k) and has_post(r) and str(k[VAL_POST]) != str(r[VAL_POST]):
                conflicts.append((key, k[VAL_POST], r[VAL_POST]))
                print("         !! 값_적용후 불일치 (%s vs %s) — 사람 판단 필요" % (k[VAL_POST], r[VAL_POST]))
            drop.add(i)

    print("\n중복 %d콤보 · 제거 대상 %d행 · 값_적용후 충돌 %d건"
          % (sum(1 for v in groups.values() if len(v) > 1), len(drop), len(conflicts)))
    if conflicts:
        print("충돌은 KEEP 행 값을 유지했다. 전건:")
        for key, a, b in conflicts:
            print("   %s %s item%d: keep=%s drop=%s" % (key[0], key[1], key[2], a, b))

    kept = [r for i, r in enumerate(rows) if i not in drop]
    assert len(kept) == before_n - len(drop), "행수 산술 불일치"
    # 병합 후 중복이 정말 0 인지 재검
    again = defaultdict(int)
    for r in kept:
        again[(r.get("원보험사코드"), r.get("공시분기"), int(r["항목번호"]))] += 1
    left = sum(1 for v in again.values() if v > 1)
    print("병합 후 남은 중복 콤보: %d" % left)
    if left:
        print("아직 중복이 남았다 — 저장하지 않는다.")
        return 2

    if not args.apply:
        print("\n(dry-run — 실제로 쓰려면 --apply)")
        return 0
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(MASTER, MASTER.with_suffix(".json.bak_%s_dedupe" % stamp))
    MASTER.write_text(json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n행수 %d -> %d 저장 완료" % (before_n, len(kept)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
