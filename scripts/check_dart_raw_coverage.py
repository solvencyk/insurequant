#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DART raw 커버리지 high-water-mark 검사 — 받아 놓은 원문이 조용히 사라지는 것을 잡는다.

왜 있나 (2026-08-25, `inbox/downloader/20260825T0001Z`)
------------------------------------------------------
parser(ifrs17)가 `PL_breakdown.json` census 로 KB손해보험 2024.3Q~2025.3Q 5개 분기가
통째로 비어 있는 것을 발견했다. 조사해 보니 **원천 부재도 negative cache 도 아니고,
디스크에 있던 raw 가 사라진 것**이었다:

* `data/dart/_inventory_manifest.json` (2026-05-30 디스크 스냅샷) 은 그 5개 분기를
  zip 바이트 크기까지 기록하고 있었다.
* 오늘 재취득한 zip 이 **그 바이트 크기와 정확히 일치**했다 — 같은 파일이 한 번 있었고
  사라졌다는 뜻이다.
* 같은 창(2024.3Q~2025.1Q)에서 손보 8개사가 함께 비어 있었다 — KB 만의 문제가 아니었다.

`data/dart/**/raw/` 는 `.gitignore` 대상이라 **git 으로는 복구도 탐지도 안 된다.**
그래서 3개월 가까이 아무도 몰랐고, 다른 레인의 census 가 우연히 건드려서 드러났다.
이 검사기는 그 사각을 메운다: 한 번이라도 디스크에 있었던 (period, 회사) 칸을
baseline 에 박제해 두고, 이후 그 칸이 사라지면 **push 를 막는다.**

계약
----
* 칸의 정의 = `data/dart/FY<Y>_Q<q>/raw/<dir>/document.zip` 이 존재하고 PK 매직으로
  시작하는 것. 빈 껍데기(`meta.json` 만 있고 `no_filing: true`)는 칸이 아니다.
* baseline 은 **줄어들지 않는다**(high-water mark). `--update` 는 합집합만 한다.
* 진짜로 지워야 하는 칸(원천이 오문서였다 등)은 `known_absent` 에 **사유와 함께**
  옮긴다 — 조용히 baseline 에서 빼는 경로는 없다.
* raw 가 통째로 없는 트리(main slim 워크트리 등)에서는 검사하지 않고 통과한다.

Usage
-----
  python scripts/check_dart_raw_coverage.py            # 검사 (exit 1 = 유실 있음)
  python scripts/check_dart_raw_coverage.py --update   # 현재 디스크를 baseline 에 합침
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
DART = ROOT / "data" / "dart"
BASELINE = DART / "_raw_coverage_baseline.json"
PERIOD_RE = re.compile(r"^FY\d{4}_Q\d$")


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def scan_disk() -> dict[str, int]:
    """{"FY2024_Q3/KR0010_KB손해보험": <zip bytes>} — 유효한 document.zip 만."""
    cells: dict[str, int] = {}
    for period in sorted(DART.glob("FY*_Q*")):
        if not (period.is_dir() and PERIOD_RE.match(period.name)):
            continue
        raw = period / "raw"
        if not raw.is_dir():
            continue
        for d in sorted(raw.iterdir()):
            if not d.is_dir():
                continue
            z = d / "document.zip"
            if not z.is_file():
                continue
            size = z.stat().st_size
            if size <= 0:
                continue
            with z.open("rb") as fh:
                if fh.read(4) != b"PK\x03\x04":
                    continue
            cells[f"{period.name}/{d.name}"] = size
    return cells


def load_baseline() -> dict:
    if not BASELINE.is_file():
        return {"cells": {}, "known_absent": {}}
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def write_baseline(data: dict) -> None:
    BASELINE.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
                        encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DART raw high-water-mark coverage check")
    ap.add_argument("--update", action="store_true",
                    help="현재 디스크 상태를 baseline 에 합친다(합집합만, 절대 줄이지 않음)")
    args = ap.parse_args(argv)

    disk = scan_disk()
    if not disk:
        print("[dart-raw-coverage] data/dart/FY*/raw 에 zip 이 하나도 없다 "
              "— slim 워크트리로 보고 검사를 건너뛴다.")
        return 0

    base = load_baseline()
    cells: dict[str, int] = base.get("cells", {})
    known_absent: dict[str, str] = base.get("known_absent", {})

    if args.update:
        merged = dict(cells)
        added = []
        for k, v in disk.items():
            if k not in merged:
                added.append(k)
            merged[k] = v
        base["cells"] = dict(sorted(merged.items()))
        base["known_absent"] = known_absent
        base["generated_at"] = _stamp()
        base.setdefault(
            "note",
            "high-water mark of DART raw cells ever seen on disk. data/dart/**/raw/ is "
            "gitignored, so git can neither detect nor recover a deletion — this file is the "
            "only detector. Never shrink it by hand; move an intentionally-dropped cell to "
            "known_absent with a reason. See scripts/check_dart_raw_coverage.py.",
        )
        write_baseline(base)
        print(f"[dart-raw-coverage] baseline updated: {len(base['cells'])} cells "
              f"(+{len(added)} new), known_absent={len(known_absent)}")
        for k in added[:20]:
            print(f"    + {k}")
        if len(added) > 20:
            print(f"    ... (+{len(added) - 20} more)")
        return 0

    if not cells:
        print("[dart-raw-coverage] baseline 이 비어 있다 — 먼저 --update 로 씨를 뿌려라.")
        return 0

    missing = sorted(k for k in cells if k not in disk and k not in known_absent)
    print(f"[dart-raw-coverage] baseline={len(cells)} disk={len(disk)} "
          f"known_absent={len(known_absent)} missing={len(missing)}")
    if known_absent:
        for k, why in sorted(known_absent.items()):
            print(f"    (known absent) {k}: {why}")
    if missing:
        print("  RED — 한 번 받아 놓았던 raw 가 디스크에서 사라졌다:")
        for k in missing:
            print(f"    - {k}  (was {cells[k]} bytes)")
        print("  → 재취득: scripts/ifrs17_batch_historical.py --pilot <KR> --periods <라벨> "
              "--skip-extract  후 scripts/extract_dart_zips.py")
        print("  → 의도적으로 뺀 칸이면 baseline 의 known_absent 로 사유와 함께 옮겨라.")
        return 1
    print("  clear — 유실 없음.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
