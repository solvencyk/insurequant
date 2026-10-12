# -*- coding: utf-8 -*-
"""e6: writes e6_screen_results_dbbffcb5.txt - the record of the browser audit of K-ICS.html (item 4).

The per-company table is generated from e2_expected_dbbffcb5.json (values derived from the pinned JSON + my own recompute, NOT from the page);
the browser run (e3_screen_audit.js / e4_tooltip_audit.js / e5_tooltip_width.js, page served from a clean `git archive 47f983ea` copy with ?iq_internal=1,
viewport emulated at 375 x 450) compared every one of these values with what the page showed.  The run's totals are written below as constants
because they come from the browser session (they cannot be recomputed by this script).
"""
import json
import sys

HERE = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

SUF = "_" + audit_io.resolved_rev()
E = json.load(open(HERE + "e2_expected" + SUF + ".json", encoding="utf-8"))
REQ = ["KR0068", "KR0001", "KR0011", "KR0050", "KR0097", "KR0073", "KR1000", "KR1102", "KR1010", "KR0087"]   # the ten named in the ticket
L = []
L.append("PIN data rev=%s (JSON files identical at HEAD 414c566f); page = K-ICS.html/theme.js of 47f983ea (designer 496d359e + 47f983ea)" % audit_io.resolved_rev())
L.append("browser run 2026-10-12, built-in browser, http://127.0.0.1:8893/K-ICS.html?iq_internal=1 (clean git archive copy), viewport emulated 375 x 450")
L.append("")
L.append("== run totals (browser session) ==")
L.append("47/47 companies selected through the page's own <select id=company> change handler; for each, e3 compared with the expected values below:")
L.append("  donut aria text and arc data (tier1, tier2) ............ 47/47 equal")
L.append("  empty-issuance flag ('발행 없음') ........................ 47/47 equal")
L.append("  number lines under the donuts ............................ 47/47 equal (strings)")
L.append("  tier1 ? popover tail (excluded tier2-type amount) ........ 47/47 equal")
L.append("  Forward Outlook: years, ratio, basic, note, tooltip tails  46/46 equal ; 서울보증보험 = placeholder with the exclusion reason as designed")
L.append("  issuance bars (years, hybrid/sub amounts) + two cells .... 47/47 equal")
L.append("  horizontal page overflow (scrollWidth > innerWidth) ...... 0/47")
L.append("  JSON value vs my independent recompute ................... 45/47 (미래에셋 24.5 vs 0.0 and DB생명 31.6 vs 0.0 are the two documented item-54 overrides)")
L.append("  issuance timeline JSON (what the bars and cells read) vs the bond ledger it is built from (e9): 126 ledger bonds with an issue date -> 125 timeline rows;")
L.append("    differences: 2 companies rounded to 2 decimals (하나생명, IBK연금) and 1 zero-face redeemed bond (동양생명 2020-09 신종) not listed - 0 value differences")
L.append("e4 tooltips (Chart.js tooltip object driven with setActiveElements so the page's callbacks produce the text; text read back):")
L.append("  donut tier1/tier2 '사용' and '잔여' lines, extra '미확정' line ... 47 x 2 charts, 0 text mismatches")
L.append("  Forward Outlook points (title, 지급여력비율, 기본자본비율, tails) .. 46 companies x 5 years, 0 text mismatches")
L.append("  a few companies were additionally hovered with the real mouse in the visible pane (including the 하나생명 tier1 donut: box 329 px); the texts equal the programmatic read")
L.append("e5 tooltip width (Chart.js getTooltipSize formula with the chart's own resolved options; calibrated: real hover on 하나생명 tier1 = 329 px, formula = 329):")
L.append("  canvas width at 375 px: donut 325 px, forward chart 307 px")
L.append("  boxes wider than their canvas (Chart.js limits the box x to [0, chartWidth - boxWidth] = 0, so the overhang is cut at the right edge):")
L.append("    donut tier1: DB손해보험 329, 아이엠라이프생명보험 329, 하나생명보험 329  (+4 px, the three '100%+' tier1 companies)")
L.append("    donut tier1: 푸본현대생명보험 341  (+16 px; the extra '기본자본형/보완자본형 미확정 신종 포함, 보완자본형이면 17.3%' line)")
L.append("    donut tier2: NH농협손해보험 349, 동양생명 349  (+24 px, the two '100%+' tier2 companies)")
L.append("  Forward Outlook tooltip: widest 153 px (메리츠화재 '지급여력비율: 230.45%') <= 307  -> no clipping")
L.append("labels vs definition_memo.md section 5 (exact string equality): subtitle line 1, subtitle line 2, captions '기본자본 자본증권' / '보완자본',")
L.append("  ? popover tier1, ? popover tier2, number-line pattern, tooltip notes ('초과분은 보완자본으로 재분류' / '초과분은 지급여력금액에서 불인정'),")
L.append("  교보라이프플래닛 tier2 tooltip '경과조치 표 미공시' ........................................ all equal")
L.append("  centre text ('100%+', '—', '데이터 없음') is canvas text, not readable from the DOM: the rule was read from the source and its inputs (pct, na) are covered above")
L.append("share (theme.js shRender, html2canvas) at 375 px with the pane visible: the exported image contained the donuts / the forward chart;")
L.append("  a blank image appeared only when the pane was not painting (Chart.js animation frames are throttled) - not a product defect")
L.append("")
L.append("== findings from the screen audit (routed by inbox ticket, not fixed here) ==")
L.append("S-1 Forward Outlook note prints a false improvement for companies whose capital is negative.  kics_forward_capital.json clamps ratio_pct / basic_ratio_pct to 0.0")
L.append("    when the interpolated capital is <= 0 (scripts/forward_capital_simulation.py v2 rule 'capacity_exhausted'), the page subtracts the TRUE baseline from the CLAMPED 2030 value:")
L.append("    예별손해보험  note: 'Baseline 지급여력 -41.8%, 기본자본 -41.8% | 2030 변화: 지급여력 +41.8%p, 기본자본 +41.8%p' ; the JSON's own capital/SCR gives -0.24%p and +4.77%p (true 2030 ratio -42.03%, basic -37.04%, not 0.0%)")
L.append("    롯데손해보험  note: 'Baseline 기본자본 -5.4% | 2030 변화: ... 기본자본 +5.4%p' ; own capital/SCR gives -1.57%p (true basic ratio -8.10% in 2026 ... -6.95% in 2030, not 0.0%)")
L.append("    the chart draws a flat 0 line for these series.  d2_forward_internal_consistency_dbbffcb5.txt has the per-year numbers (3 companies differ from their own capital/SCR: 예별, 롯데, and a 0.38%p rounding artefact at 마이브라운 whose SCR is 20.3억)")
L.append("S-2 the same note prints the negative baseline with an ASCII minus ('-41.8%', '-5.4%') - the owner rule is that every negative number on screen is shown with the triangle (△).")
L.append("S-3 tooltip boxes cut off at 375 px (Chart.js clamps the box to x=0, so the overhang is lost at the right edge; padding is 10 px):")
L.append("    donut tier1 DB손해보험 / 아이엠라이프 / 하나생명 329 vs canvas 325 -> only 4 px of the right padding is cut (text intact);")
L.append("    donut tier1 푸본현대 341 vs 325 -> text ends at 331: the last ~6 px (the trailing '%') are cut;")
L.append("    donut tier2 NH농협손해 / 동양 349 vs 325 -> text ends at 339: the last ~14 px (the closing '불인정)') are cut.")
L.append("S-4 the number line '경과조치 기발행 후순위 X억원' (tier2) is the issuer-printed item 54; for some issuers it contains post-2022 bonds, so the label overstates what is grandfathered")
L.append("    (메리츠화재 prints 15,631억 against 5,960억 issued before 2022 per the bond ledger -> tier2 0.2% shown vs 32.2% by issue vintage; 흥국생명 4,132억 vs 395억 -> 10.6% vs 37.0%).")
L.append("S-5 DB손해보험 issuance cell: '콜 상환 도래일 : 2030-09-01 (1,200억)' - the issuer's own filings disagree on which of 제1회/제2회 is called on 09-01 vs 09-25 (FY2025 annual report prints 09-01 for both, the H1 report prints 제1회 09-25 and 제2회 09-01); the amount in the cell depends on that choice. The forward chart is not affected (both calls fall in 2030).")
L.append("S-6 number line '기본자본 자본증권 X억원 / 인정한도 Y억원': for the 33 companies without a binding leg (tier1 0.0%, item 53 = 0 so no 기발행분) Y is 15% x SCR,")
L.append("    but the screen's own subtitle (and the definition memo) say 10% is the rule and 15% is only for 기발행분 - e.g. 한화생명 22,517억 (15%) vs 15,011억 (10%), 하나손해 702억 vs 468억.")
L.append("    The percentage is unaffected (numerator 0); only the printed denominator contradicts the definition. List: e8_tier1_limit_display_dbbffcb5.txt (33 of 47, binding_leg null).")
L.append("S-7 하나손해보험 issuance panel: the bond ledger row is still as_of 2025-12-31 (no H1 filing exists in data/dart/FY2026_Q2), K-ICS item 6 rose +999억 in 2026.2Q (2026-06-29 hybrid):")
L.append("    '총발행액 1,000억' and the reference line '신종 1,000억원' understate the real ~2,000억 (item 6 = 1,999). g5_stale_ledger_vs_item6_dbbffcb5.txt: 22 of 47 ledger rows are 2025-12-31;")
L.append("    하나손해 is the only one with an unexplained bond-size gap (아이엠라이프·삼성화재·한화손해·흥국생명 gaps are preferred / convertible-preferred shares, documented); 한화생명's H1 balance table (신종 3,081,900백만) equals the ledger.")
L.append("downloadable sheets (public_exports 기본자본소진율 / 보완자본소진율 / 자본비율전망) vs root JSON: 47 / 47 / 460 year-points, 0 mismatches (e7_public_sheets_vs_json_*.txt); the forward sheet's 비고 discloses the 0% cap, the screen does not (S-1).")
L.append("")
L.append("== expected (= displayed) values, the ten companies named in the ticket ==")


def line(code):
    e = E[code]
    f = e["fwd"]
    fw = "forward: %s" % (("ratio " + "/".join(str(v) for v in f["ratio"]) + " | basic " + "/".join(str(v) for v in f["basic"])) if f and f.get("status") == "ok" else (f or {}).get("status"))
    cap = e["cap"]
    cells = "-" if not cap else "hybrid %s | sub %s" % (cap.get("hybrid_cell"), cap.get("sub_cell"))
    return "%s %s | tier1 %s | tier2 %s | %s | issuance cells %s" % (code, e["name"], e["t1"]["aria"], e["t2"]["aria"], fw, cells)


for c in REQ:
    L.append(line(c))
    L.append("    number lines: " + E[c]["note"])
L.append("")
L.append("== all 47 companies (compact) ==")
for c in E:
    e = E[c]
    f = e["fwd"]
    fw = ("ratio " + "/".join(str(v) for v in f["ratio"]) + " | basic " + "/".join(str(v) for v in f["basic"])) if f and f.get("status") == "ok" else str((f or {}).get("status"))
    L.append("%s %s | T1 %s | T2 %s | %s" % (c, e["name"], e["t1"]["pct"], e["t2"]["pct"] if not e["t2"]["na"] else "n/a", fw))
open(HERE + "e6_screen_results" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L[:60]))
