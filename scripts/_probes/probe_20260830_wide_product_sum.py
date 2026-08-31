"""Manually reconstruct the 6-item CSM waterfall from the WIDE product-segmented
table (5 products x [PV,RA,CSM1,CSM2,CSM3] cols) for a given company/quarter raw
dir, independent of block_stages()/extract_stages() (which return None for item5
in some quarters). Read-only: only imports blocks_for_dir.
"""
import sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import blocks_for_dir

def parse_num(s):
    if s is None:
        return None
    s = str(s).strip()
    if s in ("", "-", "—"):
        return 0.0
    neg = s.startswith("(") and s.endswith(")")
    s2 = re.sub(r"[(),\s]", "", s)
    try:
        v = float(s2)
    except ValueError:
        return None
    return -v if neg else v

def csm_sum_5products(row_values):
    """row_values = 25 numbers (5 products x [PV,RA,CSM1,CSM2,CSM3]). Returns sum of
    the 5 products' CSM (=CSM1+CSM2+CSM3 each)."""
    total = 0.0
    for p in range(5):
        base = p * 5
        csm = row_values[base+2] + row_values[base+3] + row_values[base+4]
        total += csm
    return total

# label -> item number (matched against first 1-2 cells of a row)
ROW_LABELS = {
    "부채인 보험계약의 기초 장부금액": 1,
    "처음 인식한 계약의 효과": 2,
    "당기손익인식 보험금융손익": 3,
    "보험계약마진을 조정하는 변동": 4,
    "보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진": 5,
    "부채인 보험계약의 기말 장부금액": 6,
}

def process(rd_rel, name, label):
    rd = ROOT / rd_rel
    blocks = blocks_for_dir(rd, name)
    print(f"\n===== {label}  ({rd_rel}) — {len(blocks)} blocks =====")
    # find the WIDE block: header mentions 계약의 유형/사망보험 등
    wide = None
    for b in blocks:
        header = b.get("header") or []
        flat = " ".join(c for row in header for c in row)
        if "사망보험" in flat and "건강보험" in flat:
            wide = b
            break
    if wide is None:
        print("  NO WIDE block found among", len(blocks), "blocks")
        return
    rows = wide.get("rows") or []
    found = {}
    for r in rows:
        if not r:
            continue
        # try matching cell 0 or cell 1 against ROW_LABELS
        matched_item = None
        val_start = None
        for idx in (0, 1):
            if idx < len(r) and (r[idx] or "").strip() in ROW_LABELS:
                matched_item = ROW_LABELS[(r[idx] or "").strip()]
                val_start = idx + 1
                break
        if matched_item is None:
            continue
        nums = [parse_num(x) for x in r[val_start:]]
        if len(nums) < 25 or any(n is None for n in nums):
            print(f"  [WARN] row for item {matched_item} has {len(nums)} numeric cells (need 25): {r[:3]}...")
            continue
        s = csm_sum_5products(nums)
        found[matched_item] = s
    print("  found items (원):", found)
    print("  found items (억원):", {k: round(v/1e8, 2) for k, v in found.items()})

# KR0079 2025.2Q / 2025.3Q / 2026.1Q -- product slug names differ by quarter dir naming
process("data/dart/FY2025_Q2/raw/KR0079_미래에셋생명", "KR0079_미래에셋생명", "KR0079 2025.2Q")
process("data/dart/FY2025_Q3/raw/KR0079_미래에셋생명", "KR0079_미래에셋생명", "KR0079 2025.3Q")
process("data/dart/FY2026_Q1/raw/KR0079_미래에셋생명", "KR0079_미래에셋생명", "KR0079 2026.1Q")

process("data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664", "KR0079_미래에셋생명", "KR0079 2025.4Q (annual)")
