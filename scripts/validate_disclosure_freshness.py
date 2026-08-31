# -*- coding: utf-8 -*-
"""새 분기로 받은 경영공시 PDF 가 실은 직전 분기와 같은 파일인지 검사한다.

**왜 이 게이트가 생겼나 (2026-08-31).** 2026.2Q 라운드에서 세 회사가 직전 분기 PDF 를
그대로 받아왔다 — KR0011(DB손해)·KR0029(AIG)·KR0150(서울보증). 바이트 단위로 동일했다.
그 상태로 파싱·적재가 통과했고, 마스터의 "2026.2Q" 행 30개 중 **27개가 2026.1Q 와 값이
똑같았다.** 산수는 전부 맞으니 룰 게이트는 GREEN 이었다 — 소스가 틀린 통과다.

원인은 회사 사이트의 고정 인덱스/중복 id 다. 서울보증은 다운로드 링크 5개가 전부
`id="test1"` 을 공유해서 고정 xpath 가 항상 첫 번째(1분기) 링크를 집는다. 매 분기
반복될 구조적 결함이라 사람 눈이 아니라 기계가 잡아야 한다.

`download_disclosure_2026q2_nonlife.py` 헤더에 이미 이 함정이 **문장으로** 적혀 있었다
("Caller MUST hash-compare each output against the existing FY2026_Q1 file"). 그런데
그걸 실제로 검사하는 코드는 없었다. 문서에 mandatory 라고 쓴 것은 강제가 아니다.

판정:
  RED   직전 분기 파일과 sha256 이 동일 → 재탕. 그 분기 데이터가 아니다.
  YELLOW 직전 분기가 없어 대조 불가(신규 편입사 등).
  GREEN  새 파일.

사용:
  python scripts/validate_disclosure_freshness.py                 # 최신 분기
  python scripts/validate_disclosure_freshness.py --period FY2026_Q2
  python scripts/validate_disclosure_freshness.py --all-periods
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / "data" / "disclosure"
OUT = ROOT / "data" / "_derived" / "disclosure_freshness.json"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def periods() -> list[str]:
    ps = [d.name for d in DISC.iterdir()
          if d.is_dir() and re.fullmatch(r"FY\d{4}_Q[1-4]", d.name)]
    return sorted(ps)


def prev_period(p: str) -> str | None:
    y, q = int(p[2:6]), int(p[-1])
    return f"FY{y}_Q{q-1}" if q > 1 else f"FY{y-1}_Q4"


def pdfs(period: str) -> dict[str, Path]:
    """회사코드 -> PDF. pdf/ 를 우선하고 없으면 raw/ 를 본다."""
    out: dict[str, Path] = {}
    for sub in ("raw", "pdf"):   # pdf 가 뒤라서 있으면 덮어쓴다
        d = DISC / period / sub
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.pdf")):
            out[p.stem.split("_")[0]] = p
    return out


def check(period: str) -> tuple[list, list, list]:
    prev = prev_period(period)
    cur_map, prev_map = pdfs(period), pdfs(prev) if prev else {}
    prev_sha = {c: sha(p) for c, p in prev_map.items()}
    red, yellow, green = [], [], []
    for code, p in sorted(cur_map.items()):
        if code not in prev_sha:
            yellow.append((code, p.name, "직전 분기 파일 없음 — 대조 불가"))
            continue
        if sha(p) == prev_sha[code]:
            red.append((code, p.name, f"{prev} 파일과 sha256 동일 — 재탕"))
        else:
            green.append(code)
    return red, yellow, green


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--period")
    ap.add_argument("--all-periods", action="store_true")
    args = ap.parse_args()

    targets = periods() if args.all_periods else [args.period or periods()[-1]]
    report, total_red = {}, 0
    for period in targets:
        red, yellow, green = check(period)
        total_red += len(red)
        report[period] = {
            "red": [{"code": c, "file": f, "reason": r} for c, f, r in red],
            "yellow": [{"code": c, "file": f, "reason": r} for c, f, r in yellow],
            "green_count": len(green),
        }
        print(f"[{period}] RED={len(red)} YELLOW={len(yellow)} GREEN={len(green)}")
        for c, f, r in red:
            print(f"   RED    {c:<8} {f[:36]:<38} {r}")
        for c, f, r in yellow:
            print(f"   YELLOW {c:<8} {f[:36]:<38} {r}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSUMMARY disclosure_freshness  RED={total_red}")
    print(f"Wrote {OUT}")
    return 2 if total_red else 0


if __name__ == "__main__":
    raise SystemExit(main())
