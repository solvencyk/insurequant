# -*- coding: utf-8 -*-
"""h9: writes h9_screen_results_<rev>.txt - the record of the re-measure of K-ICS.html (ticket 20261012T2040Z re-run, 2026-10-13).

The per-company strings below are generated from h4_expected_<rev>.json (my independent expectation); the browser run compared the page with every one of them.
The totals are constants taken from the browser session (they cannot be recomputed by this script).
"""
import json
import sys

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

REV = audit_io.resolved_rev()
E = json.load(open(HERE + "h4_expected_%s.json" % REV, encoding="utf-8"))
L = []
L.append("PIN data+page rev=%s (K-ICS.html / theme.js of designer 75234ddf + 258d3c30; JSON and ledger of publishing 48c7c3ac/c05170a7/10b45d71/392efee2)" % REV)
L.append("browser run 2026-10-13, built-in browser, http://127.0.0.1:8893/K-ICS.html?iq_internal=1 served from a clean `git archive` copy of the root web files at this revision")
L.append("viewports emulated: 1280 x 800 and 375 x 812 (device pixel ratio 2)")
L.append("")
L.append("== run totals ==")
L.append("h5 AUD (page's own <select id=company>, DOM + Chart.js objects): 47/47 companies, 0 mismatches at 1280 AND at 375; horizontal page overflow 0/47 at 375")
L.append("   donut aria/arcs, number lines (tier1 limit now 10%% x SCR without a legacy leg, tier2 deducted amount = my ledger recompute), ? popover tails, forward years / ratio / basic")
L.append("   (clipped years are null points), hidden 3rd series flags, forward note + clip notice + no ASCII minus, axis ticks without ASCII minus, legend without the hidden series,")
L.append("   issuance bars (incl. 추정 flag footer), the two cells (date-only call for DB손해 신종, 하나손해 total 1,999억, rate '—' for the estimated latest row)")
L.append("h6 TT (tooltip objects driven with the elements a real hover picks; text read back): 47 companies x (2 donuts x use/rest + 5 forward years + issuance bars), 0 mismatches at 1280 and at 375")
L.append("   donut 100%+ = two lines ['사용: 100%+ (실제 X%)', over-note]; forward clipped year = only the hidden series -> '지급여력비율: 자본잠식' / '기본자본비율: 자본잠식';")
L.append("   bar tooltip footer '추정(원장 미갱신)' appears for exactly one company-year: 하나손해 2026")
L.append("h7 tooltip widths (Chart.js getTooltipSize formula, resolved options): NO tooltip box wider than its canvas at either width")
L.append("   1280: widest donut tier1 223 px (푸본), tier2 196 (NH농협손해), forward 153, bars 153  vs canvas 360 / 360 / 939 / 947")
L.append("    375: widest donut tier1 223 px (푸본), tier2 196 (NH농협손해), forward 153, bars 153  vs canvas 325 / 325 / 307 / 311   (previous pin: 329 / 341 / 349 vs 325 = clipped)")
L.append("real mouse hover at 375 (pane painting, screenshots read): 동양 tier2 100%+ -> two lines fully inside the donut canvas; 하나생명 tier1 238.2% -> two lines fully inside;")
L.append("   예별 forward 2027 -> '2027 / 지급여력비율: 자본잠식 / 기본자본비율: 자본잠식', empty plot, note below; 하나손해 2026 bar -> '2026년 발행 / 신종자본증권: 999억 / 후순위채: 0억 / 추정(원장 미갱신)'")
L.append("h8 share images (theme.js shRender -> html2canvas, per section, 375 px): 15 companies (한화생명·메리츠·DB손해·하나손해·하나생명·교보·코리안리·스위스리·교보라이프플래닛·동양·예별·롯데·푸본·아이엠라이프·농협손해)")
L.append("   x sections 소진율 / 자본비율 전망 / 발행현황 (where applicable): ring colours, forward lines (or chart frame for clipped companies), bars present, header names the company -> 0 mismatches")
L.append("   harness note: the embedded pane produces no animation frames while idle (requestAnimationFrame ticks = 0 in 1.5 s), so a freshly created Chart.js chart is copied blank;")
L.append("   with Chart.defaults.animation = false (harness only) every share image contains its charts.  Not a product defect.")
L.append("labels vs definition_memo.md section 5 (exact string equality): subtitle lines, captions, ? popover tier1/tier2 -> equal")
L.append("downloadable sheets: 기본자본소진율 / 보완자본소진율 / 자본비율전망 vs root JSON 47 / 47 / 460 points, 0 mismatches; vs MY recompute 329 cells (tier2 numerator, deducted hybrid / subordinated,")
L.append("   pre-2023 stock rows, tier1 15% and 10% limits) 0 mismatches (e7); 자본성증권발행현황 124 rows vs ledger: 0 field differences (e10)")
L.append("")
L.append("== forward notes of the two companies that printed a fake improvement before (read from the page at 375 and 1280, equal to the expectation) ==")
for c in ("KR0004", "KR0003"):
    f = E[c]["fwd"]
    L.append("%s %s: %s%s" % (c, E[c]["name"], f["note"], (" / " + f["clip_note"]) if f["clip_note"] else ""))
L.append("   series: 예별 ratio and basic = null for 2026..2030 (nothing drawn); 롯데 ratio drawn, basic null for 2026..2030; axis ticks and note use the triangle for negatives")
L.append("")
L.append("== expected (= displayed) values, the companies named in the ticket ==")
for c in ("KR0068", "KR0001", "KR0011", "KR0050", "KR0097", "KR0073", "KR1000", "KR1102", "KR1010", "KR0087"):
    e = E[c]
    f = e["fwd"]
    fw = ("ratio " + "/".join("-" if v is None else str(v) for v in f["ratio"]) + " | basic " + "/".join("-" if v is None else str(v) for v in f["basic"])) if f and f.get("status") == "ok" else str((f or {}).get("status"))
    cap = e["cap"]
    cells = "-" if not cap else "hybrid %s | sub %s" % (cap.get("hybrid_cell"), cap.get("sub_cell"))
    L.append("%s %s | tier1 %s | tier2 %s | %s | cells %s" % (c, e["name"], e["t1"]["aria"], e["t2"]["aria"], fw, cells))
    L.append("    number lines: " + e["note"])
open(HERE + "h9_screen_results_%s.txt" % REV, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L[:30]))
