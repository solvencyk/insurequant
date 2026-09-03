# -*- coding: utf-8 -*-
"""IFRS17_BS.json item5(해약환급금준비금)를 **경영공시 PDF**의 '해약환급금준비금 등의 적립'
표와 전수 대조한다.

동기(owner 2026-09-02): "해약환급금준비금을 경영공시 PDF 기준으로 비교해서 DART랑 차이 큰
애들은 갈아끼우라고 했는데 하나도 안 고쳐져 있다. 삼성생명·한화생명이 특히 1~3분기 오차가
크다." 마스터의 item5 는 DART 주석(기적립액+예정액)에서 오는데, 경영공시 표는 그 분기의
**잔액**을 직접 싣는다 — 개념이 어긋나면 경영공시가 정본이다.

표 위치: 생보 7-2 또는 7-3, 손보 5-3 (회사·분기별로 절 번호가 다르다). 단위 억원.
값이 '-' 면 그 분기 **미적립**이라는 뜻이지 결측이 아니다.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
import fitz  # noqa: E402

LABEL = "해약환급금준비금"
NUM = re.compile(r"^\(?-?[\d,]+\)?$")


def parse_pdf(path: Path):
    """(당분기값_억원 or 'none', 페이지) — 못 찾으면 None."""
    try:
        doc = fitz.open(path)
    except Exception:
        return None
    try:
        for i, pg in enumerate(doc):
            if i < 2:
                continue
            t = pg.get_text()
            if LABEL not in t or "적립" not in t:
                continue
            lines = [ln.strip() for ln in t.splitlines()]
            for j, ln in enumerate(lines):
                if ln.replace(" ", "") != LABEL:
                    continue
                # 라벨 다음의 첫 유효 토큰: 숫자 또는 '-'(미적립)
                for k in range(j + 1, min(j + 6, len(lines))):
                    tok = lines[k].replace(" ", "")
                    if tok == LABEL:          # 한화처럼 라벨이 두 번 나오는 레이아웃
                        continue
                    if tok in ("-", "–", "—"):
                        return ("none", i + 1)
                    if NUM.fullmatch(tok):
                        v = tok.replace(",", "")
                        neg = v.startswith("(") or v.startswith("-")
                        v = v.strip("()-")
                        if not v.isdigit():
                            continue
                        return (-int(v) if neg else int(v), i + 1)
                    if tok and not NUM.fullmatch(tok):
                        break     # 다른 라벨을 만났다
        return None
    finally:
        doc.close()


def main():
    master = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mi = {(r["원보험사코드"], r["공시분기"]): r["값"]
          for r in master if r["항목번호"] == 5}
    name = {r["원보험사코드"]: r["원수사명"] for r in master}

    rows = []
    for pdf in sorted((ROOT / "data" / "disclosure").glob("FY*/raw/*.pdf")):
        qdir = pdf.parts[-3]
        quarter = f"{qdir[2:6]}.{qdir[-1]}Q"
        code = pdf.stem.split("_", 1)[0]
        if not re.fullmatch(r"KR\d{4}", code):
            continue
        got = parse_pdf(pdf)
        if got is None:
            rows.append((code, quarter, None, mi.get((code, quarter)), "표없음"))
            continue
        val, _pg = got
        mv = mi.get((code, quarter))
        if val == "none":
            rows.append((code, quarter, "미적립", mv, "미적립"))
            continue
        disc = val * 100.0          # 억원 -> 백만원
        if mv is None:
            rows.append((code, quarter, disc, None, "마스터결측"))
        else:
            diff = abs(disc - mv) / max(abs(disc), 1.0)
            rows.append((code, quarter, disc, mv, f"{diff:.1%}"))

    big = [r for r in rows if r[4] not in ("표없음", "미적립", "마스터결측")
           and float(r[4].rstrip("%")) > 1.0]
    miss = [r for r in rows if r[4] == "마스터결측"]
    nonacc = [r for r in rows if r[4] == "미적립"]
    notab = [r for r in rows if r[4] == "표없음"]

    print(f"PDF 스캔 {len(rows)}개 (회사-분기)")
    print(f"  표 인식 실패 {len(notab)} · 경영공시 미적립('-') {len(nonacc)} · 마스터 결측 {len(miss)}")
    print(f"  대조 가능 {len(rows)-len(notab)-len(nonacc)-len(miss)} · **차이 1% 초과 {len(big)}건**")
    print()
    for code, q, disc, mv, tag in sorted(big, key=lambda r: -float(r[4].rstrip('%'))):
        print(f"  {name.get(code,code):<12} {q}  공시={disc:>12,.0f}  마스터={mv:>12,.0f}  차이={tag}")
    if miss:
        print("\n-- 경영공시엔 값이 있는데 마스터가 비어 있는 칸 --")
        for code, q, disc, mv, tag in sorted(miss):
            print(f"  {name.get(code,code):<12} {q}  공시={disc:,.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
