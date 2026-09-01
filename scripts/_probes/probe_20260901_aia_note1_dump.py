"""Dump AIA's '1. 일반사항' note prose in full for FY2022/FY2023/FY2024 filings."""
from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

TARGETS = {
    "2022.4Q": "data/dart/FY2022_Q4/raw/KR0080_에이아이에이생명보험_20230410002773",
    "2023.4Q": "data/dart/FY2023_Q4/raw/KR0080_에이아이에이생명보험_20240409002583",
    "2024.4Q": "data/dart/FY2024_Q4/raw/KR0080_에이아이에이생명보험_20250401000094",
}


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", s).strip()


for q, d in TARGETS.items():
    print("=" * 110)
    print(f"### {q}   {d}")
    for x in sorted(glob.glob(str(ROOT / d) + "/*.xml")):
        raw = open(x, "rb").read().decode("utf-8")
        # find "1. 일반사항" then print the following ~4000 chars of stripped text
        m = re.search(r"1\.\s*일반사항", raw)
        if not m:
            print("   no '1. 일반사항' marker")
        else:
            seg = strip_tags(raw[m.start(): m.start() + 12000])
            print("   [1.일반사항 +12k chars stripped]")
            print("   " + seg[:4500])
        print()
        # also: every sentence containing 영업이익 / 당기순이익 / 보험손익 / 투자손익
        flat = strip_tags(raw)
        print("   --- sentences mentioning the PL words ---")
        seen = set()
        for sent in re.split(r"(?<=다\.)\s*", flat):
            if any(w in sent for w in ("영업이익", "당기순이익", "보험손익", "투자손익",
                                        "보험계약마진은", "위험조정은")):
                s = sent.strip()
                if len(s) > 8 and s not in seen:
                    seen.add(s)
                    print("     * " + s[:600])
