"""gold 오버레이의 **중복 키**를 제거한다 (validation, 2026-08-30).

## 왜

`build_root_masters._apply_csm_overrides()` / `_apply_pl_overrides()` 는 gold `set` 을
리스트 순서대로 순회하며 UPSERT 한다 = **last-wins**. 같은 (코드, 항목, 분기) 가 두 번
들어 있으면 **정합성이 리스트 순서에 걸린다** — 누가 정렬하거나 dedup 하거나 diff 를
잘못 머지하면 조용히 앞 엔트리가 이기고, 화면 숫자가 뒤집힌다. 게이트는 아무 말도 안 한다.

실측 중복 7건:

  · `user_csm_cells.json` — KR0076(아이엠라이프) 2025.4Q 항목1~6, **6건**.
    앞(2026-06-11)은 '유배당외' 표만 합산했고, 뒤(2026-08-25, `why` 있음)가 '유배당' 표를
    더해 재도출한 정정본이다. 뒤 엔트리의 `why` 가 앞 엔트리를 명시적으로 지목한다
    ("이 파일의 위 2025.4Q 항목 6개").
  · `user_pl_cells.json` — KR0087 2025.3Q 항목11, **1건**.
    앞(2026-06-19/20 owner xlsx fill, 값=0.0)을 뒤(2026-08-15, 값=null)가 raw 재확인으로
    뒤집었다("7,026 숫자도 raw 에 없음" → 0 대신 null 로 명시).

두 경우 모두 **뒤가 이기는 것이 옳다.** 그래서 앞 엔트리만 지운다 — 값은 한 칸도 안 바뀐다.
지워진 값은 살아남는 엔트리의 `was` 필드에 이미 기록돼 있어 이력도 안 잃는다.

## 안전장치

적용 전후로 `_apply_*_overrides` 와 **같은 last-wins 축약**을 돌려 (키 → 값) 사전이
완전히 동일한지 확인한다. 다르면 아무것도 안 쓰고 죽는다.

실행:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
      scripts/_probes/fix_20260830_gold_overlay_dedup.py [--apply]
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    ROOT / "data" / "_gold" / "user_csm_cells.json",
    ROOT / "data" / "_gold" / "user_pl_cells.json",
]
STAMP = "bak_20260830_dedup"


def key(e):
    return (e["원보험사코드"], e["항목번호"], e["공시분기"])


def last_wins(entries):
    """`_apply_csm_overrides` / `_apply_pl_overrides` 와 같은 축약: 뒤가 이긴다."""
    out = {}
    for e in entries:
        out[key(e)] = e.get("값")
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    apply = "--apply" in argv
    rc = 0
    for path in TARGETS:
        doc = json.loads(path.read_text(encoding="utf-8"))
        entries = doc.get("set", [])
        before = last_wins(entries)

        seen_last = {}
        for i, e in enumerate(entries):
            seen_last[key(e)] = i           # 마지막 등장 위치
        keep_idx = {i for i in seen_last.values()}
        dropped = [(i, entries[i]) for i in range(len(entries)) if i not in keep_idx]

        print(f"\n{path.name}: {len(entries)} entries, 중복으로 지울 앞 엔트리 {len(dropped)}건")
        for i, e in dropped:
            k = key(e)
            print(f"  drop idx={i:<4} {k}  값={e.get('값')!r}  -> 살아남는 값={before[k]!r}")

        if not dropped:
            print("  (중복 없음)")
            continue

        new_entries = [e for i, e in enumerate(entries) if i in keep_idx]
        after = last_wins(new_entries)
        if after != before:
            diff = {k: (before.get(k), after.get(k)) for k in set(before) | set(after)
                    if before.get(k) != after.get(k)}
            print(f"  [!] 축약 결과가 바뀐다 — 중단. diff={diff}")
            rc = 2
            continue
        print(f"  축약 동일 확인: {len(before)} 키, 값 변화 0")

        if not apply:
            print("  (dry-run — 쓰지 않았다. --apply 로 실행)")
            continue
        bak = path.with_suffix(path.suffix + "." + STAMP)
        if not bak.exists():
            shutil.copy2(path, bak)
        doc["set"] = new_entries
        # 두 파일 다 후행 개행이 없고 indent=2 로 정확히 왕복한다(실측) — 그대로 맞춰 쓴다.
        # 개행 하나 붙이면 diff 가 파일 전체로 번져 리뷰가 못 읽는다.
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  wrote {path.name}: {len(new_entries)} entries (backup {bak.name})")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
