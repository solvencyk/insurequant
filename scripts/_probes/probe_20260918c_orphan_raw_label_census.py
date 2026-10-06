# -*- coding: utf-8 -*-
"""For each orphan-parent bucket, census the raw DART XML for the labels that would
yield item2/3/8 (생명장기 손익 / 원수손익 / 재보험손익).

Prints per-filing hit counts for every known label variant so that an
"ABSENT_IN_SOURCE" verdict rests on a full variant sweep, not a single keyword.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]

BUCKETS = [
    ("KR0002", "2023.1Q"), ("KR0002", "2023.2Q"),
    ("KR0003", "2023.2Q"), ("KR0003", "2023.3Q"),
    ("KR0004", "2023.4Q"), ("KR0004", "2024.4Q"), ("KR0004", "2025.4Q"),
    ("KR0005", "2023.2Q"),
    ("KR0029", "2023.4Q"), ("KR0029", "2024.4Q"), ("KR0029", "2025.4Q"),
    ("KR0068", "2023.1Q"), ("KR0068", "2023.2Q"),
    ("KR0069", "2023.1Q"), ("KR0069", "2023.2Q"),
    ("KR0071", "2023.1Q"), ("KR0071", "2023.2Q"),
    ("KR0073", "2023.1Q"), ("KR0073", "2023.2Q"),
    ("KR0074", "2023.4Q"),
    ("KR0075", "2023.4Q"),
    ("KR0083", "2023.1Q"), ("KR0083", "2023.2Q"),
    ("KR0094", "2023.1Q"), ("KR0094", "2023.2Q"),
    ("KR0095", "2023.4Q"),
    ("KR0097", "2023.4Q"),
    ("KR0104", "2023.1Q"), ("KR0104", "2023.2Q"),
]

LABELS = [
    # LOB-level (손보) — parent #2 as a disclosed line
    "장기보험", "장기손익", "장기.보험손익", "생명장기",
    "계약유형별", "보험종목별", "부문별", "영업부문",
    # 원수/재보험 grand totals -> item3 / item8
    "보험수익", "보험서비스비용", "보험서비스결과",
    "재보험수익", "재보험서비스비용", "재보험계약", "출재",
    "보유계약순액", "재보험료비용", "재보험금수익",
    # note captions
    "보험료배분접근법", "보험계약마진",
]


def quarter_to_fy(q):
    year, qq = q.split(".")
    return f"FY{year}_Q{qq[0]}"


def find_xml(code, quarter):
    fy = ROOT / "data" / "dart" / quarter_to_fy(quarter) / "raw"
    out = []
    if not fy.is_dir():
        return out
    for sub in sorted(fy.iterdir()):
        if not sub.is_dir() or not sub.name.startswith(code + "_"):
            continue
        out.extend(sorted(sub.rglob("*.xml")))
    return out


TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")

for code, quarter in BUCKETS:
    xmls = find_xml(code, quarter)
    print(f"### {code} {quarter}  ({len(xmls)} xml)")
    if not xmls:
        print("   !! NO RAW XML")
        continue
    for x in xmls:
        raw = x.read_text(encoding="utf-8", errors="replace")
        docname = ""
        m = re.search(r"<DOCUMENT-NAME[^>]*>([^<]*)</DOCUMENT-NAME>", raw)
        if m:
            docname = m.group(1)
        txt = WS.sub("", TAG.sub(" ", raw))
        hits = []
        for lab in LABELS:
            n = len(re.findall(lab, txt))
            if n:
                hits.append(f"{lab}={n}")
        print(f"   {x.parent.parent.name if x.parent.name=='xml' else x.parent.name}/{x.name} "
              f"[{docname}] {len(raw)//1024}KB")
        print(f"      " + (", ".join(hits) if hits else "(no label hits)"))
    print()
