"""Bundle all root master tables into one reviewable .xlsx (one sheet per master).

Output: insurequant_master_tables.xlsx (repo root).
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "insurequant_master_tables.xlsx"
FONT = "맑은 고딕"

# (json file, sheet name, description) — only real masters (diff snapshots excluded)
MASTERS = [
    ("IFRS17_BS.json", "17BS",
     "재무상태표 요약 (자산총계·부채총계·자본총계·AOCI누계액·법정준비금 3종 = 항목 1-7) long-format"),
    ("kics_disclosure.json", "K-ICS공시",
     "K-ICS 지급여력 공시 항목 (요구자본 1-35 + 시장위험 하위분해 36-46) long-format"),
    ("kics_rate_sensitivity.json", "금리민감도",
     "지급여력 금리민감도 (경과조치 적용전/후 x measure x base/±50/±100bp)"),
    ("CSM_waterfall.json", "CSM워터폴",
     "CSM 변동분석 (기초→신계약→이자부리→가정·경험조정→상각→기말)"),
    ("CSM_amortization.json", "CSM상각",
     "CSM 경과연차별 상각 스케줄"),
    ("NB_CSM_multiple.json", "신계약CSM배수",
     "신계약 CSM / 월납초회보험료 배수 (연누계)"),
    ("PL_breakdown.json", "손익분해PL",
     "손익계산서 24항목 분해 (보험·투자손익 등)"),
    ("dividend.json", "배당",
     "배당에 관한 사항 (DART alotMatter) — 항목1-7 회사단위 + 8-11 종류주(보통주/우선주)별"),
]

NUMERIC_COLS = {"값", "-100bp", "-50bp", "base", "+50bp", "+100bp",
                "상각액", "신계약CSM_연누계", "월납월초보험료_연누계", "신계약CSM배수_연누계"}
TEXT_COLS = {"원보험사코드", "원수사명", "티커", "생손보여부", "공시분기",
             "항목명", "경과조치여부", "measure구분", "경과차년", "종류주", "섹션", "레벨"}


def coerce(df):
    for c in df.columns:
        if c in NUMERIC_COLS:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        elif c == "항목번호":
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        else:
            df[c] = df[c].astype("string")
    return df


def main():
    frames = []
    for fn, sheet, desc in MASTERS:
        data = json.loads((REPO / fn).read_text(encoding="utf-8"))
        df = pd.DataFrame(data)
        df = coerce(df)
        frames.append((sheet, df, fn, desc))

    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        # placeholder index first (filled after we know counts)
        pd.DataFrame({"_": []}).to_excel(xw, sheet_name="요약", index=False)
        for sheet, df, _fn, _desc in frames:
            df.to_excel(xw, sheet_name=sheet, index=False)

    wb = load_workbook(OUT)

    # ---- 요약 (index) sheet ----
    idx = wb["요약"]
    idx.delete_cols(1, 4)
    idx["A1"] = "Insurequant 마스터테이블 통합"
    idx["A1"].font = Font(name=FONT, bold=True, size=14)
    headers = ["시트", "마스터 파일", "행수", "설명"]
    idx.append([])
    idx.append(headers)
    hdr_row = 3
    for sheet, df, fn, desc in frames:
        idx.append([sheet, fn, len(df), desc])
    idx.append(["합계", "", sum(len(df) for _s, df, _f, _d in frames), ""])
    # style index
    for c in range(1, 5):
        cell = idx.cell(row=hdr_row, column=c)
        cell.font = Font(name=FONT, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="305496")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    total_row = hdr_row + 1 + len(frames)
    for r in range(hdr_row + 1, total_row + 1):
        bold = (r == total_row)
        for c in range(1, 5):
            idx.cell(row=r, column=c).font = Font(name=FONT, bold=bold)
        idx.cell(row=r, column=3).alignment = Alignment(horizontal="right")
        idx.cell(row=r, column=3).number_format = "#,##0"
    idx.column_dimensions["A"].width = 16
    idx.column_dimensions["B"].width = 30
    idx.column_dimensions["C"].width = 10
    idx.column_dimensions["D"].width = 70
    idx.sheet_view.showGridLines = False

    # ---- data sheets ----
    thin = Side(style="thin", color="D9D9D9")
    for sheet, df, _fn, _desc in frames:
        ws = wb[sheet]
        ncol = ws.max_column
        nrow = ws.max_row
        # header style
        for c in range(1, ncol + 1):
            cell = ws.cell(row=1, column=c)
            cell.font = Font(name=FONT, bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="305496")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(bottom=thin)
        # body font + number format
        cols = [ws.cell(row=1, column=c).value for c in range(1, ncol + 1)]
        for c, name in enumerate(cols, start=1):
            letter = ws.cell(row=1, column=c).column_letter
            for r in range(2, nrow + 1):
                cl = ws.cell(row=r, column=c)
                cl.font = Font(name=FONT)
                if name in NUMERIC_COLS and isinstance(cl.value, (int, float)):
                    cl.number_format = "#,##0.##;(#,##0.##);-"
            # column width (approx from header + name length)
            base_w = {"원수사명": 22, "항목명": 30, "설명": 60}.get(name, 0)
            ws.column_dimensions[letter].width = base_w or max(11, min(28, len(str(name)) + 6))
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=ncol).column_letter}{nrow}"

    # order: 요약 first
    wb.move_sheet("요약", -(wb.sheetnames.index("요약")))
    wb.save(OUT)
    print(f"wrote {OUT.name}: {len(frames)} master sheets + 요약")
    for sheet, df, _fn, _desc in frames:
        print(f"  {sheet:14s} {len(df):6d} rows x {len(df.columns)} cols")


if __name__ == "__main__":
    main()
