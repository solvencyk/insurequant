"""n2_copy_evidence_images.py -- copy the rendered PDF pages that were VIEWED for the caution-flag blocks into img/ with block-based names."""
import shutil
import sys
from pathlib import Path

SP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/e15a5832-0270-4430-8e3e-4cba8a1f182c/scratchpad/img")
DST = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012/img")
DST.mkdir(exist_ok=True)
MAP = {
    "KR0003_2025.1Q__own_FY2025_Q1_p18.png": "kr0003_q1_own_p18.png",
    "KR0003_2025.1Q__F+1_FY2025_Q2_p20.png": "kr0003_q2_p20.png",
    "KR0003_2025.1Q__F+2_FY2025_Q3_p20.png": "kr0003_q3_p20.png",
    "KR0003_2023.4Q__own_FY2023_Q4_amended_p41.png": "kr0003_2023q4_own_p41.png",
    "KR0004_2023.1Q__own_FY2023_Q1_p9.png": "kr0004_q1_own_p9.png",
    "KR0004_2023.1Q__F+1_FY2023_Q2_p11.png": "kr0004_q2_p11.png",
    "KR0004_2023.1Q__F+2_FY2023_Q3_p11.png": "kr0004_q3_p11.png",
    "KR0009_2023.1Q__own_FY2023_Q1_p9.png": "kr0009_q1_own_p9.png",
    "KR0009_2023.1Q__F+1_FY2023_Q2_p10.png": "kr0009_q2_p10.png",
    "KR0009_2023.1Q__F+2_FY2023_Q3_amended_p12.png": "kr0009_q3am_p12.png",
    "KR0049_2025.1Q__own_FY2025_Q1_p16_printed15.png": "axa_fy2025q1_p16.png",
    "KR0049_2026.1Q__own_FY2026_Q1_p16_printed15.png": "axa_fy2026q1_p16.png",
    "KR0050_2025.3Q__own_FY2025_Q3_p17.png": "kr0050_q3_own_p17.png",
    "KR0050_2025.3Q__F+1_FY2025_Q4_p53.png": "kr0050_q4_p53.png",
    "KR0050_2025.3Q__F+2_FY2026_Q1_p17.png": "kr0050_2026q1_p17.png",
    "KR0071_2024.4Q__own_FY2024_Q4_p48.png": "kr0071_fy2024q4_p48.png",
    "KR0080_2026.1Q__own_FY2026_Q1_p18.png": "kr0080_fy2026q1_p18.png",
}
tot = 0
for new, old in MAP.items():
    s = SP / old
    assert s.exists(), s
    shutil.copyfile(s, DST / new)
    tot += s.stat().st_size
print(len(MAP), "images copied,", round(tot / 1024), "KB")
