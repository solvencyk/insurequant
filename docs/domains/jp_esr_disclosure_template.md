# 일본 ESR 규제 공시 양식 지도 (jp 레인 정본, 2026-09-12 신설)

> 근거 티켓: `inbox/jp/20260912T0905Z__owner__JP_MULTI__esr_disclosure_template_map.md`. 기계 스키마: `J-ESR/esr_disclosure_schema.json`.
> 표본값+검산: `J-ESR/raw/fy2025_samples/extracted_sample_values.json`. 생성기(10월 62사 추출의 프로토타입):
> `J-ESR/extract_esr_template_samples.py` (`C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/extract_esr_template_samples.py`, exit 0 = 검산 전부 통과 + census 헤드라인 일치).
> **10월 말 재census 의 확장 열 이름은 이 문서의 항목 id 를 그대로 쓴다.**

## 0. 한 줄 요약

- 규제 양식(保険業法施行規則 59条の2, 令和7年金融庁告示第74号·第75号)은 **회사가 달라도 표 골격이 같다.** 정량 7절(요약 → 적격자본 구성 → 소요자본 구성 → 경제가치 BS → 외국증권 → 보험부채 상품별 → 민감도) + 정성 2절(전제·수법 / 검증체제). 손보 표본 2사에서 라벨은 전각/반각·기호 `(A)` vs `（A）`·`Tier1` vs `Tier１` 차이뿐, NFKC 정규화 후 **동일**.
- 헤드라인 `esr_pct` 는 `適格資本の額(A) / 所要資本の額(B)`. 두 표본 모두 census 값과 일치(au 791.7 / Meiji Yasuda Non-Life 743.2). 금액은 百万円 절사라 비율 검산은 **구간 검산**이어야 한다(§4 C01).
- 스키마는 두 층: `layer:"esr"` 109항목(표 T1~T8) / `layer:"article_axes"` 22항목(금융청 모니터링 보고서 3축 + ESR 빈 자리 골격). 검산 C01~C34 + A01~A05 전부 통과(au 34/34, Meiji Yasuda Non-Life 41/41, NN Life 4/4).

## 1. 표본

| key | 회사 | 문서 | 페이지 | 층 | 비고 |
|---|---|---|---|---|---|
| `au_nonlife` | au損害保険 (au Non-Life) | `J-ESR/raw/fy2025_samples/au_nonlife_disclo_260730_4of5.pdf` (ディスクロージャー誌 業績データ편, 2026-07-30) | 31p | esr + article_axes | ESR 절 p21~30. 5개년 표 p2 헤드라인 791.7%. 민감도 값 **생략**(전 시나리오 차이 1%p 미만 주기). 본편에 責任準備金の内訳(p8)·出再 표(p6) 포함 |
| `meijiyasuda_nonlife` | 明治安田損害保険 (Meiji Yasuda Non-Life) | `J-ESR/raw/fy2025_samples/meijiyasuda_nonlife_20260904_performance_data.pdf` (【別冊】業績データ, 2026-09-04) | 14p | esr + article_axes | 별책 전체가 ESR 규제 양식(p1 목차 = 告示 절 번호 그대로). 이상위험준비금·재보험 표는 **본편에 있어 별책엔 없음** |
| `nnlife` | エヌエヌ生命保険 (NN Life) | `J-ESR/raw/fy2025_samples/nnlife_2025disclosure_202607.pdf` (ディスクロージャー誌 2026-07-29) | 95p | article_axes 만 | ESR `後日公表予定`(3곳). 基礎利益 p60, 逆ざや p15, 出再 표 p64. ESR 표 골격은 **없고 문장만** (§7-3) |

세 PDF 모두 텍스트 PDF(fitz 추출 정상, 스캔 없음). 페이지 번호는 PDF 인덱스(1부터)이며 인쇄 페이지 번호와 다르다(au 인쇄 69~79 = PDF 21~31).

## 2. 규제 양식 구조 (告示 절 번호 = Meiji Yasuda 별책 목차)

| 절 | 일본어 제목 | 표 id | 내용 | au 위치 | MY 위치 |
|---|---|---|---|---|---|
| 정량 1 | ソルベンシー・マージン比率並びに適格資本の額及び所要資本の額 | T1 (要約) | (A) 적격자본·(B) 소요자본·(A)/(B) 비율, 열 = 前年度(－)/当年度/増減 | p22 (2) | p2 |
| (au 만) | 保険会社に係る保険金等の支払能力の充実の状況（単体SMR） | T1_combined | Tier1/2 요약 + 리스크 (a)~(k) 한 표. `非保険事業に係る所要資本の額 (i)` 행이 여기만 있음 | p22 (1) | 없음 |
| 정량 2 | 適格資本の額の構成に関する事項 | T2 | Tier1 (A)=(B)−(C), Tier2 (D)=(E)−(F)−(G), 합계 (A)+(D). 33행 | p23 (3) | p3 |
| 정량 3 | 所要資本の額の構成に関する事項 | T3 | 리스크 (A)~(G), 분산효과 (H), 세효과전 (I/J), 세효과 (J/K), 세효과후. 31행 | p24 (4) | p4 |
| 정량 4 | 経済価値ベースのバランスシートに関する事項 | T4 | 4열(財務会計/組替え/評価替え/経済価値) BS + 주기(작성방침·할인율·MOCE) | p25~27 (5) | p5~9 |
| 정량 5 | 外国証券の種類別差異調整に関する事項 | T5 | 외국증권 look-through (미추출) | p27 (6) | p10 |
| 정량 6 | 保険負債の商品別差異調整に関する事項 | T6 | 6열(財務会計/再保険グロスアップ/非経済前提/経済前提/その他/経済価値 MOCE除く) × 상품 | p28 (7) | p11 |
| 정량 7 | 感応度分析に関する事項 | T7 | 8열(基準 + 7 시나리오) × 10행. MY 는 差額表 추가 | p29 (8) 값 생략 | p12 |
| (au 만) | 適格資本の額及び所要資本の額の変動要因分析 | — | 초년도라 該当なし | p29 (9) | 없음 |
| 정성 1 | 計算に用いられた前提及び手法 | T8 | 할인율 버킷·비경제전제·경영조치·리스크경감·USP·내부모형·내부할인율·중요변경 | p29 (10) 문장 | p13 항목식 |
| 정성 2 | 算出及び検証に係る手続並びに体制 | — | 검증책임자 체제(미추출) | p30 (11) | p14 |

**민감도 시나리오 8열(고정 순서):** 当期末 / 円金利 50bp 上昇 / 円金利 50bp 下降 / 米ドル金利 50bp 上昇 / 米ドル金利 50bp 下降 / 円金利 UFR 50bp 下降 / 株式・不動産 10% 下落 / 為替 10% 円高.
**민감도 행 10개:** SMR / 適格資本 / 総資産 / 保険負債(MOCE除く) / MOCE / 非保険負債 / 純資産 / 所要資本 / 生命保険リスク(au 는 행 없음) / 市場リスク.

## 3. 항목 표 (스키마 = 이 표, 두 층 131항목)

열 설명: `kics` = K-ICS 마스터 항목번호(§6, 근사 포함, 빈칸 = 대응 없음). 회사 열 = 실측값(百万円; pct 는 %; `－` = 원문 대시 = null). `page` = au/MY PDF 페이지. `formula` = 검산·정의.

| id | layer | table | label (ja) | meaning (ko) | unit | parent | kics | au_nonlife | meijiyasuda_nonlife | nnlife | page | formula |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `eligible_capital` | esr | T1 | 適格資本の額(A) | 적격자본 총액(A) | JPY_million |  | 1 | 9,278 | 40,290 | n/a(not_yet) | 22/2 | = tier1_eligible + tier2_eligible |
| `required_capital` | esr | T1 | 所要資本の額(B) | 소요자본 총액(B, 세효과 고려후) | JPY_million |  | 14 | 1,171 | 5,420 | n/a(not_yet) | 22/2 | = rc_post_tax |
| `esr_pct` | esr | T1 | ソルベンシー・マージン比率((A)/(B)) | ESR(경제가치기준 지급여력비율, 신기준 SMR) | pct |  | 27 | 791.7 | 743.2 | n/a(not_yet) | 22/2 | = eligible_capital / required_capital * 100 (truncation interval) |
| `tier1_eligible` | esr | T2 | Tier1適格資本の額 | Tier1 적격자본(A) | JPY_million | eligible_capital | 2 | 9,102 | 40,140 | n/a(not_yet) | 23/3 | = tier1_basic - tier1_adjustments |
| `tier1_basic` | esr | T2 | Tier1適格資本に係る基礎項目の額 | Tier1 기초항목(B) = EBS 순자산 | JPY_million | tier1_eligible | 4 | 13,880 | 42,118 | n/a(not_yet) | 23/3 | = tier1_instr_unrestricted + tier1_instr_restricted + tier1_non_instrument; == ebs_net_assets |
| `tier1_instr_unrestricted` | esr | T2 | 算入制限のないTier1資本調達手段の額 | 산입제한 없는 Tier1 자본조달수단(자본금·기금) | JPY_million | tier1_basic | 5 | 3,150 | 10,000 | n/a(not_yet) | 23/3 |  |
| `tier1_instr_restricted` | esr | T2 | 算入制限のあるTier1資本調達手段の額 | 산입제한 있는 Tier1 자본조달수단(신종자본증권 등) | JPY_million | tier1_basic | 6 | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_non_instrument` | esr | T2 | 資本調達手段以外のTier1適格資本の額 | 자본조달수단 이외 Tier1 적격자본 | JPY_million | tier1_basic |  | 10,730 | 32,118 | n/a(not_yet) | 23/3 | = tier1_ni_retained_earnings + tier1_ni_capital_surplus + tier1_ni_aoci + tier1_ni_other_contrib + tier1_ni_ev_adjustment |
| `tier1_ni_retained_earnings` | esr | T2 | 剰余金等の額又は利益剰余金等の額 | 잉여금등(이익잉여금+규제상 준비금) | JPY_million | tier1_non_instrument | 7 | 5,998 | 18,237 | n/a(not_yet) | 23/3 | = ebs_retained_earnings + ebs_regulatory_reserve_equity |
| `tier1_ni_capital_surplus` | esr | T2 | 資本剰余金(Tier2適格資本に算入されるものを除く)の額 | 자본잉여금(Tier2 산입분 제외) | JPY_million | tier1_non_instrument |  | 2,850 | 8,455 | n/a(not_yet) | 23/3 | == ebs_capital_surplus |
| `tier1_ni_aoci` | esr | T2 | その他の包括利益累計額又は評価・換算差額等の額 | 기타포괄손익누계액(평가·환산차액) | JPY_million | tier1_non_instrument | 9 | － | 2,064 | n/a(not_yet) | 23/3 | == ebs_aoci |
| `tier1_ni_other_contrib` | esr | T2 | その他の拠出金等の額 | 기타 출자금등 | JPY_million | tier1_non_instrument |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_ni_ev_adjustment` | esr | T2 | 経済価値ベースの調整額 | 경제가치기준 조정액(EBS 순자산 − 회계 순자산 − 규제상 준비금) | JPY_million | tier1_non_instrument | 11 | 1,882 | 3,362 | n/a(not_yet) | 23/3 | == ebs_ev_adjustment |
| `tier1_adjustments` | esr | T2 | Tier1適格資本に係る調整項目の額 | Tier1 조정항목(C, 공제) | JPY_million | tier1_eligible | 12 | 4,778 | 1,978 | n/a(not_yet) | 23/3 | = Σ tier1_adj_* (7 subs) |
| `tier1_adj_intangibles` | esr | T2 | 無形固定資産(繰延税金負債相殺後)の額 | 무형고정자산(DTL 상계후) | JPY_million | tier1_adjustments |  | 4,778 | 1,978 | n/a(not_yet) | 23/3 | == ebs_intangibles |
| `tier1_adj_dta` | esr | T2 | 繰延税金資産の額 | 이연법인세자산 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_adj_pension_asset` | esr | T2 | 前払年金費用又は退職給付に係る資産 | 선급연금비용/퇴직급여 관련 자산 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_adj_holdings_other_fi` | esr | T2 | 他の金融機関等が意図的に保有しているTier1資本調達手段の額 | 타 금융기관 의도적 보유 Tier1 조달수단 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_adj_own_instruments` | esr | T2 | 自己のTier1資本調達手段への投資の額 | 자기 Tier1 조달수단 투자 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_adj_ineligible_reinsurance` | esr | T2 | 不適格再保険資産の額 | 부적격 재보험자산 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_adj_encumbered_excess` | esr | T2 | 処分制約のある資産のうち関連する負債と所要資本を上回る額 | 처분제약 자산 중 관련부채+소요자본 초과분 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_eligible` | esr | T2 | Tier2適格資本の額 | Tier2 적격자본(D) | JPY_million | eligible_capital | 3 | 175 | 149 | n/a(not_yet) | 23/3 | = tier2_basic - tier2_adjustments - tier2_cap_deduction |
| `tier2_basic` | esr | T2 | Tier2適格資本に係る基礎項目の額 | Tier2 기초항목(E) | JPY_million | tier2_eligible |  | 175 | 149 | n/a(not_yet) | 23/3 | = tier2_instruments + tier2_non_instrument |
| `tier2_instruments` | esr | T2 | Tier2資本調達手段の額 | Tier2 자본조달수단(후순위채 등) | JPY_million | tier2_basic |  | － | － | n/a(not_yet) | 23/3 | = tier2_instr_t1_excess + tier2_instr_paid + tier2_instr_unpaid |
| `tier2_instr_t1_excess` | esr | T2 | 算入制限のあるTier1資本調達手段の制限を超過した額 | 제한초과 Tier1 조달수단(Tier2 재분류) | JPY_million | tier2_instruments | 13 | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_instr_paid` | esr | T2 | 払込済みTier2資本調達手段の額 | 납입완료 Tier2 조달수단 | JPY_million | tier2_instruments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_instr_unpaid` | esr | T2 | 払込未済のTier2資本調達手段の額 | 미납입 Tier2 조달수단(약정자본) | JPY_million | tier2_instruments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_non_instrument` | esr | T2 | 資本調達手段以外のTier2適格資本の額 | 자본조달수단 이외 Tier2 적격자본 | JPY_million | tier2_basic |  | 175 | 149 | n/a(not_yet) | 23/3 | = tier2_ni_surplus_from_instr + tier2_ni_encumbered_t1_deducted + tier2_ni_basket |
| `tier2_ni_surplus_from_instr` | esr | T2 | Tier2資本調達手段の額に含まれる資本調達手段を | Tier2 조달수단 발행 자본잉여금 | JPY_million | tier2_non_instrument |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_ni_encumbered_t1_deducted` | esr | T2 | 処分制約のある資産のうちTier1適格資本から控除される額 | 처분제약 자산 중 Tier1 공제분 | JPY_million | tier2_non_instrument |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_ni_basket` | esr | T2 | Tier2バスケット(上限適用後)の額 | Tier2 바스켓(상한 적용후) | JPY_million | tier2_non_instrument |  | 175 | 149 | n/a(not_yet) | 23/3 |  |
| `tier2_adjustments` | esr | T2 | Tier2適格資本に係る調整項目の額 | Tier2 조정항목(F) | JPY_million | tier2_eligible |  | － | － | n/a(not_yet) | 23/3 | = tier2_adj_holdings_other_fi + tier2_adj_own_instruments |
| `tier2_adj_holdings_other_fi` | esr | T2 | 他の金融機関等が意図的に保有しているTier2資本調達手段の額 | 타 금융기관 의도적 보유 Tier2 조달수단 | JPY_million | tier2_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_adj_own_instruments` | esr | T2 | 自己のTier2資本調達手段への投資の額 | 자기 Tier2 조달수단 투자 | JPY_million | tier2_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_cap_deduction` | esr | T2 | Tier2適格資本への上限適用による控除の額 | Tier2 상한 적용 공제(G) | JPY_million | tier2_eligible |  | － | － | n/a(not_yet) | 23/3 |  |
| `eligible_capital_total` | esr | T2 | 適格資本の額((A)+(D)) / 適格資本の額(A)+(D) | 적격자본 합계(A+D) — T2 표 합계행 | JPY_million |  | 1 | 9,278 | 40,290 | n/a(not_yet) | 23/3 | == eligible_capital |
| `rc_life` | esr | T3 | 生命保険リスクの額 | 생명보험리스크(A) | JPY_million | rc_pre_tax | 17 | － | － | n/a(not_yet) | 24/4 |  |
| `rc_nonlife` | esr | T3 | 損害保険リスクの額 | 손해보험리스크(B) | JPY_million | rc_pre_tax | 18 | 1,119 | 2,096 | n/a(not_yet) | 24/4 | <= rc_nl_liability + rc_nl_motor + rc_nl_property + rc_nl_other (correlation aggregation) |
| `rc_nl_liability` | esr | T3 | 賠償責任保険類似の商品に係るリスクの額 | 배상책임보험 유사 상품 리스크 | JPY_million | rc_nonlife |  | － | 283 | n/a(not_yet) | 24/4 |  |
| `rc_nl_motor` | esr | T3 | 自動車保険類似の商品に係るリスクの額 | 자동차보험 유사 상품 리스크 | JPY_million | rc_nonlife |  | － | 0 | n/a(not_yet) | 24/4 |  |
| `rc_nl_property` | esr | T3 | 財物保険類似の商品に係るリスクの額 | 재물보험 유사 상품 리스크 | JPY_million | rc_nonlife |  | 159 | 518 | n/a(not_yet) | 24/4 |  |
| `rc_nl_other` | esr | T3 | その他保険に係るリスクの額 | 기타보험 리스크 | JPY_million | rc_nonlife |  | 1,031 | 1,657 | n/a(not_yet) | 24/4 |  |
| `rc_catastrophe` | esr | T3 | 巨大災害リスクの額 | 거대재해리스크(C) | JPY_million | rc_pre_tax |  | 87 | 1,865 | n/a(not_yet) | 24/4 | <= rc_cat_natural + rc_cat_other - rc_cat_mgmt_action |
| `rc_cat_natural` | esr | T3 | 巨大自然災害リスクの額 | 거대자연재해리스크 | JPY_million | rc_catastrophe |  | － | 1,748 | n/a(not_yet) | 24/4 | <= rc_cat_nat_jp_earthquake + rc_cat_nat_jp_windflood + rc_cat_nat_jp_snow + rc_cat_nat_foreign + rc_cat_nat_other |
| `rc_cat_nat_jp_earthquake` | esr | T3 | 日本における地震に係るリスクの額 | 일본 지진 | JPY_million | rc_cat_natural |  | － | 546 | n/a(not_yet) | 24/4 |  |
| `rc_cat_nat_jp_windflood` | esr | T3 | 日本における風水災に係るリスクの額 | 일본 풍수해 | JPY_million | rc_cat_natural |  | － | 1,447 | n/a(not_yet) | 24/4 |  |
| `rc_cat_nat_jp_snow` | esr | T3 | 日本における雪災に係るリスクの額 | 일본 설해 | JPY_million | rc_cat_natural |  | － | 374 | n/a(not_yet) | 24/4 |  |
| `rc_cat_nat_foreign` | esr | T3 | 外国における巨大自然災害リスクの額 | 해외 거대자연재해 | JPY_million | rc_cat_natural |  | － | 156 | n/a(not_yet) | 24/4 |  |
| `rc_cat_nat_other` | esr | T3 | その他の額 | 기타(거대자연재해 내) | JPY_million | rc_cat_natural |  | － | － | n/a(not_yet) | 24/4 |  |
| `rc_cat_other` | esr | T3 | その他の巨大災害に係るリスクの額 | 기타 거대재해(팬데믹·테러 등) | JPY_million | rc_catastrophe |  | 87 | 918 | n/a(not_yet) | 24/4 |  |
| `rc_cat_mgmt_action` | esr | T3 | マネジメント・アクションの効果の額 | 경영조치 효과(거대재해) | JPY_million | rc_catastrophe |  | － | － | n/a(not_yet) | 24/4 |  |
| `rc_market` | esr | T3 | 市場リスクの額 | 시장리스크(D) | JPY_million | rc_pre_tax | 19 | 247 | 4,613 | n/a(not_yet) | 24/4 | <= rc_mkt_interest + rc_mkt_spread + rc_mkt_equity + rc_mkt_property + rc_mkt_fx + rc_mkt_concentration - rc_mkt_mgmt_action |
| `rc_mkt_interest` | esr | T3 | 金利リスクの額 | 금리리스크 | JPY_million | rc_market | 36 | － | 665 | n/a(not_yet) | 24/4 |  |
| `rc_mkt_spread` | esr | T3 | スプレッドリスクの額 | 스프레드리스크 | JPY_million | rc_market |  | 0 | － | n/a(not_yet) | 24/4 |  |
| `rc_mkt_equity` | esr | T3 | 株式リスクの額 | 주식리스크 | JPY_million | rc_market | 37 | － | 2,218 | n/a(not_yet) | 24/4 |  |
| `rc_mkt_property` | esr | T3 | 不動産リスクの額 | 부동산리스크 | JPY_million | rc_market | 38 | － | 1,591 | n/a(not_yet) | 24/4 |  |
| `rc_mkt_fx` | esr | T3 | 為替リスクの額 | 환리스크 | JPY_million | rc_market | 39 | － | 1,681 | n/a(not_yet) | 24/4 |  |
| `rc_mkt_concentration` | esr | T3 | 資産集中リスクの額 | 자산집중리스크 | JPY_million | rc_market | 40 | 247 | 1,412 | n/a(not_yet) | 24/4 |  |
| `rc_mkt_mgmt_action` | esr | T3 | マネジメント・アクションの効果の額 | 경영조치 효과(시장) | JPY_million | rc_market |  | － | － | n/a(not_yet) | 24/4 |  |
| `rc_credit` | esr | T3 | 信用リスクの額 | 신용리스크(E) | JPY_million | rc_pre_tax | 20 | 78 | 475 | n/a(not_yet) | 24/4 |  |
| `rc_operational` | esr | T3 | オペレーショナル・リスクの額 | 운영리스크(F) | JPY_million | rc_pre_tax | 21 | 251 | 463 | n/a(not_yet) | 24/4 |  |
| `rc_mgmt_action_excess` | esr | T3 | マネジメント・アクションの効果の上限超過額 | 경영조치 효과 상한초과액(G, 가산) | JPY_million | rc_pre_tax |  | － | － | n/a(not_yet) | 24/4 |  |
| `rc_diversification` | esr | T3 | 分散効果の額 | 분산효과(H, 차감) | JPY_million | rc_pre_tax | 16 | 274 | 2,530 | n/a(not_yet) | 24/4 |  |
| `rc_pre_tax` | esr | T3 | 所要資本の額(税効果考慮前) | 소요자본(세효과 고려전, I/J) | JPY_million | required_capital | 15 | 1,510 | 6,985 | n/a(not_yet) | 24/4 | = rc_life + rc_nonlife + rc_catastrophe + rc_market + rc_credit + rc_operational + rc_mgmt_action_excess - rc_diversification + rc_non_insurance_business |
| `rc_tax_effect` | esr | T3 | 所要資本の税効果の額 | 소요자본 세효과(J/K, 차감) | JPY_million | required_capital | 22 | 338 | 1,564 | n/a(not_yet) | 24/4 |  |
| `rc_post_tax` | esr | T3 | 所要資本の額(税効果考慮後) | 소요자본(세효과 고려후) — T3 합계행 | JPY_million |  | 14 | 1,171 | 5,420 | n/a(not_yet) | 24/4 | = rc_pre_tax - rc_tax_effect; == required_capital |
| `ebs_total_assets` | esr | T4 | 総資産 | EBS 총자산 | JPY_million |  |  | 22,664 | 64,031 | n/a(not_yet) | 25/5 | = statutory + reclass + revaluation (row-wise) |
| `ebs_intangibles` | esr | T4 | 無形固定資産 | EBS 무형고정자산 | JPY_million | ebs_total_assets |  | 4,778 | 1,978 | n/a(not_yet) | 25/5 | == tier1_adj_intangibles |
| `ebs_reinsurance_recoverables` | esr | T4 | 再保険回収額 | EBS 재보험회수액 | JPY_million | ebs_total_assets |  | 1,575 | 142 | n/a(not_yet) | 25/5 |  |
| `ebs_total_liabilities` | esr | T4 | 総負債 | EBS 총부채 | JPY_million |  |  | 8,783 | 21,912 | n/a(not_yet) | 25/6 | = ebs_insurance_liabilities + ebs_non_insurance_liabilities |
| `ebs_insurance_liabilities` | esr | T4 | 保険負債(保険契約準備金)合計 | EBS 보험부채 합계 | JPY_million | ebs_total_liabilities |  | 4,969 | 7,306 | n/a(not_yet) | 25/6 | = ebs_current_estimate + ebs_moce |
| `ebs_current_estimate` | esr | T4 | 現在推計の額 | 현재추계(최선추정부채, BEL) | JPY_million | ebs_insurance_liabilities |  | 4,917 | 7,099 | n/a(not_yet) | 25/6 |  |
| `ebs_moce` | esr | T4 | 現在推計を超えるマージン | MOCE(현재추계 초과 마진, 위험마진) | JPY_million | ebs_insurance_liabilities |  | 51 | 207 | n/a(not_yet) | 25/6 |  |
| `ebs_reg_reserve_in_liabilities` | esr | T4 | 規制上の準備金に属するもの | 규제상 준비금(위험준비금·이상위험준비금 등, 회계기준 보험부채 내) — イ열 | JPY_million | ebs_insurance_liabilities |  | 2,222 | 14,879 | n/a(not_yet) | 25/6 | reclassified to equity (ロ열 △) |
| `ebs_non_insurance_liabilities` | esr | T4 | 非保険負債合計 | EBS 비보험부채 합계 | JPY_million | ebs_total_liabilities |  | 3,814 | 14,605 | n/a(not_yet) | 25/6 |  |
| `ebs_other_reserves_reclass` | esr | T4 | その他の準備金 | 기타 준비금(부채로 재분류된 규제상 준비금 일부) — ニ열 | JPY_million | ebs_non_insurance_liabilities |  | － | 322 | n/a(not_yet) | 6 |  |
| `ebs_price_fluctuation_reserve` | esr | T4 | 価格変動準備金 | 가격변동준비금(회계기준, 자본으로 재분류) — イ열 | JPY_million | ebs_non_insurance_liabilities |  | － | 831 | n/a(not_yet) | 6 |  |
| `ebs_net_assets` | esr | T4 | 純資産 | EBS 순자산 | JPY_million |  | 4 | 13,880 | 42,118 | n/a(not_yet) | 25/7 | = ebs_total_assets - ebs_total_liabilities; == tier1_basic; = ebs_net_assets_statutory + ebs_regulatory_reserve_equity + ebs_ev_adjustment |
| `ebs_net_assets_statutory` | esr | T4 | 純資産 | 회계기준 순자산(EBS 표 イ열) | JPY_million | ebs_net_assets |  | 9,776 | 23,367 | n/a(not_yet) | 25/7 |  |
| `ebs_capital_stock` | esr | T4 | 基金又は資本金 / 資本金 | 자본금/기금 | JPY_million | ebs_net_assets |  | 3,150 | 10,000 | n/a(not_yet) | 25/7 |  |
| `ebs_capital_surplus` | esr | T4 | 資本剰余金 | 자본잉여금 | JPY_million | ebs_net_assets |  | 2,850 | 8,455 | n/a(not_yet) | 25/7 |  |
| `ebs_retained_earnings` | esr | T4 | 剰余金又は利益剰余金 / 利益剰余金 | 이익잉여금 | JPY_million | ebs_net_assets |  | 3,776 | 2,847 | n/a(not_yet) | 25/7 |  |
| `ebs_regulatory_reserve_equity` | esr | T4 | 規制上の準備金 | 규제상 준비금(자본으로 재분류된 합계) — ニ열 | JPY_million | ebs_net_assets |  | 2,222 | 15,389 | n/a(not_yet) | 25/7 | ≈ ebs_reg_reserve_in_liabilities + ebs_price_fluctuation_reserve - ebs_other_reserves_reclass (observed bridge) |
| `ebs_aoci` | esr | T4 | その他の包括利益累計額合計 / その他の包括利益累計額 | 기타포괄손익누계액 | JPY_million | ebs_net_assets |  | － | 2,064 | n/a(not_yet) | 7 |  |
| `ebs_ev_adjustment` | esr | T4 | 経済価値ベースの調整額 | 경제가치기준 조정액 | JPY_million | ebs_net_assets | 11 | 1,882 | 3,362 | n/a(not_yet) | 25/7 |  |
| `il_total_ex_moce` | esr | T6 | 保険負債 | 보험부채(MOCE 제외) 경제가치 | JPY_million |  |  | 4,917 | 7,099 | n/a(not_yet) | 28/11 | == ebs_current_estimate |
| `il_unexpired` | esr | T6 | 未経過責任に係る保険負債 | 미경과책임 보험부채(LRC 상당) | JPY_million | il_total_ex_moce |  | 2,020 | 823 | n/a(not_yet) | 28/11 |  |
| `il_incurred` | esr | T6 | 既経過責任に係る保険負債 | 기경과책임 보험부채(LIC 상당) | JPY_million | il_total_ex_moce |  | 2,897 | 6,275 | n/a(not_yet) | 28/11 |  |
| `rc_non_insurance_business` | esr | T1_combined | 非保険事業に係る所要資本の額 | 비보험사업 소요자본(i) — au 결합표에만 있는 행 | JPY_million | rc_pre_tax | 23 | － | － | n/a(not_yet) | 22 |  |
| `tier1_ratio_pct` | esr | derived |  | 기본자본비율 상당 = tier1_eligible / required_capital × 100 (일본 미공시, 파생) | pct | esr_pct | 28 | 777.3 | 740.6 | n/a(not_yet) |  | = tier1_eligible / required_capital * 100 |
| `esr_pct_5yr_summary` | esr | summary_5yr | 単体ベースのソルベンシー・マージン比率 / ソルベンシー・マージン比率 新基準 | 5개년 주요지표 표의 헤드라인(교차확인용) | pct | esr_pct |  | 791.7 | － | n/a(not_yet) | 2 | == esr_pct |
| `sens_jpy_rate_up50_esr_pct` | esr | T7 | 円金利50ベーシス・ポイント上昇 | 민감도 ESR: 엔 금리 +50bp | pct | esr_pct |  |  | 736.7 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_jpy_rate_down50_esr_pct` | esr | T7 | 円金利50ベーシス・ポイント下降 | 민감도 ESR: 엔 금리 -50bp | pct | esr_pct |  |  | 750.1 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_usd_rate_up50_esr_pct` | esr | T7 | 米ドル金利50ベーシス・ポイント上昇 | 민감도 ESR: 달러 금리 +50bp | pct | esr_pct |  |  | 743.3 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_usd_rate_down50_esr_pct` | esr | T7 | 米ドル金利50ベーシス・ポイント下降 | 민감도 ESR: 달러 금리 -50bp | pct | esr_pct |  |  | 743.2 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_jpy_ufr_down50_esr_pct` | esr | T7 | 円金利UFR50ベーシス・ポイント下降 | 민감도 ESR: 엔 UFR -50bp | pct | esr_pct |  |  | 743.2 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_equity_property_down10_esr_pct` | esr | T7 | 株式・不動産10%下落 | 민감도 ESR: 주식·부동산 -10% | pct | esr_pct |  |  | 764.4 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_fx_yen_up10_esr_pct` | esr | T7 | 為替10%円高 | 민감도 ESR: 환율 10% 엔고 | pct | esr_pct |  |  | 755.9 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `internal_model_applied` | esr | T8 | 内部モデル手法の適用 | 내부모형 적용 여부 | flag |  |  | unstated | False | n/a(not_yet) |  |  |
| `usp_applied` | esr | T8 | 会社固有のストレス係数手法の適用 | 회사고유 스트레스계수(USP) 적용 여부 | flag |  |  | unstated | False | n/a(not_yet) |  |  |
| `internal_discount_rate_applied` | esr | T8 | 内部割引率手法の適用 | 내부할인율 적용 여부 | flag |  |  | unstated | False | n/a(not_yet) |  |  |
| `mgmt_action_applied` | esr | T8 | マネジメント・アクション | 경영조치(management action) 반영 여부 | flag |  |  | unstated | False | n/a(not_yet) |  |  |
| `risk_mitigation_reinsurance` | esr | T8 | リスク削減手法 / リスク削減効果 | 재보험 리스크경감 반영 여부 | flag |  |  | True | True | n/a(not_yet) |  |  |
| `transitional_measures` | esr | T8 | 経過措置 / 激変緩和 | 경과조치(激変緩和措置) 적용 여부 | flag |  |  | False | False | n/a(not_yet) |  |  |
| `sensitivity_omitted` | esr | T8 | 記載を省略 | 민감도 표 생략 여부(차이 1%p 미만 사유) | flag |  |  | True | False | n/a(not_yet) |  |  |
| `first_year_no_movement_analysis` | esr | T8 | 変動要因分析 | 변동요인분석 미기재(초년도) | flag |  |  | True | False | n/a(not_yet) |  |  |
| `calc_method` | esr | T8 | 内部モデル手法の適用 / 標準的手法 | 산정방식 standard / standard_implied / internal_model | enum |  |  | standard_implied | standard | n/a(not_yet) |  | derived from internal_model_applied |
| `discount_bucket_jpy` | esr | T8 | 適用バケット / 一般バケット / ミドルバケット / トップバケット | 엔화 할인율 버킷 | enum |  |  | 一般バケット | 一般バケット | n/a(not_yet) |  |  |
| `discount_rates_jpy` | esr | T8 | 主な通貨 / 主要な年限ごとの割引率 | 엔화 할인율(연한별 %) | pct_by_tenor |  |  | {'1y': 1.21, '2y': 1.447, '3y': 1.576} | {'5y': 1.889, '10y': 2.49, '15y': 3.013, '20y': 3.579} | n/a(not_yet) |  |  |
| `esr_status` | article_axes | axes:esr_placeholder | 後日公表予定 / 別途公表予定 / 2026年10月末に公表予定 | posted / not_yet / not_found | enum |  |  | posted | posted | not_yet |  |  |
| `esr_placeholder_locations` | article_axes | axes:esr_placeholder | ソルベンシー・マージン比率 新基準 / 保険金等の支払能力の充実の状況（ソルベンシー・マージン比率） | '後日公表予定' 문구가 놓인 표/절 위치 목록(10월에 채워질 자리) | list |  |  | － | － | 3 loc |  |  |
| `smr_old_basis_fy2024_pct` | article_axes | axes:esr_placeholder | ソルベンシー・マージン比率 旧基準 | 구기준 SMR FY2024 (비교 참고, ESR 아님) | pct |  |  | － | － | 863.9 |  |  |
| `cat_reserve_total` | article_axes | axes:catastrophe_reserve_adequacy | 異常危険準備金 / 責任準備金の内訳 | 이상위험준비금 잔액 합계(전 종목) | JPY_million |  |  | 2,222 | － | － |  |  |
| `cat_reserve_fire` | article_axes | axes:catastrophe_reserve_adequacy | 火災 行 × 異常危険準備金 列 | 화재 종목 이상위험준비금 잔액(금융청 부족 지적 대상) | JPY_million |  |  | － | － | － |  |  |
| `cat_reserve_by_line` | article_axes | axes:catastrophe_reserve_adequacy | 火災/海上/傷害/自動車/自動車損害賠償責任/その他 | 종목별 이상위험준비금 잔액 | dict |  |  | {"火災": null, "海上": null, "傷害": 1421, "自動車": null, "自動車損害賠償責任": null, "その他": 800} | － | － |  |  |
| `ordinary_reserve_total` | article_axes | axes:catastrophe_reserve_adequacy | 普通責任準備金 | 보통책임준비금 합계(같은 표) | JPY_million |  |  | 3,259 | － | － |  |  |
| `cat_reserve_adequacy_note` | article_axes | axes:catastrophe_reserve_adequacy | 積立不足 / 積立率 / 異常危険準備金の取崩 | 적립 부족/적립률 서술 유무 (없으면 null) | text |  |  | － | NOT_IN_SAMPLE_DOC (別冊 業績データ has no 責任準備金の内訳 table — main disclosure volume needed) | － |  |  |
| `air_used` | article_axes | axes:air_used | アセット・インテンシブ / 資産集約型再保険 / 再保険 | not_mentioned / mentioned / mentioned_esr_purpose | enum |  |  | not_mentioned | not_mentioned | not_mentioned |  |  |
| `air_evidence` | article_axes | axes:air_used | 既契約の出再に伴う損益 / 共同保険式再保険 / 最低保証再保険 | AIR 정황 근거(기계약 출재 손익·관계사 재보험 각주 등) | text |  |  | － | － | 基礎利益 note: 既契約の出再に伴う損益を除外 (in-force block cession P&L excluded from core profit); 関連当事者取引 note: 共同保険式再保険・最低保証再保険 (coinsurance-type / guarantee reinsurance with group company) |  |  |
| `inforce_cession_pl` | article_axes | axes:air_used | 既契約の出再に伴う損益に相当する額 | 기계약 출재 관련 손익(기초이익에서 제외된 액) | JPY_million |  |  | － | － | -3,733 |  |  |
| `reins_counterparties_n` | article_axes | axes:air_used | 出再先保険会社の数 / 再保険を引き受けた主要な保険会社等の数 | 출재 상대 재보험사 수 | count |  |  | 5 | － | 5 |  |  |
| `reins_top5_share_pct` | article_axes | axes:air_used | 出再保険料のうち上位5社の出再先に集中している割合 / 支払再保険料の金額が大きい上位5社に対する支払再保険料の割合 | 상위 5사 출재보험료 집중도 | pct |  |  | 100.0 | － | 100.0 |  |  |
| `reins_rating_a_or_above_pct` | article_axes | axes:air_used | 出再保険料の格付ごとの割合 / 格付機関による格付に基づく区分ごとの支払再保険料の割合 | A등급 이상 재보험사 출재보험료 비중 | pct |  |  | 80.0 | － | 100.0 |  |  |
| `reins_unreceived_claims` | article_axes | axes:air_used | 未だ収受していない再保険金の金額 | 미수 재보험금 | JPY_million |  |  | － | － | 17,042 |  |  |
| `core_profit` | article_axes | axes:interest_margin_sign | 基礎利益 | 기초이익(당기) | JPY_million |  |  | － | － | 18,523 |  |  |
| `core_profit_prev` | article_axes | axes:interest_margin_sign | 基礎利益 | 기초이익(전기) | JPY_million |  |  | － | － | 14,828 |  |  |
| `negative_spread_100m` | article_axes | axes:interest_margin_sign | 逆ざや / 逆鞘 | 역마진(逆ざや) 금액 — 단위 億円(표본 원문 단위) — 양수=역마진 존재 | JPY_100million |  |  | － | － | 37 |  |  |
| `negative_spread_prev_100m` | article_axes | axes:interest_margin_sign | 逆ざや | 역마진 전기(億円) | JPY_100million |  |  | － | － | 67 |  |  |
| `interest_margin` | article_axes | axes:interest_margin_sign | 利差損益 / 利差益 / 利差損 / 順ざや | 이차손익(三利源 공시사에서만) | JPY_million |  |  | － | － | － |  |  |
| `interest_margin_sign` | article_axes | axes:interest_margin_sign | 利差損益 / 逆ざや / 順ざや | positive / negative / unstated (역마진이면 negative) | enum |  |  | － | － | negative |  |  |
| `three_source_disclosed` | article_axes | axes:interest_margin_sign | 利差損益 / 危険差損益 / 費差損益 | 三利源(利差·危険差·費差) 분해 공시 여부 | bool |  |  | － | － | False |  |  |

## 4. 검산식과 결과 (`run_checks` / `run_axes_checks`)

허용오차 원칙: 금액은 百万円 미만 **절사**(au 주기 5 "記載単位未満を切り捨て")라, 합계행 = Σ내역 검산은 항 수만큼 ±1 씩 벌어질 수 있다. 비율은 분자·분모 각각 [x, x+1) 구간이라 **구간 검산**.

| id | 식 | 오차 | au | MY | 비고 |
|---|---|---|---|---|---|
| C01 | `esr_pct ∈ [E/(R+1), (E+1)/R]×100` | ±0.05 | 791.7 ∈ [791.64, 792.40] | 743.2 ∈ [743.22, 743.38] | 점추정 792.31 / 743.36 — **소수 첫째자리 반올림으로는 안 맞는다**, 구간으로만 맞는다 |
| C02 | `eligible_capital == eligible_capital_total` (T1 == T2 합계행) | 0 | 9,278 | 40,290 | |
| C03 | `required_capital == rc_post_tax` (T1 == T3 합계행) | 0 | 1,171 | 5,420 | |
| C04 | `eligible = tier1 + tier2` | ±1 | 9,102+175=9,277 vs 9,278 | 40,140+149=40,289 vs 40,290 | 둘 다 절사 1 차이 |
| C05 | `tier1 = tier1_basic − tier1_adjustments` | ±1 | 13,880−4,778 | 42,118−1,978 | |
| C06 | `tier1_basic = 無制限調達手段 + 制限付 + 調達手段以外` | ±1 | 3,150+10,730 | 10,000+32,118 | |
| C07 | `調達手段以外 = 剰余金等 + 資本剰余金 + AOCI + 拠出金 + 経済価値調整額` | ±2 | 5,998+2,850+0+0+1,882 | 18,237+8,455+2,064+0+3,362 | |
| C08 | `tier1_adjustments = Σ 7개 공제` | ±2 | 4,778 (무형만) | 1,978 (무형만) | |
| C09~C11 | Tier2 (D)=(E)−(F)−(G), (E)=조달수단+그 외, 그 외 = 3 내역 | ±1 | 175 | 149 | 두 회사 모두 Tier2 = バスケット 뿐 |
| C12 | `rc_pre_tax = A+B+C+D+E+F+G − H (+ 非保険事業)` | ±9 | 1,508 vs 1,510 | 6,982 vs 6,985 | 항별 절사 누적 |
| C13 | `rc_post_tax = rc_pre_tax − rc_tax_effect` | ±1 | 1,510−338=1,172 vs 1,171 | 6,985−1,564=5,421 vs 5,420 | |
| C14~C17 | 부모 리스크 ≤ Σ 하위 (상관 통합이라 단순합 아님, 표 주기) | ≤ | 損保 1,119 ≤ 1,190 · 市場 247 = 247 | 損保 2,096 ≤ 2,458 · 巨大災害 1,865 ≤ 2,666 · 自然災害 1,748 ≤ 2,523 · 市場 4,613 ≤ 7,567 | **등식이 아니라 부등식** — 하위합으로 부모를 재계산하면 안 됨 |
| C18 | `tier1_basic == ebs_net_assets` | 0 | 13,880 | 42,118 | T2 ↔ T4 교차 |
| C19 | `ebs_net_assets = 総資産 − 総負債` | ±1 | 22,664−8,783=13,881 | 64,031−21,912=42,119 | |
| C20 | `総負債 = 保険負債 + 非保険負債` | ±1 | 4,969+3,814 | 7,306+14,605 | |
| C21 | `保険負債 = 現在推計 + MOCE` | ±1 | 4,917+51=4,968 | 7,099+207 | |
| C22 | `EBS 純資産 = 회계 純資産 + 規制上の準備金 + 経済価値調整額` | ±1 | 9,776+2,222+1,882 | 23,367+15,389+3,362 | 회계→경제가치 순자산 브리지 |
| C23~C27 | T2 내역 ↔ T4 자본항목 교차(調整額·無形·資本剰余金·剰余金等=利益剰余金+規制上準備金·AOCI) | 0~±1 | 전부 일치 | 18,237 = 2,847+15,389 (Δ1) | |
| C28~C29 | T6 `保険負債(MOCE除く) == 現在推計`, `= 未経過 + 既経過` | ±1 | 4,917 = 2,020+2,897 | 7,099 = 823+6,275 (Δ1) | |
| C30 | 5개년 표 헤드라인 == esr_pct | 0 | 791.7 | (별책엔 5개년 표 없음) | |
| C31 | 민감도 基準열 == 헤드라인(9행) 또는 생략 주기 존재 | 0 | 생략 주기 확인 | 9/9 일치 | au 는 "差の絶対値がいずれも1%未満" 주기로 값 생략 |
| C32 | 差額表 = 水準表 − 基準 (pct ±0.15, 금액 ±1) | count | — | 57/57 | 절사로 447 vs 448 같은 1 차이 발생 |
| C33 | 시나리오별 esr == eligible/required 구간 | count | — | 7/7 | |
| C34 | `規制上の準備金(자본) = 危険準備金等(부채 イ열) + 価格変動準備金 − その他の準備金(ニ열)` | ±2 | 2,222 = 2,222 | 15,389 ≈ 14,879+831−322 = 15,388 | 표본 2건 관측식(告示 정의 확인 전) |
| A01 | `規制上の準備金 == 異常危険準備金 합계 (+価格変動準備金)` | ±1 | 2,222 == 2,222 | (별책에 표 없음) | au 는 이상위험준비금이 유일한 규제상 준비금 |
| A02 | 출재 격付 비중 합 = 100 | ±0.2 | 80+0+20 | — | NN Life 10.8+88.8+0.4 |
| A03~A04 | 基礎利益 정수 파싱 / `interest_margin_sign == negative ⇔ 逆ざや > 0` | — | — | — | NN Life 37億円 → negative |
| A05 | `esr_status == not_yet` 이면 placeholder 위치 ≥ 1 | — | — | — | NN Life 3곳 |

결과: **au 34/34, Meiji Yasuda Non-Life 41/41, NN Life 4/4 통과, census 헤드라인 2/2 일치, NN Life census `not_yet` 일치.**

## 5. 추출 규칙 (10월 62사 적용)

1. **라벨 정규화**: 줄 단위 NFKC → `（A）`→`(A)`, `Tier１`→`Tier1`, `－`→`-`. 대시 집합 `- ー − ― ‐` 는 null. `△`/`▲` 접두 = 음수. `%` 접미 허용.
2. **열 순서**: FY2025 는 모든 표가 `イ=前年度(－) / ロ=当年度 (/ ハ=増減)` — 값 토큰 **2번째**가 당기. FY2026 부터는 前年度 열이 채워지므로 같은 규칙으로 2번째 = 당기(증감 열 유무 무관). EBS 는 4열이라 마지막 토큰 = 経済価値, 첫 토큰 = 財務会計(4토큰 행에서만).
3. **중복 라벨은 순차 커서**: `マネジメント・アクションの効果の額` 은 巨大災害 안·市場 안 두 번, `財物保険類似` 등은 T6 에 여러 번. 표 안에서 앞 항목 매치 위치 다음부터 찾는다(ITEMS 순서 = 양식 행 순서).
4. **라벨 뒤 코드/계속줄 건너뛰기**: `(A)`, `①`, `(a)+(b)+…`, `（（J）－（K））`, 줄바꿈된 라벨 후반부(`余金の額`, `金に属するもの以外）`)가 값 앞에 최대 6줄 끼어든다.
5. **행 생략 회사**: au 는 EBS 에서 값이 전부 대시인 행을 통째로 뺀다(`価格変動準備金`·`その他の包括利益累計額`·`コールローン` 등). MY 는 양식 전 행을 찍는다. → 못 찾은 행은 `ROW_OMITTED`(=0) 로 두고 실패로 치지 않는다. T2·T3 는 두 회사 다 전 행 인쇄.
6. **정성 플래그는 정성 페이지(T8)+민감도 페이지(T7)에서만 검색**한다. 전체 문서에서 `マネジメント・アクション` 을 찾으면 T3 행 라벨에 걸려 "적용" 으로 오판한다(실측 사고, 수정됨). MY 처럼 항목식(`該当ありません`)이면 False, au 처럼 언급이 없으면 `unstated`.
7. **`calc_method`**: `内部モデル手法の適用 該当ありません` → `standard`; 언급 없음 → `standard_implied`(규제상 내부모형은 승인·공시 의무라 무언급 = 표준식으로 본다, 단 census 에는 구분 유지). `confidence_level` 은 양식에 없다 — 告示 표준식 = 1년 VaR 99.5% 고정이라 `standard` 면 99.5 로 채운다.
8. **경과조치(激変緩和措置)**: 두 표본 모두 `経過措置` 문자열 0건 → 양식에 경과조치 표가 없다. 회사가 적용하면 정성 절 "その他の重要な前提及び手法" 에 문장으로 나올 것이므로 그 절에서 검색(`transitional_measures` 플래그). 한국 K-ICS 처럼 적용전/적용후 2열 표는 **없다**.
9. 헤드라인 5개년 표(au p2·NN p11): 열이 **오래된→최신** 순, 신기준은 마지막 열만 값. `esr_pct_5yr_summary` = 페이지의 마지막 `%` 토큰.

## 6. K-ICS 대응 (`kics_item_ref`) — 억지 대응 금지 원칙

| J-ESR id | K-ICS | 대응 성격 |
|---|---|---|
| `eligible_capital` / `eligible_capital_total` | 1 지급여력금액 | 정확 |
| `required_capital` / `rc_post_tax` | 14 지급여력기준금액 | 정확(둘 다 세효과 후) |
| `esr_pct` | 27 지급여력비율 | 정확 |
| `tier1_eligible` / `tier2_eligible` | 2 기본자본 / 3 보완자본 | 정확 |
| `tier1_basic` / `ebs_net_assets` | 4 건전성감독기준 재무상태표 순자산 | 근사(일본 Tier1 기초항목 = EBS 순자산 그대로; 한국 4 도 감독기준 BS 순자산) |
| `tier1_instr_unrestricted` / `tier1_instr_restricted` | 5 보통주 / 6 보통주 이외 자본증권 | 근사(일본은 資本金·基金 = 무제한 조달수단; 한국 5 는 보통주 자본금+주식발행초과금 범위가 다를 수 있음) |
| `tier1_ni_retained_earnings` | 7 이익잉여금 | 근사(일본은 規制上の準備金 포함) |
| `tier1_ni_aoci` | 9 기타포괄손익누계액 | 정확 |
| `tier1_ni_ev_adjustment` / `ebs_ev_adjustment` | 11 조정준비금 | 근사(둘 다 회계 순자산→감독 순자산 차이 계정) |
| `tier1_adjustments` | 12 불인정 항목 | 부분(한국 12 는 예정배당 등, 일본 (C) 는 무형·DTA·자기보유 등 — 공제라는 위치만 같다) |
| `tier2_instr_t1_excess` | 13 보완자본 재분류 항목 | 정확 |
| `rc_pre_tax` | 15 기본요구자본 | 근사(일본은 非保険事業 (i) 포함, 한국 15 는 미포함·23 별도) |
| `rc_diversification` | 16 분산효과 | 정확(부호: 둘 다 차감) |
| `rc_life` | 17 생명장기손해보험위험액 | 부분(한국 17 은 장기손보 포함) |
| `rc_nonlife` | 18 일반손해보험위험액 | 부분(한국 18 은 대재해 포함, 일본은 巨大災害 (C) 별도) |
| `rc_catastrophe`, `rc_cat_*` | — | **null**: 한국 대재해는 18 내부(별도 번호 없음). 35 대재해위험액은 생명장기 하위라 다른 개념 |
| `rc_market` | 19 시장위험액 | 정확 |
| `rc_mkt_interest/equity/property/fx/concentration` | 36/37/38/39/40 | 정확 |
| `rc_mkt_spread` | — | **null**: K-ICS 시장위험에 스프레드 없음(신용스프레드는 신용위험) |
| `rc_credit` / `rc_operational` | 20 / 21 | 정확 |
| `rc_tax_effect` | 22 법인세조정액 | 정확 |
| `rc_non_insurance_business` | 23 기타 요구자본 | 근사 |
| `tier1_ratio_pct` (파생) | 28 기본자본비율 | 정확(일본 미공시라 tier1/required 로 파생) |
| 민감도 `純資産の額` × 円金利 ±50bp | 41(충격전)/43(상승)/44(하락) | 근사(K-ICS 는 규정 충격 시나리오, 일본은 50bp 평행) — 스키마 `sensitivity.rows[].kics_item_ref` |
| `sens_*_esr_pct` | — | null: 한국은 ESR-under-shock 항목이 없고 `kics_rate_sensitivity.json` 별도 마스터 |
| EBS·T6·MOCE·할인율·article_axes 전부 | — | null(한국 마스터에 개념 없음) |

## 7. 회사별 편차 (10월엔 이 편차가 62사로 늘어난다)

### 7-1. 손보 2사(같은 규제 양식) 사이의 편차

| 축 | au Non-Life | Meiji Yasuda Non-Life | 추출기 대응 |
|---|---|---|---|
| 문서 | ディスクロージャー誌 본편의 業績データ 장 안(인쇄 p69~79) — 5개년 표·재보험·준비금 표와 같은 파일 | 【別冊】業績データ 가 ESR 양식 전용, 본편 별도 | 3축은 별책 회사면 **본편을 하나 더 열어야** 한다 |
| 헤드라인 표 | (1) 결합표(Tier1/2 + 리스크 (a)~(k)) **와** (2) 要約 두 번 | 要約 한 번 | T1 은 要約 에서, (i) 非保険事業 은 결합표에서 |
| 열 | 前年度/当年度/増減 3열 | 前年度/当年度 2열(요약만 増減 있음) | 2번째 토큰 = 당기, 공통 |
| 리스크 코드 | T3 세효과전 (I), 세효과 (J) | (J), (K) | 코드 무시, 라벨로 매칭 |
| EBS 행 | 값 없는 행 생략(価格変動準備金·AOCI·コールローン 등) | 전 행 인쇄 | `ROW_OMITTED` 허용 |
| 민감도 | 값 전부 대시 + "差の絶対値がいずれも1%未満" 주기 | 水準表 + 差額表 2개 | `sensitivity_omitted` 플래그, 生命保険リスク 행 au 없음 |
| 정성 절 | 문장식(내부모형·USP 언급 없음 → `unstated`) + 変動要因分析 절(초년도 該当なし) | 항목식(a~e 전부 該当ありません → False) | tri-state |
| 할인율 표 | 1/2/3년 (단기 상품) | 5/10/15/20년 | 연한 키는 회사별 |
| 규제상 준비금 | 異常危険準備金 2,222 뿐(価格変動準備金 0) | 危険準備金等 14,879 + 価格変動準備金 831 − その他 322 | C34 관측식 |
| 단위 | 百万円 | 百万円 | 둘 다 百万円. **생보 대형사·지주 결산설명자료는 億円** 이 관행이라 10월엔 `unit_disclosed` 열 필수(§5) |
| 세효과 | 세효과전→세효과의 額→세효과후 3행 동일 | 동일 | 헤드라인 (B) = 세효과 **후** 로 통일(둘 다) |

### 7-2. 생보 양식 vs 손보 양식 (article_axes 층)

| 축 | 손보 (au / MY) | 생보 (NN Life) |
|---|---|---|
| `catastrophe_reserve_adequacy` | 본편 `責任準備金の内訳` 표: 종목(火災/海上/傷害/自動車/自賠責/その他) × 열(普通責任準備金/異常危険準備金/危険準備金/払戻積立金/契約者配当準備金等/合計). au 는 火災 없음(상해·기타 보험사)이라 `cat_reserve_fire` null — 금융청 부족 지적 대상(화재)은 대형 손보에서만 의미. 적립 부족 서술은 두 표본 모두 없음 | **해당 없음**(생보엔 이상위험준비금 없음. 대신 危険準備金 + 責任準備金積立率 100% 표) |
| `air_used` | 出再 표 `(10) 出再先保険会社の数·上位5社割合`, `(11) 格付ごとの割合`(A以上/BBB以上/その他 3버킷). AIR 언급 0 | 재보험 표 `(4) 主要な保険会社等の数`, `(5) 上位5社`, `(6) 格付区分`(AA−/A+/A 등 세부 등급, 괄호 = 제3분야 무적립 계약분), `(7) 未収再保険金`. AIR(`アセット・インテンシブ`) 언급 0 이지만 **정황 2건**: 基礎利益 주기 "既契約の出再に伴う損益を除外"(FY2025 △3,733百万円) + 관련당사자 각주 "共同保険式再保険・最低保証再保険"(그룹사 출재) → `air_evidence` 에 기록, `air_used=not_mentioned` 유지 |
| `interest_margin_sign` | **해당 없음**(손보엔 이차손익·逆ざや 개념 없음) | 健全性 box `逆ざや 67→37 億円`(단위 **億円**, 다른 표는 百万円) → negative. `基礎利益` 표(p60)는 キャピタル損益·臨時損益 분해뿐 **三利源(利差·危険差·費差) 분해 없음** → `three_source_disclosed=false`. 대형 생보는 三利源 을 내므로 `interest_margin` 은 그쪽에서 채운다 |
| ESR 헤드라인 | 규제 양식 표 | `後日公表予定` 3곳(§7-3) |

### 7-3. NN Life 의 ESR 빈 자리 골격 (10월에 채워질 위치)

1. p11 主要な経営指標 5개년 표: 행 `ソルベンシー・マージン比率` 가 `新基準`(전 열 `-`, 2025 열에 `(注2)`) / `旧基準`(783.4→863.9%, 2025 `-`) 2단. 주기 (注2) "…2025年度より異なる基準によって算出されます。なお、当該数値に関しては、後日公表予定です。" — **구기준도 FY2025 부터 중단**(au 도 "旧制度による前年度以前の数字の記載を省略").
2. p15 健全性 box: `新基準 -（別途公表予定）`, `旧基準 863.9 / -`, 같은 페이지 `逆ざや` 표.
3. p54 業績・データ編 "7. 保険金等の支払能力の充実の状況（ソルベンシー・マージン比率）": **표 없이 문장 1단락**. 10월엔 여기(또는 별책)에 au (1)~(11) 과 같은 규제 양식 표가 들어올 것으로 본다 — census 는 `esr_placeholder_locations` 의 페이지를 먼저 다시 연다.
4. p42 회사데이터편 5개년 표 재게재(1과 동일 주기).

### 7-4. 10월 62사에서 예상되는 추가 편차(표본에 없어 미검증, notes 에 적을 것)

- 지주 6사·상호회사 5사: 결산설명자료 헤드라인이 **그룹 연결**(`scope=group`)이고 단위 億円·소수 0~1자리. 규제 양식 단체값은 디스클로저지 별책. 둘 다 적되 `scope` 구분.
- 생보: T3 에 `生命保険リスク (A)` 가 채워지고 하위(死亡/長寿/罹患/解約/経費 등) 행이 생긴다 — 표본에 없어 ITEMS 에 미등록. 발견 즉시 `rc_life_*` 로 추가(K-ICS 29~34 대응 후보).
- 내부모형 승인사·USP 적용사: 정성 절이 `適用しています` 로 바뀌며 `calc_method=internal_model`. 경과조치 적용사는 문장으로만.
- 억円 표기 회사: 절사 구간 검산의 폭이 100배 커진다(C01 의 ±1 → ±100百万円). `unit_disclosed` 로 분기.
