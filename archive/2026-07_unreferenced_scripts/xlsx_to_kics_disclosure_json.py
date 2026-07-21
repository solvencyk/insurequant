"""kics_disclosure.xlsx -> kics_disclosure.json (repo root). Backs up existing JSON first."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "kics_disclosure.xlsx"
OUT = ROOT / "kics_disclosure.json"
EXPECTED = [
    "원보험사코드",
    "원수사명",
    "티커",
    "생손보여부",
    "항목번호",
    "항목명",
    "공시분기",
    "값",
]


def main() -> int:
    if not XLSX.is_file():
        raise SystemExit(f"Missing {XLSX}")

    df = pd.read_excel(XLSX, engine="openpyxl")
    if len(df.columns) == 8:
        df.columns = EXPECTED
    else:
        missing = [c for c in EXPECTED if c not in df.columns]
        if missing:
            raise SystemExit(f"column mismatch: {list(df.columns)}")

    df = df.dropna(how="all")

    def to_str(v) -> str:
        if pd.isna(v):
            return ""
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v).strip()

    def to_item_no(v) -> int:
        if pd.isna(v):
            raise ValueError("empty 항목번호")
        return int(round(float(v)))

    records: list[dict] = []
    for _, row in df.iterrows():
        if all(to_str(row[c]) == "" for c in EXPECTED):
            continue
        records.append(
            {
                "원보험사코드": to_str(row["원보험사코드"]),
                "원수사명": to_str(row["원수사명"]),
                "티커": to_str(row["티커"]),
                "생손보여부": to_str(row["생손보여부"]),
                "항목번호": to_item_no(row["항목번호"]),
                "항목명": to_str(row["항목명"]),
                "공시분기": to_str(row["공시분기"]),
                "값": to_str(row["값"]),
            }
        )

    if OUT.is_file():
        backup = OUT.with_suffix(
            OUT.suffix + f".bak_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
        )
        shutil.copy2(OUT, backup)
        print(f"backup: {backup.name}")

    OUT.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote {OUT.name} rows={len(records)} (from {XLSX.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
