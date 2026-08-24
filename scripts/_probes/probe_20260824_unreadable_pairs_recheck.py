"""`SOURCE_UNREADABLE_NOT_VERIFIED` 9쌍에 대한 **sender 독립 재확인** (2026-08-24).

parser-kics 가 vision 판독으로 "9쌍 전부 원문이 전=후 동일을 명시한다" 고 답했다. 원 sender 로서
그 주장을 베끼지 않고 다시 잰다. 이 스크립트는 세 가지를 한다:

  ① 인용 페이지의 fitz 텍스트를 그대로 덤프한다 — 텍스트가 나오면 vision 없이도 검증된다
     (parser 가 미래에셋 3분기는 텍스트가 나온다고 주장했다. 그 주장부터 확인한다).
  ② 마스터의 item17/19 적용전·적용후를 뽑아 **전=후인지** 재확인한다.
  ③ 문서 전체 텍스트밀도와 **인용 페이지만의 밀도**를 나란히 잰다 — 사이드카가 UNREADABLE 로
     찍는 근거(전체 평균)와 실제 판독 대상 페이지의 상태가 다른지 보기 위해서다.

읽기 전용. 마스터도 사이드카도 건드리지 않는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "artifacts" / "validation" / "probe_20260824_unreadable_pairs_recheck.txt"

# parser 답변이 든 인용 페이지(0-idx). 목록을 그대로 믿지 않으려고 **주변 페이지까지** 넓힌다.
PAIRS = [
    ("KR0010", "KB손해보험",        "FY2025_Q3", "2025.3Q", [14, 15, 16]),
    ("KR0010", "KB손해보험",        "FY2026_Q1", "2026.1Q", [16, 17, 18]),
    ("KR0079", "미래에셋생명",      "FY2025_Q1", "2025.1Q", [16, 17, 18]),
    ("KR0079", "미래에셋생명",      "FY2025_Q3", "2025.3Q", [17, 18, 19]),
    ("KR0079", "미래에셋생명",      "FY2026_Q1", "2026.1Q", [17, 18, 19]),
    ("KR0080", "에이아이에이생명",  "FY2025_Q1", "2025.1Q", [15, 16]),
    ("KR0080", "에이아이에이생명",  "FY2025_Q3", "2025.3Q", [15, 16]),
    ("KR0080", "에이아이에이생명",  "FY2026_Q1", "2026.1Q", [16, 17]),
    ("KR0087", "동양생명",          "FY2026_Q1", "2026.1Q", [15, 16]),
]

MARKERS = ("경과조치", "적용하지", "동일", "지급여력기준금액", "생명", "시장위험")


def _find_pdf(fy: str, code: str) -> Path | None:
    d = ROOT / "data" / "disclosure" / fy / "raw"
    if not d.exists():
        return None
    hits = sorted(d.glob(f"{code}_*.pdf"))
    return hits[0] if hits else None


WATCH_ITEMS = (1, 14, 15, 17, 19, 27)


def _master_cells():
    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    out: dict[tuple[str, str, int], tuple] = {}
    for r in rows:
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        if it in WATCH_ITEMS:
            out[(r.get("원보험사코드"), r.get("공시분기"), it)] = (
                r.get("값"), r.get("값_적용후"))
    return out


def _tfi_map():
    """공통적용 경과조치(TFI) 적용여부 사이드카 — vision 주장의 **기계적 필요조건**."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from validate_kics_disclosure import _load_tfi_applicability
    return _load_tfi_applicability()


def main() -> None:
    cells = _master_cells()
    tfi = _tfi_map()
    lines: list[str] = []
    for code, name, fy, q, pages in PAIRS:
        pdf = _find_pdf(fy, code)
        lines.append(f"===== {code} {name} {q} =====")
        lines.append(f"  pdf: {pdf.relative_to(ROOT) if pdf else 'NOT FOUND'}")
        lines.append(f"  TFI 적용여부 사이드카: {tfi.get((code, q), '키없음')}")
        for it in WATCH_ITEMS:
            pre, post = cells.get((code, q, it), (None, None))
            same = "전==후" if str(pre) == str(post) else "*** 전!=후 ***"
            lines.append(f"  master item{it}: 값={pre!r} 값_적용후={post!r}  {same}")
        if pdf is None:
            lines.append("")
            continue
        doc = fitz.open(pdf)
        total = sum(len(doc[i].get_text().strip()) for i in range(doc.page_count))
        lines.append(f"  문서 전체: {doc.page_count}p / {total:,}자 "
                     f"= {total / max(1, doc.page_count):.1f}자/p  <- 사이드카가 보는 값")
        cited = 0
        for i in pages:
            if i >= doc.page_count:
                lines.append(f"  p{i}: 범위 밖(page_count={doc.page_count})")
                continue
            t = doc[i].get_text()
            cited += len(t.strip())
            hits = [m for m in MARKERS if m in t.replace(" ", "")]
            lines.append(f"  p{i}: {len(t.strip()):>6,}자  마커 {hits}")
            body = " ".join(t.split())
            lines.append(f"       {body[:600]}")
        lines.append(f"  인용 페이지 합: {cited:,}자 / {len(pages)}p "
                     f"= {cited / max(1, len(pages)):.1f}자/p  <- 실제 판독 대상")
        doc.close()
        lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
