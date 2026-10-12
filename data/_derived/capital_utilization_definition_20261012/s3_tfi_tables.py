"""Step 3: read the issuer-printed 「(1) 공통적용 경과조치」 (TFI) table from every 2026.2Q MD (read-only).

For each company prints both columns (경과조치 적용 전 / 적용 후) of:
  지급여력금액, 기본자본, 보완자본, 보완자본 한도 적용 전, 보완자본 한도, 해약환급금 부족분 초과분,
  (기발행 신종자본증권), (기발행 후순위채무), 지급여력기준금액
and derives the issuer's own netting convention.
Output: s3_tfi_tables.json, s3_tfi_tables.txt

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_definition_20261012/s3_tfi_tables.py
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MD_DIR = REPO / "md_inbox" / "FY2026_Q2"

LAB = [
    ("ratio", r"^지급여력비율"),
    ("total", r"^지급여력금액$"),
    ("t1", r"^기본자본$"),
    ("t2", r"^보완자본$"),
    ("pre_limit", r"^보완자본한도적용전"),
    ("limit", r"^보완자본한도$"),
    ("lapse", r"^해약환급금부족분"),
    ("leg_hyb", r"^\(?기발행신종자본증권"),
    ("leg_sub", r"^\(?기발행후순위채무"),
    ("scr", r"^지급여력기준금액"),
]
UNIT_RE = re.compile(r"단위\s*[:：]?\s*(억원|백만원|천원|원)")


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def num(s: str):
    s = s.strip()
    if s == "":
        return None
    if s in ("-", "−", "—", "△-"):
        return 0.0
    t = s.replace(",", "").replace(" ", "")
    neg = (t.startswith("(") and t.endswith(")")) or t.startswith("△") or t.startswith("-")
    t = t.strip("()").lstrip("△-")
    try:
        v = float(t)
    except ValueError:
        return "TEXT:" + s
    return -v if neg else v


def main() -> int:
    out = {}
    lines_txt = []
    for p in sorted(MD_DIR.glob("KR*.md")):
        code = p.name[:6]
        lines = p.read_text(encoding="utf-8").split("\n")
        anchor = None
        for i, l in enumerate(lines):
            if l.startswith("|"):
                c = [x.strip() for x in l.strip().strip("|").split("|")]
                if re.match(r"^보완자본한도적용전", norm(c[0])):
                    anchor = i
                    break
        if anchor is None:
            out[code] = {"status": "NO_TFI_ANCHOR"}
            lines_txt.append(f"{code} NO_TFI_ANCHOR")
            continue
        unit = None
        for k in range(anchor, max(0, anchor - 40), -1):
            m = UNIT_RE.search(lines[k].replace(" ", ""))
            if m:
                unit = m.group(1)
                break
        got = {}
        header = None
        for k in range(max(0, anchor - 12), min(len(lines), anchor + 12)):
            if not lines[k].startswith("|"):
                continue
            c = [x.strip() for x in lines[k].strip().strip("|").split("|")]
            lab = norm(c[0])
            if header is None and ("적용" in "".join(c[1:]) or "구분" in lab):
                header = c
            for key, pat in LAB:
                if re.match(pat, lab) and key not in got:
                    got[key] = [num(x) for x in c[1:]]
        scale = {"억원": 1.0, "백만원": 0.01, "천원": 1e-5, "원": 1e-8}.get(unit, 0.01)
        rec = {"status": "OK", "unit": unit, "header": header, "anchor_line": anchor + 1, "rows": got}
        # columns: first = 적용 전, last = 적용 후 (if 2 columns)
        def col(key, idx):
            v = got.get(key)
            if not v or len(v) <= idx and idx != -1:
                return None
            x = v[idx] if v else None
            return round(x * scale, 2) if isinstance(x, float) else x
        rec["pre"] = {k: col(k, 0) for k, _ in LAB}
        rec["post"] = {k: (col(k, -1) if got.get(k) and len(got[k]) > 1 else None) for k, _ in LAB}
        out[code] = rec
        pr, po = rec["pre"], rec["post"]
        lines_txt.append(
            f"{code} unit={unit} L{anchor+1} hdr={header}\n"
            f"   PRE : tot={pr['total']} t1={pr['t1']} t2={pr['t2']} preLim={pr['pre_limit']} lim={pr['limit']} lapse={pr['lapse']} legH={pr['leg_hyb']} legS={pr['leg_sub']} scr={pr['scr']}\n"
            f"   POST: tot={po['total']} t1={po['t1']} t2={po['t2']} preLim={po['pre_limit']} lim={po['limit']} lapse={po['lapse']} legH={po['leg_hyb']} legS={po['leg_sub']} scr={po['scr']}")
    (HERE / "s3_tfi_tables.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "s3_tfi_tables.txt").write_text("\n".join(lines_txt) + "\n", encoding="utf-8")
    print("\n".join(lines_txt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
