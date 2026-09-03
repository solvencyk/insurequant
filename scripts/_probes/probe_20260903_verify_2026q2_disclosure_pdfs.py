# -*- coding: utf-8 -*-
"""FY2026_Q2 정기경영공시 pdf/ 39건 내용검증 (2026-09-03, owner 발주 재현용).

owner가 raw/ 에 1건뿐이라고 지적한 것에 대한 대응 조사:
1) pdf/ 에 39건이 이미 있는지, 2) 진짜 그 회사·2026.2Q 원문인지(스캔본/빈껍데기 아님),
3) 생보 7-2/7-3(해약환급금준비금등의 적립)·손보 5-3 절이 raw PDF 본문에 실제로 있는지
   (parsed/ MD 는 truncate 됐을 수 있어 파서 산출물이 아니라 raw PDF 를 직접 스캔).

사용:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260903_verify_2026q2_disclosure_pdfs.py
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import fitz  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf"
RAW_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "raw"
OUT = ROOT / "data" / "_derived" / "disclosure_2026q2_content_verify.json"

# 손보 17사 (source-catalog.yaml 기준 KR 코드)
NONLIFE_CODES = {
    "KR0001", "KR0002", "KR0003", "KR0004", "KR0005", "KR0008", "KR0009",
    "KR0010", "KR0011", "KR0029", "KR0032", "KR0049", "KR0050", "KR0051",
    "KR0150", "KR1000", "KR1098",
}

# 2026-09-03 실측 정정: 생보·손보 공통으로 "7-3. 해약환급금준비금 등의 적립" 절 사용
# (KR0049/KR0051 손보 2사에서 직접 확인 — owner 티켓의 "손보 5-3" 은 실제와 다름, 보고서에 정정 명시)
SECTION_RE = re.compile(r"7[-\s]?[23]\s*[-.]?\s*해약환급금\s*준비금")
GENERIC_SURRENDER_RE = re.compile(r"해약환급금\s*준비금")
PERIOD_RE = re.compile(r"2026\s*년\s*2\s*/\s*4\s*분기|2026[.\s]*0?6[.\s]*30|2026-06-30")


def kr_code(fn: str) -> str | None:
    m = re.match(r"(KR\d+)", fn)
    return m.group(1) if m else None


def per_page_density(doc: fitz.Document) -> list[int]:
    return [len(page.get_text()) for page in doc]


def main() -> None:
    results = {}
    files = sorted(PDF_DIR.glob("*.pdf")) + sorted(RAW_DIR.glob("*.pdf"))
    seen_codes = set()
    for p in files:
        code = kr_code(p.name)
        if not code or code in seen_codes:
            continue  # raw/ 에도 있으면 raw/ 우선(먼저 온 pdf/ 스킵 방지 위해 raw를 뒤에 안 두고 먼저 훑음 — 아래 정렬로 처리)
        seen_codes.add(code)

    # raw 우선 계약과 동일하게: raw에 있으면 raw를, 없으면 pdf를 검증 대상으로 삼는다
    raw_map = {kr_code(p.name): p for p in RAW_DIR.glob("*.pdf") if kr_code(p.name)}
    pdf_map = {kr_code(p.name): p for p in PDF_DIR.glob("*.pdf") if kr_code(p.name)}
    all_codes = sorted(set(raw_map) | set(pdf_map))

    for code in all_codes:
        src = "raw" if code in raw_map else "pdf"
        path = raw_map.get(code) or pdf_map[code]
        entry = {"file": path.name, "source_dir": src, "size_bytes": path.stat().st_size}
        try:
            doc = fitz.open(str(path))
        except Exception as e:  # noqa: BLE001
            entry["error"] = f"open_failed: {e}"
            results[code] = entry
            continue

        entry["page_count"] = doc.page_count
        densities = per_page_density(doc)
        full_text = "".join(page.get_text() for page in doc)
        entry["total_chars"] = len(full_text)
        entry["avg_chars_per_page"] = round(len(full_text) / max(doc.page_count, 1), 1)
        entry["min_page_chars"] = min(densities) if densities else 0
        # 스캔본 의심: 텍스트밀도가 낮은 페이지 비중
        low_density_pages = [i + 1 for i, d in enumerate(densities) if d < 30]
        entry["low_density_page_count"] = len(low_density_pages)
        entry["low_density_pages_sample"] = low_density_pages[:10]

        entry["period_marker_hits"] = len(PERIOD_RE.findall(full_text))
        entry["surrender_reserve_generic_hits"] = len(GENERIC_SURRENDER_RE.findall(full_text))
        entry["company_type"] = "nonlife" if code in NONLIFE_CODES else "life"
        entry["target_section_hits"] = len(SECTION_RE.findall(full_text))
        entry["target_section_label"] = "7-2/7-3"
        # 순서역전 폴백: 일부사(KR0072/KR0097 등)는 raw text 추출 순서가 "라벨 먼저, 절번호 나중"
        # (박스/여백 레이아웃 탓). 앞뒤 60자 이내 "7-2"/"7-3" 존재만 근접판정으로 재확인.
        if entry["target_section_hits"] == 0:
            near_hits = 0
            for m in GENERIC_SURRENDER_RE.finditer(full_text):
                ctx = full_text[max(0, m.start() - 60):m.end() + 60]
                if re.search(r"7[-\s]?[23]", ctx):
                    near_hits += 1
            entry["target_section_hits_proximity_fallback"] = near_hits

        # "해약환급금준비금" 뒤 200자 내 숫자(1자리 이상, "-" 포함) 존재 = 표 바디로 판정.
        # 억원 단위라 콤마 없는 2~4자리 숫자가 정상(과거 콤마-only 정규식이 오탐, 2026-09-03 수정)
        has_body = False
        for m in GENERIC_SURRENDER_RE.finditer(full_text):
            window = full_text[m.end():m.end() + 200]
            if re.search(r"\d", window) or re.search(r"\s-\s", window):
                has_body = True
                break
        entry["surrender_section_has_numeric_body"] = has_body

        doc.close()
        results[code] = entry

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    # 요약 출력
    total = len(results)
    with_target_section = sum(1 for v in results.values() if v.get("target_section_hits", 0) > 0)
    with_numeric_body = sum(1 for v in results.values() if v.get("surrender_section_has_numeric_body"))
    with_period = sum(1 for v in results.values() if v.get("period_marker_hits", 0) > 0)
    scanned_suspect = sum(1 for v in results.values() if v.get("low_density_page_count", 0) > 0)

    print(f"총 {total}사 검증")
    print(f"  기간마커('2026년2/4분기' 등) 검출: {with_period}/{total}")
    print(f"  대상 절(7-3/5-3) 헤더 검출: {with_target_section}/{total}")
    print(f"  해약환급금준비금 절 + 숫자표 바디 있음: {with_numeric_body}/{total}")
    print(f"  저밀도 페이지(스캔본 의심) 보유: {scanned_suspect}/{total}")
    print()
    print("=== 대상 절 미검출 회사 목록 ===")
    for code in all_codes:
        v = results[code]
        if v.get("target_section_hits", 0) == 0:
            print(f"  {code} [{v['company_type']}] {v['file']} pages={v.get('page_count')} "
                  f"generic_hits={v.get('surrender_reserve_generic_hits')}")
    print()
    print(f"산출: {OUT}")


if __name__ == "__main__":
    main()
