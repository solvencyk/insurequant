import sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context

xml_path = ROOT / "data/dart/FY2023_Q1/raw/KR0079_미래에셋생명/xml/20230515002900.xml"
tables = list(_iter_tables_with_context(xml_path))
by_line = {t.line_no: t for t in tables}

TARGET_LINES = {
    "사망": 15088, "건강": 15755, "연금": 16425, "저축": 17092, "기타": 17756,
}

def parse_num(s):
    if s is None:
        return None
    s = s.strip()
    if s in ("", "-", "—"):
        return 0.0
    neg = s.startswith("(") and s.endswith(")")
    s2 = re.sub(r"[(),\s]", "", s)
    s2 = s2.replace(")", "").replace("%", "")
    try:
        v = float(s2)
    except ValueError:
        return None
    return -v if neg else v

# Row-label -> item number, matched by the row's FIRST cell (or first cell if it's
# a plain label with 7 trailing numeric values), scoped to the "당분기" section only
# (stop once we hit "전분기").
ROW_MAP = {
    "기초 잔액": 1,
    "처음 인식한 계약의 효과": 2,
    "당기손익인식 보험금융손익": 3,
    "보험계약마진을 조정하는 변동": 4,
    "보험계약마진의 당기인식분": 5,
    "기말 잔액": 6,
}

totals = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0}
per_product = {}

for prod, ln in TARGET_LINES.items():
    t = by_line[ln]
    rows = t.rows
    in_current = False
    seen_first_gijo = 0  # 기초 잔액 appears in both 당분기 and 전분기; use section flag
    vals = {}
    for r in rows:
        if not r:
            continue
        label0 = (r[0] or "").strip()
        if label0 == "당분기":
            in_current = True
            continue
        if label0 == "전분기":
            in_current = False
            continue
        if not in_current:
            continue
        # numeric tail = last 7 cells (label[, sublabel], v1..v7)
        tail = r[-7:] if len(r) >= 7 else None
        if tail is None:
            continue
        nums = [parse_num(x) for x in tail]
        if any(n is None for n in nums):
            continue
        csm_subtotal = nums[5]  # index: PV,RA,CSM1,CSM2,CSM3,CSM_subtot,TOTAL -> idx5=CSM subtotal
        # match label against known rows -- check every cell in the row (label or sublabel)
        matched_item = None
        for cell in r[:2]:
            c = (cell or "").strip()
            if c in ROW_MAP:
                matched_item = ROW_MAP[c]
                break
        if matched_item:
            vals[matched_item] = csm_subtotal
    per_product[prod] = vals
    print(f"{prod}: {vals}")
    for k, v in vals.items():
        totals[k] += v

print("\nSUM across 5 products (백만원):", totals)
print("SUM in 억원:", {k: round(v/100, 2) for k, v in totals.items()})

print("\nGold values (KR0079 2023.1Q, 억원): {1: 19794.95, 2: 572.47, 3: 116.0, 4: 105.28, 5: -520.14, 6: 20068.56}")
