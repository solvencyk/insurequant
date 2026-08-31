import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

print("=== IFRS17_BS.json item numbering (sample rows) ===")
bs = json.load(open(ROOT / "IFRS17_BS.json", encoding="utf-8"))
seen_items = {}
for r in bs:
    if r["항목번호"] not in seen_items:
        seen_items[r["항목번호"]] = (r["항목명"], r["섹션"])
for k in sorted(seen_items):
    print(k, seen_items[k])

# find a KR0001 row for 자산총계 to check unit/magnitude
print("\nKR0001 2026.1Q or latest rows:")
kr1_rows = [r for r in bs if r["원보험사코드"] == "KR0001"]
quarters = sorted(set(r["공시분기"] for r in kr1_rows))
print("quarters available:", quarters[-3:])
latest_q = quarters[-1]
for r in kr1_rows:
    if r["공시분기"] == latest_q:
        print(r["항목번호"], r["항목명"], r["값"])

print("\n=== PL_breakdown.json item numbering (sample) ===")
pl = json.load(open(ROOT / "PL_breakdown.json", encoding="utf-8"))
print("type:", type(pl), "len:", len(pl) if isinstance(pl, list) else list(pl.keys())[:5])
if isinstance(pl, list):
    print("keys:", list(pl[0].keys()))
    print(json.dumps(pl[0], ensure_ascii=False, indent=2)[:800])
