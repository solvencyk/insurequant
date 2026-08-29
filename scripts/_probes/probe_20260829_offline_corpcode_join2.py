# -*- coding: utf-8 -*-
"""2차: `data/_derived/alotmatter_fetch_census.json`(**git 추적**) 의 KR코드->corp_code 매핑이
`fetch_dart_fs.resolve_corp()`(CORPCODE.xml, gitignore + 네트워크 폴백) 와 같은가.

같으면 게이트는 네트워크·gitignore 파일 없이 FS-API 캐시를 결정적으로 붙일 수 있다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_dart_fs as F  # noqa: E402


def main():
    cen = json.loads((ROOT / "data" / "_derived" / "alotmatter_fetch_census.json")
                     .read_text(encoding="utf-8"))
    kr2cc: dict[str, str] = {}
    for c in cen.get("cells", []):
        if c.get("kr") and c.get("corp_code"):
            kr2cc.setdefault(c["kr"], c["corp_code"])
    print(f"census KR->corp_code: {len(kr2cc)} 개 (universe_total={cen.get('universe_total')}, "
          f"unresolved={cen.get('unresolved')})")

    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    pairs = sorted({(r["원보험사코드"], r["원수사명"]) for r in rows})
    print(f"PL 마스터 회사: {len(pairs)} 개\n")

    ok = miss = mismatch = 0
    cache = ROOT / "data" / "dart" / "_fs_api_cache"
    for kr, name in pairs:
        off = kr2cc.get(kr)
        try:
            on = F.resolve_corp(name)
        except Exception:
            on = None
        has_cache = bool(off) and bool(list(cache.glob(f"{off}_*.json")))
        if off is None:
            miss += 1
            print(f"  MISS      {kr} {name:22s} online={on}")
        elif on is not None and off != on:
            mismatch += 1
            print(f"  MISMATCH  {kr} {name:22s} online={on} offline={off}")
        else:
            ok += 1
            if not has_cache:
                print(f"  (캐시없음) {kr} {name:22s} corp_code={off}")
    print(f"\n일치={ok}  census미등재={miss}  불일치={mismatch}")


if __name__ == "__main__":
    main()
