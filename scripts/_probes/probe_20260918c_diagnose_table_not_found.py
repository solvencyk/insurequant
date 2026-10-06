# -*- coding: utf-8 -*-
"""20260918 TABLE_NOT_FOUND 14칸 원인 진단 (레이아웃 변형 vs 스캔본).

키워드 0회로 '원문 없음' 단정 금지 (memory: keyword-absence-is-not-source-absence).
각 후보 페이지의 텍스트 밀도 + 라벨 4종(보험손익/투자손익/영업이익/당기순이익) 존재 여부를
따로 찍어서, "제목 문구만 다른가" vs "이 페이지 자체가 스캔본인가"를 가른다.

산출: data/_derived/_probe_20260918c_diagnosis.json (사람이 읽을 요약도 stdout)
"""
import fitz, os, io, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
fitz.TOOLS.mupdf_display_errors(False)

TARGETS = [
    ("KR0051", ["2024.1Q", "2024.2Q", "2024.3Q", "2025.1Q", "2025.2Q", "2026.1Q"]),
    ("KR0080", ["2025.1Q", "2025.2Q", "2025.3Q", "2026.1Q"]),
    ("KR0097", ["2024.2Q"]),
    ("KR1098", ["2024.2Q", "2024.3Q", "2025.1Q"]),
]

CORE_LABELS = ["보험손익", "투자손익", "영업이익", "당기순이익"]


def quarter_to_folder(q):
    fy, qq = q.split(".")
    qn = qq[0]
    return f"FY{fy}_Q{qn}"


def diagnose(pdf_path, max_pages=30):
    doc = fitz.open(pdf_path)
    n = doc.page_count
    per_page = []
    for i in range(min(max_pages, n)):
        t = doc[i].get_text()
        hits = [lab for lab in CORE_LABELS if lab in t]
        if len(t.strip()) > 30 or hits:
            per_page.append({"page": i + 1, "textlen": len(t), "label_hits": hits,
                              "has_title_kw": ("포괄손익계산서" in t)})
    doc.close()
    return n, per_page


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    report = []
    for code, quarters in TARGETS:
        for q in quarters:
            folder = quarter_to_folder(q)
            rawdir = os.path.join(ROOT, "data", "disclosure", folder, "raw")
            cands = [f for f in os.listdir(rawdir) if f.startswith(code + "_")] if os.path.isdir(rawdir) else []
            if not cands:
                report.append({"code": code, "quarter": q, "verdict": "NO_PDF_FILE"})
                continue
            pdf_path = os.path.join(rawdir, cands[0])
            try:
                npages, per_page = diagnose(pdf_path)
            except Exception as e:
                report.append({"code": code, "quarter": q, "verdict": "ERROR", "detail": str(e)[:200]})
                continue
            # 후보: 라벨 4종 중 3개 이상 잡히는 페이지
            strong = [p for p in per_page if len(p["label_hits"]) >= 3]
            weak = [p for p in per_page if 1 <= len(p["label_hits"]) < 3]
            avg_textlen_first10 = sum(p["textlen"] for p in per_page[:10]) / max(1, len(per_page[:10]))
            verdict = "SCAN_SUSPECT" if avg_textlen_first10 < 50 else (
                "STRONG_CANDIDATE_FOUND" if strong else (
                    "WEAK_CANDIDATE_ONLY" if weak else "NO_CANDIDATE_TEXT_OK"))
            report.append({
                "code": code, "quarter": q, "source_file": os.path.relpath(pdf_path, ROOT).replace("\\", "/"),
                "n_pages": npages, "avg_textlen_first10pages": round(avg_textlen_first10, 1),
                "verdict": verdict,
                "strong_pages": [p["page"] for p in strong],
                "weak_pages": [(p["page"], p["label_hits"]) for p in weak],
            })
    outp = os.path.join(ROOT, "data", "_derived", "_probe_20260918c_diagnosis.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    for r in report:
        print(r.get("code"), r.get("quarter"), "->", r.get("verdict"),
              "strong_pages=", r.get("strong_pages"), "weak_pages=", r.get("weak_pages"))
    print("\nwrote:", outp)


if __name__ == "__main__":
    main()
