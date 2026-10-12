"""c3_dart_sections.py (parser-kics, ticket 20261012T1230Z) -- READ ONLY on data/dart; writes only dart_sections/*.txt next to this script.

For every company that has a 신종자본증권 / 후순위채 (inventory c1) or a K-ICS item 6 / 53 / 54 > 0, find its local DART reports
(annual 사업보고서 FY2023..FY2025 = FYyyyy_Q4, 반기보고서 FY2026_Q2, plus 분기/반기 of 2023 for the earliest snapshot) and dump the sections that
carry the issuer's own wording about capital-recognised debt:
   "자본으로 인정되는 채무증권의 발행"  (사업보고서 III.4.라 - per-bond: 발행일, 발행금액, 자본인정에 관한 사항, 만기 및 조기상환 가능일,
                                        발행금리, 우선순위, 기타 중요한 발행조건 = step-up / 이자지급 재량 ...)
   "신종자본증권" notes of the financial statements (이자율 조정 / 스텝업 / 조기상환 설명)
Each dump line = "LINE_NO | text" of dart_text.to_lines().  Output file name: <code>_<period>_<xml stem>.txt (one per XML with hits).

Run (repo root): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/c3_dart_sections.py [CODE ...]
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
from dart_text import read_xml, to_lines  # noqa: E402

OUT = HERE / "dart_sections"
OUT.mkdir(exist_ok=True)
inv = json.loads((HERE / "census_inventory.json").read_text(encoding="utf-8"))["rows"]
codes = sorted({r["code"] for r in inv})
if len(sys.argv) > 1:
    codes = sys.argv[1:]

PERIODS = ["FY2023_Q1", "FY2023_Q2", "FY2023_Q4", "FY2024_Q2", "FY2024_Q4", "FY2025_Q2", "FY2025_Q4", "FY2026_Q2"]
HEAD = re.compile(r"자본으로\s*인정되는\s*채무증권")
NOTE = re.compile(r"스텝업|Step-up|step-up|STEP-UP|이자율이 조정|금리가 조정|가산금리|조기상환권|콜옵션|이자지급.{0,6}(재량|정지|유예)|지급\s*정지|누적적|비누적")
SIZE_MIN = 300_000  # main report bodies are MBs; skip tiny notes


def reports(code):
    out = []
    for p in PERIODS:
        d = REPO / "data" / "dart" / p / "raw"
        if not d.is_dir():
            continue
        for sub in sorted(d.iterdir()):
            if sub.is_dir() and sub.name.startswith(code):
                xs = [x for x in sub.glob("*.xml") if x.stat().st_size >= SIZE_MIN]
                for x in sorted(xs, key=lambda z: -z.stat().st_size)[:1]:
                    out.append((p, sub.name, x))
    return out


for code in codes:
    rs = reports(code)
    print(f"== {code}: {len(rs)} xml files")
    for p, sub, x in rs:
        t0 = time.time()
        try:
            lines = to_lines(read_xml(x))
        except Exception as exc:  # noqa: BLE001
            print("   ERR", x.name, exc)
            continue
        head_idx = [i for i, ln in enumerate(lines) if HEAD.search(ln) and len(ln) < 60]
        blocks = []
        for i in head_idx:
            j = i + 1
            while j < len(lines) and j - i < 700:
                if re.match(r"^(마|바|사)\.\s", lines[j]) or re.match(r"^\d+\.\s+[가-힣]", lines[j]) and j - i > 15:
                    break
                j += 1
            blocks.append((i, j))
        note_idx = [i for i, ln in enumerate(lines) if NOTE.search(ln) and ("신종" in ln or "자본증권" in ln or "후순위" in ln)]
        if not blocks and not note_idx:
            print(f"   {p} {x.name}: nothing ({round(time.time() - t0, 1)}s)")
            continue
        fn = OUT / f"{code}_{p}_{x.stem}.txt"
        with open(fn, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(f"# {x.relative_to(REPO)} | {len(lines)} lines | sections 'capital-recognised debt': {len(blocks)} | note hits: {len(note_idx)}\n")
            for (i, j) in blocks:
                fh.write(f"\n## SECTION lines {i + 1}-{j} (heading: {lines[i][:60]})\n")
                for k in range(i, j):
                    fh.write(f"{k + 1:>6} | {lines[k][:900]}\n")
            fh.write("\n## NOTE HITS (lines mentioning step-up / rate adjustment / call / interest suspension together with 신종·자본증권·후순위)\n")
            for k in note_idx[:80]:
                fh.write(f"{k + 1:>6} | {lines[k][:900]}\n")
        print(f"   {p} {x.name}: sections={len(blocks)} note_hits={len(note_idx)} -> {fn.name} ({round(time.time() - t0, 1)}s)")
