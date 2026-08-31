import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
pl = json.load(open(ROOT / "PL_breakdown.json", encoding="utf-8"))

seen = {}
for r in pl:
    if r["항목번호"] not in seen:
        seen[r["항목번호"]] = r["항목명"]
for k in sorted(seen, key=lambda x: str(x)):
    print(k, seen[k])

print("\nsearch for 당기순이익-like labels:")
labels = set(r["항목명"] for r in pl)
for l in sorted(labels):
    if "순이익" in l or "순손익" in l:
        print(" ", l)

print("\nKR0001 2026.2Q rows (if present):")
rows = [r for r in pl if r["원보험사코드"] == "KR0001" and r["공시분기"] == "2026.2Q"]
for r in rows:
    print(r["항목번호"], r["항목명"], r["값"], r.get("값_당분기"))
if not rows:
    qs = sorted(set(r["공시분기"] for r in pl if r["원보험사코드"] == "KR0001"))
    print("no 2026.2Q; available quarters:", qs[-5:])
