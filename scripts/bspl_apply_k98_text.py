# -*- coding: utf-8 -*-
"""KR1098 (카카오페이손해보험) text-layer 8-1 balance sheets 2025.1Q..2026.2Q -> v2 transcription JSON (temporary helper)"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
import fitz  # noqa: E402
from bspl_granularity.pdfrows import rows_from_page  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = ROOT / "data/_derived/bspl_apply_20261011/vision/v2"
FYQ = {"2025.1Q": "FY2025_Q1", "2025.2Q": "FY2025_Q2", "2025.3Q": "FY2025_Q3", "2026.1Q": "FY2026_Q1", "2026.2Q": "FY2026_Q2"}
ROMAN = re.compile(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.")
ANC = {"10": "현금및현금성자산", "13": "금융자산", "14": "재보험계약자산", "15": "유형자산", "20": "보험계약부채", "24": "기타부채", "1": "자산총계", "2": "부채총계", "3": "자본총계",
       "4": "기타포괄손익누계액", "30": "자본금", "31": "이익잉여금결손금"}


def clean(label: str) -> str:
    s = label.replace(" ", "")
    s = re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.", "", s)
    s = re.sub(r"^\d+\.", "", s)
    s = re.sub(r"[\(\)]", "", s)
    return s


def find_bs(doc):
    best = None
    for i in range(len(doc)):
        flat = "".join(doc[i].get_text().split())
        if "자산총계" in flat and "부채총계" in flat and "자본총계" in flat and "현금및현금성자산" in flat and "보험계약부채" in flat:
            rows, _free = rows_from_page(doc[i], pageno=i + 1)
            if len(rows) >= 20:
                best = (i + 1, rows)
                break
    return best


def main():
    for q, fy in FYQ.items():
        f = sorted((ROOT / "data/disclosure" / fy / "raw").glob("KR1098_*.pdf"))
        f = [x for x in f if "_v20" not in x.name and "_amended" not in x.name and "attachment" not in x.name] or f
        doc = fitz.open(str(f[0]))
        res = find_bs(doc)
        if res is None:
            print(q, "NO BS PAGE", f[0].name)
            continue
        page, rows = res
        lines, top_assets, top_liabs, eq = {}, [], [], []
        sec = "A"
        raw0 = []
        for r in rows:
            lab = r.label
            vals = [v for v in r.vals]
            if not lab or not vals:
                continue
            c = clean(lab)
            if len(vals) < 2:
                continue
            cur, prior = vals[0], vals[1]
            if c.startswith("자산총계"):
                lines["자산총계"] = [int(cur), int(prior)]
                sec = "L"
                continue
            if c.startswith("부채총계"):
                lines["부채총계"] = [int(cur), int(prior)]
                sec = "E"
                continue
            if c.startswith("자본총계"):
                lines["자본총계"] = [int(cur), int(prior)]
                continue
            if c.startswith("부채및자본총계") or c.startswith("부채와자본총계"):
                lines["부채및자본총계"] = [int(cur), int(prior)]
                continue
            name = c
            lines[name] = [int(cur), int(prior)]
            if ROMAN.match(lab.replace(" ", "")):
                {"A": top_assets, "L": top_liabs, "E": eq}[sec].append(name)
            raw0.append((sec, lab, name, cur, prior))
        print("=====", q, f[0].name, "page", page)
        for sec, lab, name, cur, prior in raw0:
            print(f"   {sec} {lab[:30]:<30} {int(cur):>18,} {int(prior):>18,}")
        print("   top assets:", top_assets)
        print("   top liabs :", top_liabs)
        print("   equity    :", eq)
        sa = sum(lines[n][0] for n in top_assets)
        sl = sum(lines[n][0] for n in top_liabs)
        se = sum(lines[n][0] for n in eq)
        print("   sums cur:", sa - lines["자산총계"][0], sl - lines["부채총계"][0], se - lines["자본총계"][0])
        # structure checks for the zero proof
        assert "금융자산" in lines and "상각후원가측정금융자산" in lines and lines["금융자산"] == lines["상각후원가측정금융자산"], "금융자산 has other children"
        assert not any("재보험계약부채" in n for n in lines), "has 재보험계약부채 line"
        assert not any(("당기손익" in n or "기타포괄손익공정가치" in n or "기타포괄손익-공정가치" in n) for n in lines if n != "기타포괄손익누계액"), "FVPL/FVOCI line present"
        d = {
            "code": "KR1098", "quarter": q, "pdf": f[0].relative_to(ROOT).as_posix(), "page": page, "unit": "원", "scale": 1e-6, "tol_units": 1, "source_kind": "text",
            "read_by": "정기경영공시 8-1 재무상태표(텍스트층, geometry 행 복원 scripts/bspl_granularity/pdfrows.py). 「Ⅱ.금융자산」은 하위 줄 「1.상각후원가측정금융자산」 하나뿐이고 같은 금액",
            "cols": ["당기말", "전기말"], "lines": lines,
            "sums": [
                ["자산총계", top_assets, "자산총계 = 최상위 자산 줄 합(전 줄 열거; 금융자산 = 상각후원가측정금융자산 하나뿐)"],
                ["부채총계", top_liabs, "부채총계 = 최상위 부채 줄 합(전 줄 열거)"],
                ["자본총계", eq, "자본총계 = 자본 줄 합"],
                ["부채및자본총계", ["부채총계", "자본총계"], "자산 = 부채 + 자본"],
            ],
            "loads": [
                {"col": 0, "quarter": q, "zero": {"11": "당기손익-공정가치측정금융자산", "12": "기타포괄손익-공정가치측정금융자산"}, "closure": ["자산총계"]},
                {"col": 0, "quarter": q, "zero": {"21": "재보험계약부채"}, "closure": ["부채총계"]},
            ],
            "anchors": [{"col": 0, "quarter": q, "items": [10, 14, 15, 20, 24, 1, 2, 3, 4, 30, 31], "lines": {**ANC, "13": "상각후원가측정금융자산"}}],
            "note": "재보험계약부채·당기손익/기타포괄손익-공정가치측정금융자산 줄은 표에 없음(모든 줄 열거 + 폐합). 같은 회사 2023.1Q~2024.1Q·2024.4Q·2025.4Q 마스터의 0.0 칸과 같은 관례.",
        }
        (OUT / f"KR1098_{q}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("   wrote", f"KR1098_{q}.json")


main()
