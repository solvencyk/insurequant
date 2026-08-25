# -*- coding: utf-8 -*-
"""하나생명 CSM 6셀 원문 재검산 (validation iter4).

FY2025 사업보고서(20260325000201) note 14-4 · FY2024(20250331000222) note 13-4 ·
FY2023(20240329000112) note 13-3(=같은 성격의 측정요소 차이조정) 을 각각 열어
**행 라벨과 셀 값을 그대로 인쇄**한다. 잔차(plug)로 만든 값이 0개인지 확인하는 것이
목적이라, 계산은 하지 않고 원문 셀만 찍는다. <당기>/<전기> 표를 둘 다 찍는다.

read-only. 파일 기록 없음.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FILINGS = [
    ("FY2023 (20240329000112)",
     ROOT / "data/dart/FY2023_Q4/raw/KR0097_하나생명보험_20240329000112/20240329000112_00760.xml",
     r"13-4\s*보험료배분접근법을\s*적용한\s*보험계약\s*이외"),
    ("FY2024 (20250331000222)",
     ROOT / "data/dart/FY2024_Q4/raw/KR0097_하나생명보험_20250331000222/20250331000222_00760.xml",
     r"13-4\s*보험료배분접근법을\s*적용한\s*보험계약\s*이외"),
    ("FY2025 (20260325000201)",
     ROOT / "data/dart/FY2025_Q4/raw/KR0097_하나생명보험_20260325000201/20260325000201_00760.xml",
     r"14-4\s*보험료배분접근법을\s*적용한\s*보험계약\s*이외"),
    ("FY2025 dup filing (20260325000202)",
     ROOT / "data/dart/FY2025_Q4/raw/KR0097_하나생명보험_20260325000202/20260325000202_00761.xml",
     r"14-4\s*보험료배분접근법을\s*적용한\s*보험계약\s*이외"),
]

TAG = re.compile(r"<[^>]+>")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def cells(tr_html: str) -> list[str]:
    out = []
    for m in re.finditer(r"<T[DEH][^>]*>(.*?)</T[DEH]>", tr_html, re.S | re.I):
        t = TAG.sub(" ", m.group(1)).replace("&nbsp;", " ").replace("&amp;", "&")
        out.append(re.sub(r"\s+", " ", t).strip())
    return out


def dump(label: str, path: Path, caption_pat: str, n_tables: int = 4) -> None:
    print("=" * 110)
    print(f"{label}   {path.name}")
    print("=" * 110)
    if not path.exists():
        print("  !! MISSING")
        return
    src = read(path)
    flat = TAG.sub(" ", src)
    cm = re.search(caption_pat, re.sub(r"\s+", " ", flat))
    # 캡션은 태그가 섞여 있을 수 있어 raw 에서도 느슨하게 찾는다
    m = re.search(caption_pat.replace(r"\s*", r"[\s<>/A-Za-z0-9=\"']*"), src)
    if not m:
        # fallback: '14-4'/'13-4' 문자열 위치
        key = caption_pat[:4].replace("\\", "")
        m = re.search(re.escape(key), src)
    if not m:
        print("  !! caption not found")
        return
    start = m.start()
    print(f"  caption @char {start}: "
          f"{re.sub(chr(92)+'s+', ' ', TAG.sub(' ', src[start:start+220])).strip()}")
    seg = src[start:start + 400000]
    tabs = list(re.finditer(r"<TABLE.*?</TABLE>", seg, re.S | re.I))
    for ti, tm in enumerate(tabs[:n_tables]):
        tbl = tm.group(0)
        trs = re.findall(r"<TR.*?</TR>", tbl, re.S | re.I)
        pre = re.sub(r"\s+", " ", TAG.sub(" ", seg[max(0, tm.start() - 800):tm.start()]))
        um = re.findall(r"\(\s*단위\s*[:：]?\s*[^)]{1,20}\)", pre)
        marker = re.findall(r"<\s*당\s*기\s*>|<\s*전\s*기\s*>|당\s*기|전\s*기", pre[-160:])
        print(f"\n  [TABLE #{ti}] rows={len(trs)}  단위={um[-1] if um else '(선언없음)'}"
              f"  직전문맥끝={pre[-90:]!r}")
        for tr in trs:
            c = cells(tr)
            if c and any(x for x in c):
                print("      | " + " | ".join(x if x else "-" for x in c[:12]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for label, p, pat in FILINGS:
        dump(label, p, pat)
        print()
