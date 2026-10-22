# -*- coding: utf-8 -*-
"""Independent raw scan (does NOT import scripts/ or src/): where do the competing FY-opening CSM values of the
failing single-quarter buckets appear in the DART XML filings on disk?  For every number token in a filing we test
the 억원 value under the 원 / 천원 / 백만원 scales against each target (tol 0.06억 = 1-decimal rounding) and print the
hit with the nearest preceding caption-like line, so we can tell whether a later filing prints a restated comparative.
Read-only; writes s4_raw_scan.txt."""
import re, glob, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DART = ROOT / "data" / "dart"
TARGETS = {
    "KR0001": {"periods": ["FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2023_Q4", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3"],
               "vals": {"A_open_1Q2Q": 100383.8, "B_open_3Q4Q": 96376.4, "close_2023.2Q": 100684.2, "close_2023.1Q": 100033.5,
                        "close_2023.3Q": 103383.0}},
    "KR0068": {"periods": ["FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2023_Q4", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3"],
               "vals": {"A_open_1Q2Q": 96679.3, "B_open_3Q4Q": 97629.5, "close_2023.2Q": 101167.4, "close_2023.1Q": 97125.1,
                        "close_2023.3Q": 97991.1}},
    "KR0099": {"periods": ["FY2023_Q3", "FY2023_Q4", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"],
               "vals": {"A_open_1Q3Q": 31201.3, "B_open_4Q": 31327.6, "close_2023.3Q": 32139.5, "close_2023.4Q": 30176.4}},
    "KR0003": {"periods": ["FY2024_Q3", "FY2024_Q4", "FY2025_Q1", "FY2025_Q2", "FY2025_Q3", "FY2025_Q4"],
               "vals": {"A_open_1Q3Q(=2023.4Q close)": 23966.2, "B_open_4Q": 23860.8, "close_2024.3Q": 24529.9,
                        "close_2024.4Q": 23201.6}},
}
NUM = re.compile(r"\(?-?\d{1,3}(?:,\d{3})+\)?|\(?-?\d{4,}\)?")
CAP = re.compile(r"보험계약마진|당분기|전분기|당반기|전반기|당기|전기|<TITLE|구\s*분")
TAG = re.compile(r"<[^>]+>")
out = []; P = out.append
def read(p):
    b = p.read_bytes()
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    return b.decode("utf-8", "replace")
for code, spec in TARGETS.items():
    for per in spec["periods"]:
        files = sorted(glob.glob(str(DART / per / "raw" / f"{code}_*" / "*.xml")) +
                       glob.glob(str(DART / per / "raw" / f"{code}_*" / "xml" / "*.xml")))
        files = [f for f in files if not re.search(r"_0076\d\.xml$", f)]  # attachments (audit reports) skipped
        for f in files:
            lines = read(pathlib.Path(f)).splitlines()
            last_cap = ""
            hits = []
            for i, ln in enumerate(lines, 1):
                txt = TAG.sub(" ", ln)
                if CAP.search(ln) and len(txt.strip()) < 220 and ("보험계약마진" in txt or "TITLE" in ln or "당" in txt or "전" in txt):
                    if "보험계약마진" in txt or "TITLE" in ln:
                        last_cap = (str(i) + ": " + re.sub(r"\s+", " ", txt).strip())[:150]
                for tok in NUM.findall(txt):
                    raw = tok.strip("()").replace(",", "")
                    try:
                        v = float(raw)
                    except ValueError:
                        continue
                    for lab, tgt in spec["vals"].items():
                        for scale, div in (("백만원", 1e2), ("천원", 1e5), ("원", 1e8)):
                            if abs(v / div - tgt) <= 0.06:
                                hits.append((i, lab, tok, scale, last_cap))
            P(f"== {code} {per} {pathlib.Path(f).name} lines={len(lines)} hits={len(hits)}")
            seen = set()
            for i, lab, tok, scale, cap in hits:
                k = (lab, cap)
                if k in seen:
                    continue
                seen.add(k)
                P(f"   L{i} {lab} = {tok} [{scale}]  cap<{cap}>")
(HERE / "s4_raw_scan.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
