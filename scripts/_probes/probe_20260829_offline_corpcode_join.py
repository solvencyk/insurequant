# -*- coding: utf-8 -*-
"""FS-API 캐시를 **오프라인·결정적으로** (원수사명, 분기) 에 붙일 수 있는가 (읽기 전용).

문제: `fetch_dart_fs.resolve_corp()` 는 `data/dart/raw/CORPCODE.xml`(30MB, **gitignore**)를
읽고, 없으면 **네트워크로 받는다**. 게이트가 그걸 쓰면 새 클론·CI 에서 커버리지가 달라지고
골든이 환경마다 흔들린다. 그래서 **추적되는 파일만으로** 같은 매핑이 되는지 확인한다.

후보: `data/dart/_alotmatter_cache/*.json` (git 추적, 1,040+ 파일) — 각 응답의 `list[]` 가
`corp_code` 와 `corp_name` 을 같이 싣는다.

두 매핑(온라인 resolve_corp vs 오프라인 alotmatter 색인)이 **같은 corp_code** 를 주는지,
그리고 오프라인 매핑이 몇 개 회사를 덮는지 센다.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_dart_fs as F  # noqa: E402


def offline_index() -> dict[str, str]:
    """정규화 corp_name -> corp_code (추적 파일만)."""
    idx: dict[str, str] = {}
    for p in sorted((ROOT / "data" / "dart" / "_alotmatter_cache").glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for a in d.get("list", []) or []:
            cn, cc = (a.get("corp_name") or "").strip(), (a.get("corp_code") or "").strip()
            if cn and cc:
                idx.setdefault(cn.replace(" ", ""), cc)
    return idx


def main():
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    names = sorted({r["원수사명"] for r in rows})
    idx = offline_index()
    print(f"오프라인 색인(alotmatter): corp_name {len(idx)} 개")
    print(f"PL 마스터 회사: {len(names)} 개")
    print()

    ok = miss = mismatch = 0
    for n in names:
        nn = n.replace(" ", "")
        # 온라인(현행) 경로
        try:
            on = F.resolve_corp(n)
        except Exception:
            on = None
        # 오프라인 후보: 정확일치 → 마스터명이 색인명을 포함 → 색인명이 마스터명을 포함
        off = idx.get(nn)
        if off is None:
            cands = sorted((k for k in idx if k and (k in nn or nn in k)),
                           key=lambda k: -len(k))
            off = idx[cands[0]] if cands else None
        if off is None:
            miss += 1
            print(f"  MISS      {n:22s} online={on}")
        elif on is not None and off != on:
            mismatch += 1
            print(f"  MISMATCH  {n:22s} online={on} offline={off}")
        else:
            ok += 1
    print()
    print(f"일치={ok}  오프라인미해결={miss}  불일치={mismatch}")


if __name__ == "__main__":
    main()
