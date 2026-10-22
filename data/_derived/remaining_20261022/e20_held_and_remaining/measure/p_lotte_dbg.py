"""debug: 롯데 split layout in a later filing, current vs prior markers"""
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import lotte_lib as L
import prod as P
sys.stdout.reconfigure(encoding="utf-8")
fy = sys.argv[1]
tabs = P.tables_for("KR0003", fy)
_norm = L._norm
n = 0
for i, t in enumerate(tabs):
    if not t.rows:
        continue
    r0 = " ".join(_norm(c) for c in t.rows[0])
    r0c = r0.replace(" ", "")
    tag = ""
    if any(k in r0c for k in ("보험수익분석공시", "보험서비스비용분석공시", "재보험수익분석공시", "재보험비용분석공시", "재보험비용의보험서비스비용분석공시")):
        tag = "SUBHEAD"
    elif r0c.startswith(("당분기", "당반기")):
        tag = "CUR-MARK"
    elif r0c.startswith(("전분기", "전반기", "전기")):
        tag = "PRIOR-MARK"
    if tag:
        print(i, tag, getattr(t, "line_no", None), r0[:80])
for prior in (False, True):
    out, lines = L.split(tabs, prior)
    print("prior" if prior else "current", {k: out.get(k) for k in (4, 5, 6, 9, 10, 11, 13, 14, "_jang_rev", "_jang_cost", "_jang_rerev", "_jang_recost")}, "tables:", len(lines or []))
for prior in (False, True):
    out, lines = L.split2(tabs, prior)
    j = None
    if out.get("_jang_rev") is not None and out.get("_jang_cost") is not None:
        j = (out["_jang_rev"] - out["_jang_cost"]) + ((out.get("_jang_rerev") or 0) - (out.get("_jang_recost") or 0))
    print("SPLIT2", "prior" if prior else "current", "2(장기)=", j, {k: out.get(k) for k in (4, 5, 6, 9, 10, 11, 13, 14)}, "tables:", len(lines or []), lines)
