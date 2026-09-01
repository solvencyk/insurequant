# -*- coding: utf-8 -*-
"""Fill 값_적용후 for items 22 (법인세조정액) and 23 (기타 요구자본) from the raw 경과조치 tables.

Why this exists: the 경과조치 '적용후' loaders filled the 요구자본 core (15-21) but skipped the
two adjustment rows, so 123 (회사,분기) of the 18 선택경과조치 적용사 carried item22/23후 = null
while the disclosure prints them on the same table. The gate only ever *saw* a fraction of that
(`_post_transition_parent_census` 조정항목 review fires only when the PREVIOUS quarter has a post
value), so every fill exposed one more quarter behind it — a cascade with no end until the whole
census is closed at once. Closing them also lets the R5 적용후 항등식
(item14후 = item15후 − item22후 + item23후) actually run on those cells instead of skipping.

Parse contract — three independent guards, all must pass before a cell is written:

  1. ROW: only lines that are exactly "법인세조정액" / "기타요구자본" on a page that mentions
     경과조치 and one of 장수위험 / 주식위험 / 금리위험 (= the ②/③ 선택적용 tables). The
     [경과조치 적용 전 … 세부] table's rows read "Ⅱ. 법인세조정액" / "Ⅲ. 기타 요구자본" and carry
     three QUARTER columns, so the exact-match rule keeps them out; the 재무제표 주석 copies are
     excluded by the page keywords.
  2. UNIT: the row's 적용전 number, after trying 백만원/억원/천원 scaling, must reproduce the
     already-stored 적용전 (값) for that item. If no scale matches, the row is not what we think
     it is → skip. (Both-zero rows short-circuit: unit is irrelevant.)
  3. IDENTITY: with the candidate 22후/23후, R5 적용후 (item14후 = item15후 − item22후 + item23후)
     must close inside the gate's own tolerance max(2.0, 0.5% of expected). This is what stops a
     mis-picked column from landing.

Multiple tables (②, ③, and occasionally more) each state the pair. If they disagree the cell is a
genuine 다중경과조치 결합 unknown (e.g. 흥국생명's 기타요구자본 = 관계회사 요구자본 환산치, which
② and ③ move to different values) → skipped, never guessed.

UPSERT-only (never overwrites an existing 값_적용후). Idempotent — safe to re-run each quarter.

Usage: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
           scripts/fill_post_transition_adjust_items.py [--dry-run] [--code KR0003]
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

TARGET = REPO / "kics_disclosure.json"

# Keep in sync with _TRANSITION_APPLIERS in scripts/validate_kics_disclosure.py
_TRANSITION_APPLIERS = frozenset({
    "KR0070", "KR0071", "KR0072", "KR0073", "KR0076", "KR0082",
    "KR0083", "KR0097", "KR0100", "KR1010", "KR1011", "KR0104",
    "KR0049", "KR0002", "KR0003", "KR0004", "KR0005", "KR0032",
})

# raw 도출 불가로 이미 확정된 (회사,분기) — 손대지 않는다.
_SKIP = {
    ("KR0005", "2024.4Q"),  # image-only PDF(텍스트레이어 0), owner GOLD-SCAN 대기
    ("KR0049", "2024.3Q"),  # 그 분기 지급여력비율 섹션 자체가 없음(보험업감독규정 부칙 제3조)
}

ROW_LABELS = {22: "법인세조정액", 23: "기타요구자본"}
PAGE_MUST_HAVE = ("경과조치",)
PAGE_ANY_OF = ("장수위험", "주식위험", "금리위험")
SCALES = (0.01, 1.0, 0.0001)  # 백만원→억원, 이미 억원, 천원→억원
ZERO_TOKENS = {"-", "─", "–", "—", "", "0"}


def _num(v):
    if v is None:
        return None
    s = str(v).strip().replace(",", "").replace(" ", "").replace("%", "")
    if s in ("", "-", "─", "–", "—"):
        return None
    for ch in ("△", "▲", "▽", "▼", "−"):
        s = s.replace(ch, "-")
    m = re.fullmatch(r"\((-?\d[\d.]*)\)", s)
    if m:
        s = "-" + m.group(1)
    s = s.lstrip("+")
    try:
        return float(s)
    except ValueError:
        return None


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


def quarter_to_period(q: str) -> str:
    year, qq = q.split(".")
    return f"FY{year}_Q{qq[0]}"


def find_pdf(code: str, quarter: str):
    hits = disclosure_pdfs(quarter_to_period(quarter), code)
    if not hits:
        return None
    amended = [p for p in hits if "_amended" in p.name]
    return max(amended or hits, key=lambda p: p.stat().st_size)


def scan_pairs(pdf: Path) -> dict[int, list[tuple[str, str]]]:
    """-> {item_no: [(전_token, 후_token), ...]} one entry per 경과조치 table occurrence."""
    out: dict[int, list[tuple[str, str]]] = {22: [], 23: []}
    doc = fitz.open(pdf)
    try:
        for page in doc:
            text = page.get_text()
            if not all(k in text for k in PAGE_MUST_HAVE):
                continue
            if not any(k in text for k in PAGE_ANY_OF):
                continue
            lines = [l.strip() for l in text.splitlines()]
            for i, line in enumerate(lines):
                for item, label in ROW_LABELS.items():
                    if line != label:
                        continue
                    nxt = [x for x in lines[i + 1:i + 6] if x != ""][:2]
                    if len(nxt) == 2:
                        out[item].append((nxt[0], nxt[1]))
    finally:
        doc.close()
    return out


def resolve(pairs: list[tuple[str, str]], stored_pre):
    """-> (value_after_in_억원, why). None value means unresolved."""
    if not pairs:
        return None, "표에 행 없음"
    cands: set[float] = set()
    notes: list[str] = []
    for pre_tok, post_tok in pairs:
        pre_zero = pre_tok.strip() in ZERO_TOKENS
        post_zero = post_tok.strip() in ZERO_TOKENS
        if pre_zero and post_zero:
            if stored_pre is None or abs(stored_pre) < 0.5:
                cands.add(0.0)
                continue
            return None, f"raw 0 인데 저장된 적용전={stored_pre}"
        pre_v = _num(pre_tok)
        if pre_v is None:
            # 이 occurrence는 표 행이 아니다(라벨 중복 / 다음 절 제목이 딸려온 케이스) — 버린다.
            notes.append(f"전 파싱불가({pre_tok!r})")
            continue
        if stored_pre is None:
            return None, "저장된 적용전 없음(단위 확정 불가)"
        scale = next((s for s in SCALES
                      if abs(pre_v * s - stored_pre) <= max(1.0, 0.01 * abs(stored_pre))), None)
        if scale is None:
            return None, f"단위 불일치 (raw전={pre_v} vs 저장전={stored_pre})"
        post_v = _num(post_tok)
        if post_v is None:
            # 적용후 칸이 비어 있는 표기(= 해당 경과조치가 이 항목을 안 건드림). 0 과 구분되지
            # 않으므로 후보로 세지 않고, 다른 표의 명시값에 판단을 맡긴다.
            notes.append(f"후 공란({post_tok!r})")
            continue
        cands.add(round(post_v * scale, 2))
    if not cands:
        return None, "; ".join(notes) or "해석 가능한 행 없음"
    if len(cands) != 1:
        return None, f"표별 적용후 불일치 {sorted(cands)} (다중경과조치 결합 불명)"
    return cands.pop(), "ok"


def main() -> int:
    dry = "--dry-run" in sys.argv
    only = None
    if "--code" in sys.argv:
        only = sys.argv[sys.argv.index("--code") + 1]

    data = json.loads(TARGET.read_text(encoding="utf-8"))
    by_cq: dict[tuple[str, str], dict[int, dict]] = {}
    for r in data:
        by_cq.setdefault((r["원보험사코드"], r["공시분기"]), {})[int(r["항목번호"])] = r

    todo = []
    for (code, quarter), items in by_cq.items():
        if code not in _TRANSITION_APPLIERS or (code, quarter) in _SKIP:
            continue
        if only and code != only:
            continue
        gaps = [n for n in (22, 23) if n in items and items[n].get("값_적용후") in (None, "")]
        if gaps:
            todo.append((code, quarter, gaps))
    todo.sort()

    written, blocked, noraw = [], [], []
    for code, quarter, gaps in todo:
        items = by_cq[(code, quarter)]
        name = next((r.get("원수사명", code) for r in items.values()), code)
        pdf = find_pdf(code, quarter)
        if pdf is None:
            noraw.append((code, name, quarter, "raw PDF 없음"))
            continue
        pairs = scan_pairs(pdf)

        cand: dict[int, float] = {}
        why: dict[int, str] = {}
        for n in gaps:
            v, reason = resolve(pairs[n], _num(items[n].get("값")))
            why[n] = reason
            if v is not None:
                cand[n] = v
        if not cand:
            blocked.append((code, name, quarter, "; ".join(f"item{n}: {why[n]}" for n in gaps)))
            continue

        # IDENTITY guard: R5 적용후 must close with the candidate values in place.
        v15 = _num((items.get(15) or {}).get("값_적용후"))
        v14 = _num((items.get(14) or {}).get("값_적용후"))
        v22 = cand.get(22, _num((items.get(22) or {}).get("값_적용후")))
        v23 = cand.get(23, _num((items.get(23) or {}).get("값_적용후")))
        if None in (v14, v15, v22, v23):
            blocked.append((code, name, quarter, "R5 입력 불완비(14/15/22/23후 중 결측)"))
            continue
        exp = v15 - v22 + v23
        if abs(exp - v14) > max(2.0, 0.005 * abs(exp)):
            blocked.append((code, name, quarter,
                            f"R5 불성립: 15후-22후+23후={exp:.2f} vs 14후={v14:.2f}"))
            continue

        for n, v in sorted(cand.items()):
            items[n]["값_적용후"] = _fmt(v)
            written.append((code, name, quarter, n, _fmt(v)))

    print(f"{'DRY-RUN ' if dry else ''}대상 (회사,분기)={len(todo)}  "
          f"채움={len(written)}셀  보류={len(blocked)}  raw없음={len(noraw)}")
    for code, name, quarter, n, v in written:
        print(f"  FILL  {code} {name} {quarter} item{n} -> {v}")
    for code, name, quarter, reason in blocked:
        print(f"  HOLD  {code} {name} {quarter}: {reason}")
    for code, name, quarter, reason in noraw:
        print(f"  NORAW {code} {name} {quarter}: {reason}")

    if not dry and written:
        TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
