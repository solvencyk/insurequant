"""Post-fix verification: KR0032 17BS <-> K-ICS residual on 이익잉여금 / AOCI."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
CODE = "KR0032"
QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q",
      "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q",
      "2026.1Q", "2026.2Q"]

kics = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
bs = json.loads((REPO / "IFRS17_BS.json").read_text(encoding="utf-8"))


def n(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


ki = {}
for r in kics:
    if r.get("원보험사코드") != CODE:
        continue
    try:
        it = int(r["항목번호"])
    except (TypeError, ValueError):
        continue
    if it in (7, 9):
        ki.setdefault(r["공시분기"], {})[it] = n(r.get("값"))

b = {}
for r in bs:
    if r.get("원보험사코드") != CODE:
        continue
    if r.get("항목명") in ("이익잉여금", "기타포괄손익 누계액"):
        b.setdefault(r.get("공시분기"), {})[r["항목명"]] = n(r.get("값"))

print("KR0032 NH농협손해보험 — 17BS(백만원/100=억원) vs K-ICS(억원), 정정 후")
print(f"{'분기':<9} {'17BS 이익잉여금':>15} {'K-ICS item7':>12} {'잔차%':>8}   "
      f"{'17BS AOCI':>12} {'K-ICS item9':>12} {'잔차%':>8}")
FLAG = {"2023.2Q", "2023.3Q", "2024.4Q"}
for q in QS:
    bb, kk = b.get(q, {}), ki.get(q, {})
    r7b, r7k = bb.get("이익잉여금"), kk.get(7)
    r9b, r9k = bb.get("기타포괄손익 누계액"), kk.get(9)

    def rel(x, y):
        if x is None or y is None:
            return None
        xe = x / 100.0
        d = max(abs(xe), abs(y))
        return None if d == 0 else abs(xe - y) / d * 100.0

    p7, p9 = rel(r7b, r7k), rel(r9b, r9k)
    mark = "  <== 정정 분기" if q in FLAG else ""
    print(f"{q:<9} {(r7b or 0)/100:>15,.1f} {r7k if r7k is not None else 0:>12,.0f} "
          f"{(f'{p7:.3f}' if p7 is not None else '-'):>8}   "
          f"{(r9b or 0)/100:>12,.1f} {r9k if r9k is not None else 0:>12,.0f} "
          f"{(f'{p9:.3f}' if p9 is not None else '-'):>8}{mark}")
