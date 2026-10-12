# -*- coding: utf-8 -*-
"""Write amort_split_evidence.md (cell list before/after + sum-identity table) from amort_split_evidence.json / amort_split_manifest.json."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
D = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ifrs17_owner_followups_20261012/"
ev = json.loads(open(D + "amort_split_evidence.json", "rb").read().decode("utf-8"))
man = json.loads(open(D + "amort_split_manifest.json", "rb").read().decode("utf-8"))
L = []
L.append("# CSM 상각 스케줄 분할표 5사 + 한화생명 연결/별도 표 선택 — 증빙 (2026-10-12, parser-ifrs17, 티켓 20261012T1020Z 항목 6)")
L.append("")
L.append("재현: `scripts/extract_amort_split_tables_20261012.py`(원문 XML 읽기·항등식·스펙 생성) → `scripts/load_amort_split_tables_20261012.py [--apply|--revert]`(셀 단위 적재). 마스터 `CSM_amortization.json` 2025.4Q 만, 패널·xlsx 는 안 건드렸다.")
L.append("")
L.append("## 1. 바꾼 칸 전수 (전 → 후, 억원, 소수 1자리 = `build_tidy_exports.num`)")
L.append("")
L.append("| 회사 | 경과차년 | 전 | 후 | 정확값(억원) | 원천 |")
L.append("|---|---|---|---|---|---|")
for comp in man["companies"]:
    for c in comp["cells"]:
        L.append(f"| {comp['name']} ({comp['code']}) | y{c['경과차년']} | {'(빈 칸)' if c['old'] is None else c['old']} | {c['new']} | {c['exact_eok']} | {comp['source']} |")
L.append("")
L.append(f"합계 {man['cells_changed']}칸 = 분할표 4사 y9·y10 8칸(빈 칸 → 값) + 한화생명 y1~y10 10칸(연결 → 별도). 라이나 2025.4Q 는 이미 PDF 로 y1~y10 이 채워져 있고 DART 뒷 표와 5자리까지 일치해서 **바꾸지 않았다**.")
L.append("")
L.append("## 2. 합계 항등식 확인표 (원문 표 직접 읽기, 단위는 회사별 표 단위)")
L.append("")
L.append("당기 표(문서에서 먼저 나오는 쌍) 합계 = 마스터 2025.4Q 기말 CSM(항목 6), 전기 표 합계 = 마스터 2024.4Q 기말 CSM. 행 단위로는 `y1~y8 + (9년, 10년, 11~15, 16~20, 21~25, 26~30, 30+) = 계` 가 모든 포트폴리오 행에서 닫힌다(허용 3 단위).")
L.append("")
L.append("| 회사 | 원천(별도) | 단위 | 당기 합계(억원) | 마스터 기말 CSM 2025.4Q | 상대차 | 전기 합계(억원) | 마스터 2024.4Q | 행 항등식 최악 잔차 | 별도=연결 | y1~y8 합 | y9+y10 | y11+ |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for e in ev:
    if e["code"] == "KR0068":
        continue
    cur = e["current"]["rows"]
    tot = next(r for r in cur if r["label"] == "합계")
    div = 100.0 if e["unit"] == "백만원" else 1e5
    y18 = sum(tot["y1_y8"]) / div
    y910 = sum(tot["back"][:2]) / div
    cons = e.get("consolidated") or {}
    cons_s = "연결 파일 없음" if not e["con_xml"] else ("같음(전 행)" if cons.get("all_rows_equal") else "다름")
    prior = e.get("identity_prior_total_eok")
    L.append(f"| {e['name']} ({e['code']}) | `{e['sep_xml'].split('/')[-1]}` 쌍 {e['current']['front_line']}·{e['current']['back_line']}행 | {e['unit']} | {e['identity_current_total_eok']:,.2f} | {e['master_closing_csm_2025.4Q']:,.1f} | {e['rel_diff_current_total_vs_closing']:+.6f} | "
             f"{'' if prior is None else format(prior, ',.2f')} | {'' if e.get('master_closing_csm_2024.4Q') is None else format(e['master_closing_csm_2024.4Q'], ',.1f')} | {e['row_identity_worst_abs_gap_in_unit']} {e['unit']} | {cons_s} | {y18:,.2f} | {y910:,.2f} | {e['y11plus_eok']:,.2f} |")
h = next(e for e in ev if e["code"] == "KR0068")
L.append("")
L.append("한화생명(KR0068): 별도 표 한 장(분할 아님) — "
         f"`{h['sep_xml'].split('/')[-1]}` {h['current_separate_line']}행, 합계 {h['current_separate_total_eok']:,.2f}억원 = 마스터 기말 CSM {h['master_closing_csm_2025.4Q']:,.1f}(상대차 {h['rel_diff_separate_total_vs_closing']:+.2e}), "
         f"y1~30+ 합 = 계(잔차 {h['parts_sum_gap_in_unit']} 백만원). 옛 마스터 값 = 연결 표 `{h['con_xml'].split('/')[-1]}` {h['consolidated_current_line']}행(합계 {h["consolidated_current_total_eok"]:,.2f}억원, 별도보다 +1.85 %). "
         f"y11+ = {h['y11plus_eok']:,.2f}억원(마스터는 y1~y10 만 담는다).")
L.append("")
L.append("## 3. 안 한 것 / 알려둘 것")
L.append("")
L.append("- 패널 `data/dart/viz/csm_amort_schedule.json`·`viz_build_ifrs17_panels.py::extract_amort_schedule`(앞 반쪽만 읽는다)·xlsx `CSM상각` 시트는 티켓 규칙대로 안 건드렸다. 패널 `buckets.total`(분할표 4사 + 라이나)은 계속 부분합이고 한화생명 패널은 연결 표다. `build_tidy_exports.py --only amort` 로 마스터를 패널에서 다시 만들면 이 18칸이 되돌아가므로 그 뒤 `scripts/load_amort_split_tables_20261012.py --apply` 를 다시 돌린다.")
L.append("- 라이나 패널 행을 마스터값으로 바꿀지는 이번 범위 밖(보고만).")
L.append("- 마스터에는 y1~y10 만 있다. y11 이후(AIA 8,629.93 · 처브 622.77 · 메트라이프 11,890.64 · BNP 55.07 · 라이나 10,184.13 · 한화생명 56,918.93억원)는 `amort_split_evidence.json` 의 `y11plus_eok` 에 있다.")
open(D + "amort_split_evidence.md", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("written", len(L), "lines")
