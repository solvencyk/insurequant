# -*- coding: utf-8 -*-
"""DART 본문 XML 전수 census — (39개사 x FY2023_Q1..FY2026_Q2) 그리드.

`scripts/check_dart_raw_coverage.py` 는 **한 번이라도 디스크에 있었던 칸**(high-water
mark)이 사라졌는지만 본다. 이 프로브는 그 반대 축이다 — **기대 그리드 기준으로 애초에
없는 칸**을 센다. 둘 다 필요하다.

## 이 census 를 손으로 다시 짜면 반드시 밟는 함정 2종 (2026-09-02 실측)

**함정 ① 회사명으로 키를 잡으면 거짓 결측이 나온다.**
raw 리프 이름은 `KR####_<DART canonical name>` 인데 DART canonical 은 K-ICS 원수사명과
다르다 — `KR0069_삼성생명`(K-ICS 는 '삼성생명보험'), `KR0079_미래에셋생명`(K-ICS 는
'미래에셋생명보험'). 이름으로 훑으면 이 두 칸이 "2026.2Q 원문 자체가 없음" 으로 나오는데
**실제로는 둘 다 5.3MB / 3.7MB 본문 XML 이 멀쩡히 있다.** 이 오탐이 실제로 한 번
발주로 이어졌다(2026-09-02). **반드시 KR 코드로 키를 잡을 것.**

**함정 ② 본문 XML 은 리프 바로 밑에만 있는 게 아니다.**
`leaf/*.xml` 만 glob 하면 64칸이 "zip 만 있고 본문 없음" 으로 나온다. 그 칸들은
`leaf/xml/*.xml` 로 이미 풀려 있다(`extract_dart_zips.py` 가 인정하는 세 레이아웃 =
`*.xml` · `xml/*.xml` · `extracted*/*.xml`). 세 개를 다 봐야 한다.

## 셀 판정

  xml        본문 XML >=1개 (위 세 레이아웃 중 하나)
  zip_only   document.zip 은 있는데 XML 이 없음 -> extract_dart_zips.py 돌릴 것
  no_filing  디렉터리에 meta.json {"no_filing": true} — 원천 부재를 **기록해 둔** 칸
  MISSING    디렉터리 자체가 없음 (미조사 또는 유실)

`MISSING` 은 두 부류로 갈라서 센다. **연1회 공시사(감사보고서만 내는 회사)** 의 비-4분기
칸은 원천에 분기 필링이 존재하지 않으므로 결손이 아니다 — 판정 근거는
`data/_derived/bs_carry_forward_cells.json` 의 `hold_forward_annual_only_filer`.

Usage:
  python scripts/_probes/census_dart_body_xml.py
  python scripts/_probes/census_dart_body_xml.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

DART = ROOT / "data" / "dart"
CARRY_FORWARD = ROOT / "data" / "_derived" / "bs_carry_forward_cells.json"

# 39-company universe — claude-agent-downloader.md §Universe (fixed list).
UNIVERSE: list[tuple[str, str, str]] = [
    ("KR0001", "메리츠화재", "손보"),
    ("KR0002", "한화손보", "손보"),
    ("KR0003", "롯데손보", "손보"),
    ("KR0004", "MG손해(구 예별)", "손보"),
    ("KR0005", "흥국화재", "손보"),
    ("KR0008", "삼성화재", "손보"),
    ("KR0009", "현대해상", "손보"),
    ("KR0010", "KB손해", "손보"),
    ("KR0011", "DB손해", "손보"),
    ("KR0029", "AIG손해", "손보"),
    ("KR0032", "NH농협손해", "손보"),
    ("KR0049", "악사손해", "손보"),
    ("KR0050", "하나손해", "손보"),
    ("KR0051", "신한이지손해", "손보"),
    ("KR0150", "서울보증", "손보"),
    ("KR1000", "코리안리", "손보"),
    ("KR1098", "카카오페이손해", "손보"),
    ("KR0068", "한화생명", "생보"),
    ("KR0069", "삼성생명", "생보"),
    ("KR0070", "ABL생명", "생보"),
    ("KR0071", "흥국생명", "생보"),
    ("KR0072", "KDB생명", "생보"),
    ("KR0073", "교보생명", "생보"),
    ("KR0074", "라이나생명", "생보"),
    ("KR0075", "BNP파리바카디프", "생보"),
    ("KR0076", "iM라이프", "생보"),
    ("KR0079", "미래에셋생명", "생보"),
    ("KR0080", "AIA생명", "생보"),
    ("KR0082", "DB생명", "생보"),
    ("KR0083", "푸본현대생명", "생보"),
    ("KR0087", "동양생명", "생보"),
    ("KR0094", "신한라이프", "생보"),
    ("KR0095", "메트라이프", "생보"),
    ("KR0097", "하나생명", "생보"),
    ("KR0099", "KB라이프", "생보"),
    ("KR0100", "처브라이프", "생보"),
    ("KR0104", "농협생명", "생보"),
    ("KR1010", "교보라이프플래닛", "생보"),
    ("KR1011", "IBK연금보험", "생보"),
]

PERIODS = [f"FY{y}_Q{q}" for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)] + [
    "FY2026_Q1",
    "FY2026_Q2",
]

# AIG(KR0029) 는 2023~2026 전 기간 사업/반기/분기보고서를 내지 않고 감사보고서만 낸다
# (2026-08-19 inbox/downloader/20260819T0820Z 발주 D 에서 확정). carry-forward
# 레지스트리에도 등재돼 있으나 여기에 명시해 둔다.
_ANNUAL_ONLY_EXTRA = {"KR0029"}


def annual_only_filers() -> set[str]:
    """연1회 공시사 = 분기 필링이 원천에 없는 회사 (레지스트리 정본 + AIG)."""
    codes = set(_ANNUAL_ONLY_EXTRA)
    try:
        reg = json.loads(CARRY_FORWARD.read_text(encoding="utf-8"))
        if reg.get("rule") == "hold_forward_annual_only_filer":
            codes |= set(reg.get("companies", {}))
    except (OSError, json.JSONDecodeError):
        print("  [warn] bs_carry_forward_cells.json 을 못 읽었다 — AIG 만 적용", file=sys.stderr)
    return codes


def scan_period(period: str) -> dict[str, dict]:
    root = DART / period / "raw"
    out: dict[str, dict] = {}
    if not root.is_dir():
        return out
    for leaf in sorted(root.iterdir()):
        if not leaf.is_dir():
            continue
        kr = leaf.name.split("_", 1)[0]
        if not kr.startswith("KR"):
            continue  # corp_code-prefixed 지주 등은 보험사 유니버스가 아님
        rec = out.setdefault(kr, {"leaves": [], "xml": 0, "zip": 0, "no_filing": False})
        rec["leaves"].append(leaf.name)
        # 함정 ②: 세 레이아웃을 모두 본다.
        for pat in ("*.xml", "xml/*.xml", "extracted*/*.xml"):
            rec["xml"] += len(list(leaf.glob(pat)))
        rec["zip"] += len(list(leaf.glob("*.zip")))
        meta = leaf / "meta.json"
        if meta.is_file():
            try:
                if json.loads(meta.read_text(encoding="utf-8")).get("no_filing"):
                    rec["no_filing"] = True
            except (OSError, json.JSONDecodeError):
                pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, help="셀 판정을 JSON 으로도 저장")
    args = ap.parse_args()

    annual_only = annual_only_filers()
    scans = {p: scan_period(p) for p in PERIODS}

    grid: dict[str, dict[str, str]] = {}
    counts: Counter[str] = Counter()
    missing: list[tuple[str, str, str, bool]] = []

    for kr, name, _kind in UNIVERSE:
        grid[kr] = {}
        for p in PERIODS:
            rec = scans[p].get(kr)
            if rec is None:
                v = "MISSING"
            elif rec["xml"] > 0:
                v = "xml"
            elif rec["no_filing"]:
                v = "no_filing"
            elif rec["zip"] > 0:
                v = "zip_only"
            else:
                v = "MISSING"
            if v == "MISSING":
                missing.append((kr, name, p, kr in annual_only))
            counts[v] += 1
            grid[kr][p] = v

    sym = {"xml": "O", "zip_only": "z", "no_filing": "-", "MISSING": "X"}
    hdr = "".join(f"{p.replace('FY','').replace('_Q','.'):<8}" for p in PERIODS)
    print(f"{'KR':<8}{'회사':<18}{'AO':<4}{hdr}")
    for kr, name, _kind in UNIVERSE:
        ao = "AO" if kr in annual_only else ""
        line = "".join(f"{sym[grid[kr][p]]:<8}" for p in PERIODS)
        print(f"{kr:<8}{name:<18}{ao:<4}{line}")

    total = len(UNIVERSE) * len(PERIODS)
    print(f"\ngrid = {len(UNIVERSE)}사 x {len(PERIODS)}분기 = {total} cells")
    for k in ("xml", "zip_only", "no_filing", "MISSING"):
        print(f"  {k:<10} {counts[k]}")

    q_missing = [m for m in missing if not m[3]]
    a_missing = [m for m in missing if m[3]]
    print(f"\nMISSING — 분기 공시사 (실제 결손): {len(q_missing)}")
    for kr, name, p, _ in q_missing:
        print(f"    {kr} {name} {p}")
    print(f"MISSING — 연1회 공시사 (원천에 분기 필링 없음, 결손 아님): {len(a_missing)}")
    per = Counter(p for _, _, p, _ in a_missing)
    for p in PERIODS:
        if per[p]:
            print(f"    {p}: {per[p]}")

    if counts["zip_only"]:
        print("\n  -> zip_only 가 있다: python scripts/extract_dart_zips.py")

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "periods": PERIODS,
                    "annual_only": sorted(annual_only),
                    "counts": dict(counts),
                    "grid": grid,
                    "missing_quarterly_filers": [
                        {"kr": k, "name": n, "period": p} for k, n, p, _ in q_missing
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nwrote {args.json}")

    return 1 if q_missing or counts["zip_only"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
