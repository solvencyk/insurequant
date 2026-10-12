# -*- coding: utf-8 -*-
"""Write chubb_d2_evidence.md from chubb_d2_evidence.json + chubb_summary22.json + chubb_identity.json."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
D = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ifrs17_owner_followups_20261012/"
ev = json.loads(open(D + "chubb_d2_evidence.json", "rb").read().decode("utf-8"))["quarters"]
s22 = json.loads(open(D + "chubb_summary22.json", "rb").read().decode("utf-8"))
ident = json.loads(open(D + "chubb_identity.json", "rb").read().decode("utf-8"))
L = ["# 처브라이프 KR0100 항목 20 정의 통일(D2 = 일반계정 보험계약부채 + 특별계정부채) — 증빙 (2026-10-12, 티켓 항목 4 ⑦)", ""]
L += ["재현: `scripts/extract_chubb_d2_20261012.py`(원문 PDF 재독 + 스펙) → `scripts/apply_ifrs17_bs_fix_20261012.py --spec data/_derived/ifrs17_owner_followups_20261012/chubb_d2_spec_bs.json --round chubb_d2 [--apply]`(BS 6칸 + 오버레이·사이드카·파트) · "
      "`scripts/apply_chubb_ilp_d2_20261012.py [--apply|--revert]`(ILP 항목 14·15 9셀 + provenance).", ""]
L += ["## 1. 무엇이 틀렸나", "",
      "- 경영공시 재무상태표(업무보고서 서식, FY2025_Q3 까지)는 일반계정 `1. 보험계약부채`(D1)와 `IV. 특별계정부채`(SA, 변액)를 따로 인쇄한다. 연말 DART·감사보고서 셀(2023.4Q·2024.4Q·2025.4Q)과 2026 K-IFRS 서식 "
      "(`Ⅰ. 보험계약부채` 1,275,313,916,144원 = 2026.1Q p26)의 「보험계약부채」는 변액 보험계약부채를 포함한다. 그런데 중간분기 BS 6칸(2023.1Q·2024.1Q·2024.3Q·2025.1Q·2025.2Q·2025.3Q)과 ILP 9셀(2023.1Q~2025.3Q)은 D1 만 담아 "
      "연말마다 계단이 생기고(2025.1Q: 연말 13,004억 → 10,717억 → 2025.4Q 13,358억) 2-4 합계(항목 8)가 변액 2,400~2,700억을 포함해 항목 20 이 항목 8 보다 작아졌다(포트폴리오 검증기 R3 RED 5).",
      "- 메트라이프 KR0095 항목 20 은 이미 같은 정의(일반계정 보험계약부채 + 특별계정부채)로 적재돼 있다(BS 레인 2026-10-11).", ""]
L += ["## 2. 원문 재독 (9분기, PDF 텍스트층 + 쪽 렌더링)", "",
      "| 분기 | PDF(쪽) | D1 일반계정 보험계약부채(원) | SA 특별계정부채(원) | D2 = D1+SA(원) | 가.잔여보장 + 나.발생사고 − D1 | 2-2 요약표(억원) 책임준비금 / 특별계정부채 | 8-1 환산(억원) D1+재보험계약부채 / SA | 부채총계 항등식 |",
      "|---|---|---|---|---|---|---|---|---|"]
for q, e in ev.items():
    s = s22[q]
    iden = ident[q]
    hit = iden["hits"][0] if iden["hits"] else None
    ident_s = (f"잔차 {iden['resid']:,} = 기타부채·계약자지분조정 인쇄 토큰 {hit[0]:,} + {hit[1]:,}" if hit else f"잔차 {iden['resid']:,} (토큰 쌍 미검출; 2-2 요약표로 확인)")
    L.append(f"| {q} | `{e['pdf'].split('/')[2]}` D1 p{e['D1_pages'][0]} · SA p{e['SA_pages'][0]} | {e['D1_won']:,} | {e['SA_won']:,} | {e['D2_won']:,} | {e['lrc_plus_lic_minus_d1_won']} 원 | "
             f"{s['summary']['책임준비금'][0]:,} / {s['summary']['특별계정부채'][0]:,} | {s['d1_plus_re_eok']:,.2f} / {s['sa_eok']:,.2f} | {ident_s} |")
L += ["", "- 라벨 확인: 2024.1Q·2024.2Q·2024.3Q·2025.1Q~3Q 는 토큰이 인쇄된 줄의 라벨이 `1. 보험계약부채`/`IV. 특별계정부채` 로 읽힌다(2023.1Q·2023.2Q·2023.3Q 는 한 쪽에 표가 겹쳐 있어 라벨 줄을 못 읽었고, 2-2 요약표 책임준비금·특별계정부채 억원값이 8-1 값과 반올림 안에서 같다).",
      "- 특별계정은 LIC 를 안 담는다: 일반계정 발생사고요소가 연말 DART LIC 와 같다 — 2023.12.31 222.82 대 DART 2023.4Q 222.83, 2024.12.31 250.05(2025.1Q PDF p32 전기 열 `나. 발생사고요소` 25,004,812,029원) 대 DART 2024.4Q 250.05.",
      "- D2 대 연말 K-IFRS 라인: 2023.4Q −0.110 %(1,223,837.9 대 1,222,488.1백만원), 2024.4Q −0.074 %(1,301,389.1 대 1,300,424.0).", ""]
L += ["## 3. 바꾼 칸 (전 → 후)", "", "### IFRS17_BS.json 항목 20 (백만원, 6칸; 오버레이·사이드카·파트 파일 같이)", "",
      "| 분기 | 전(일반계정) | 후(D2) | 파트 파일 |", "|---|---|---|---|"]
for q, e in ev.items():
    if e["bs_item20_old"] is not None:
        L.append(f"| {q} | {e['bs_item20_old']:,.6f} | {e['bs_item20_new']:,.6f} | {'KR0100_agent_gran.json' if q == '2023.1Q' else 'KR0100_agent_followup.json(기타 에이전트 등급, 엔진 파트 KR0100.json 보다 우선)'} |")
L += ["", "### insurance_liability_portfolio.json 항목 14·15 (억원, 9셀; 항목 10~13 불변)", "",
      "| 분기 | 14 전 → 후 | 15 전 → 후 | 10(LIC) | R-LIC3: 10 + 14 − 15 |", "|---|---|---|---|---|"]
for q, e in ev.items():
    o, n = e["ilp_old"], e["ilp_new"]
    L.append(f"| {q} | {o['i14']:,.2f} → {n['i14']:,.2f} | {o['i15']:,.2f} → {n['i15']:,.2f} | {o['i10']:,.2f} | {round(o['i10'] + n['i14'] - n['i15'], 2):+.2f} |")
L += ["", "빈 BS 3분기(2023.2Q·2023.3Q·2024.2Q: 마스터에 항목 20 이 없다)는 채우지 않았다 — D2 값은 위 표에 있다(2023.2Q 1,156,141.39455 · 2023.3Q 1,122,961.83869 · 2024.2Q 1,274,461.117934백만원).", ""]
open(D + "chubb_d2_evidence.md", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("written", len(L))
