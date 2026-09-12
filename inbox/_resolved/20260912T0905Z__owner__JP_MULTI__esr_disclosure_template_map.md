---
from: owner
to: jp
created: 20260912T0905Z
status: resolved
route: investigate
company: JP_MULTI
period: FY2025
track: J-ESR
---

## 미결 (owner) — 규제 양식 ESR 공시 2건을 뜯어 "공시 양식 지도" + 기계 스키마를 미리 만든다 (10월 62사 대비)

**배경.** 09-12 census posted 15사 중 규제 양식(ディスクロージャー誌·別冊)으로 ESR 표를 낸 곳은 2사뿐:
- au損害保険 `J-ESR/raw/fy2025_samples/au_nonlife_disclo_260730_4of5.pdf` (31p; p2 헤드라인 791.7%, p21~22 신기준 표 —
  適格資本(A) 9,278百万円·所要資本(B, 税効果考慮後) 1,171百万円)
- 明治安田損害保険 `J-ESR/raw/fy2025_samples/meijiyasuda_nonlife_20260904_performance_data.pdf` (14p; p2 표 (A) 40,290·(B) 5,420·
  743.2%, p12 민감도 표 — UFR 50bp 下降 / 株式・不動産 10% 下落 / 為替 10% 円高 등)
나머지 8사(지주·대형 생보)는 결산설명자료 헤드라인만. 10월 말 62사가 낼 것은 이 규제 양식이므로, **지금 이 2건으로 양식을
해부해 두면 10월에 회사마다 다른 표를 같은 열로 뽑을 수 있다.** owner 09-12 지시.

**할 일.**
1. 두 PDF 를 fitz 로 페이지별 텍스트/표 구조를 뜯는다(스캔이면 렌더 확인). ESR 관련 표 **전부**(헤드라인·구성요소·리스크별
   소요자본 분해·분산효과·적격자본 구성(Tier/資本性·負債性 등 있으면)·민감도·경과조치 있으면 그것도) 를 찾아 항목을 열거한다.
   "ESR 표 하나만" 보고 끝내지 말 것 — 라벨 변형 목록은 `docs/domains/claude-agent-jp.md` §3 참고.
2. 산출 A: `docs/domains/jp_esr_disclosure_template.md` — 항목 표(항목 id · 일본어 라벨(변형 포함) · 한국어 뜻 · 단위 · 어느 표/
   어느 페이지 근처 · 두 회사 실측값 · 검산식). 검산식 예: `esr = eligible / required`, `required = Σ리스크 − 분산효과`(표가 그렇게
   돼 있으면), 민감도 표의 "基準" 열 = 헤드라인.
3. 산출 B: `J-ESR/esr_disclosure_schema.json` — 기계용 스키마(`items[]`: id, labels_ja[], unit, parent, formula|null, required:true/false).
   census csv 의 확장 열 이름은 이 id 를 그대로 쓴다(10월 티켓이 참조).
4. 산출 C: `J-ESR/raw/fy2025_samples/extracted_sample_values.json` — 스키마대로 두 회사 값을 채운 표본 + self-check(검산식 통과 여부).
   두 회사 헤드라인은 census 값(791.7 / 743.2)과 일치해야 한다.
5. 두 회사 양식이 서로 다른 점(항목 유무·라벨·단위 百万円 vs 億円·세효과 처리)을 문서 끝에 "회사별 편차" 절로 적어라 — 10월에
   그 편차가 62사로 늘어난다.

**규칙.** `docs/domains/claude-agent-jp.md` 4절 그대로(브라우저 금지 — 이 작업은 로컬 PDF 만 쓰니 네트워크 불필요). python 풀패스,
멀티라인 `python -c` 금지, UTF-8 BOM 없음. 서브에이전트 생성 금지. `jp/`·마스터 JSON 수정 금지. 끝나면 답변란에 항목 수·검산 결과·
편차 요약을 적고 `status: answered`, `TODO_jp.md` 갱신, `docs/changelog_jp.md` 기록. 보고문에 일본어 문자 금지(라벨은 문서 안에만).

## 범위 확장 (owner 2026-09-12, 발주 직후)

owner 질문 "기사 3축 수요와 한국 양식에 부합하나?" → ESR 표만으로는 절반. 아래를 **같은 산출물에 추가**한다.

6. **K-ICS 대응 열.** 스키마 `items[]` 각 항목에 `kics_item_ref`(대응하는 한국 K-ICS 마스터 항목번호, 없으면 null)를 붙인다.
   대응 규칙: 適格資本 ↔ 1(지급여력금액), 所要資本 ↔ 14(지급여력기준금액), 리스크별 소요자본 ↔ 15~24 계열(보험/시장/신용/운영/
   분산효과 — 정확한 번호는 `docs/agents/kics-json-validation-rules.md` 항목표로 확인), 금리민감도 ↔ 41~46. 억지 대응은 금지 —
   개념이 다르면 null 로 두고 문서에 이유.
7. **기사 3축 섹션도 같은 문서에서 뜯는다** (`docs/domains/claude-agent-jp.md` §4b 의 열 이름 그대로):
   - 손보 표본 2건(au·明治安田損保): `異常危険準備金` 표(적립액·적립률·부족 여부 서술) → `catastrophe_reserve_adequacy`;
     재보험 절(出再·再保険会社 집중, AIR 언급 유무) → `air_used`.
   - 생보 표본 신규 1건: `J-ESR/raw/fy2025_samples/nnlife_2025disclosure_202607.pdf`(NN Life 디스클로저지 2026-07-29 발행, 95p,
     ESR 은 "後日公表予定" 이라 헤드라인은 없지만 양식은 있다): `基礎利益` 분해의 `利差損益`(부호·逆ざや 서술) → `interest_margin_sign`;
     재보험/AIR(`アセット・インテンシブ`·`再保険`) 절 → `air_used`; 그리고 ESR 자리에 "後日公表予定" 이 어떤 표 틀로 비어 있는지
     (10월에 채워질 표의 골격) 도 항목 열거.
   스키마는 두 층으로: `layer: "esr"`(ESR 표) / `layer: "article_axes"`(3축). 표본값 JSON 도 두 층.
8. 문서의 "회사별 편차" 절에 생보/손보 양식 차이(생보엔 이상위험준비금 없음·손보엔 이차손익 없음 등)를 명시.

## 답변 (jp, 2026-09-12)

**산출물 (전부 UTF-8 BOM 없음, LF).**
- (A) `docs/domains/jp_esr_disclosure_template.md` — 양식 구조(告示 정량 7절+정성 2절 = T1~T8) · 항목 표 131행 · 검산식 C01~C34/A01~A05 ·
  추출 규칙 9개 · K-ICS 대응표 · 회사별 편차(손보 2사 / 생보 vs 손보 / NN Life 빈 자리 골격 / 10월 예상 편차).
- (B) `J-ESR/esr_disclosure_schema.json` — `items[]` 131개 = `layer:"esr"` 109 + `layer:"article_axes"` 22. 각 항목 id·labels_ja·ko·unit·
  parent·formula·required·column·`kics_item_ref`(억지 대응 없이 27개만, 근사는 문서 §6 에 사유). `sensitivity.scenarios` 8·`rows` 10.
- (C) `J-ESR/raw/fy2025_samples/extracted_sample_values.json` — 3사 값 + 검산 결과. 생성기 `J-ESR/extract_esr_template_samples.py`
  (10월 62사 추출기의 프로토타입, exit 0 = 검산 전부 통과 + census 일치).

**항목 수·검산.** 
| 회사 | esr 층 매치/비null/총 | axes 층 비null | 검산 | census |
|---|---|---|---|---|
| au Non-Life | 88 / 52 / 91 (미매치 3 = au 가 EBS 에서 생략한 빈 행: 価格変動準備金·その他の準備金·AOCI) | 9 | 34/34 | 791.7 일치 |
| Meiji Yasuda Non-Life | 90 / 65 / 91 (미매치 1 = 非保険事業 행이 양식에 없음) | 4 | 41/41 | 743.2 일치 |
| NN Life | ESR 표 없음(後日公表予定) | 16 | 4/4 | not_yet 일치 |

핵심 검산: `esr = 適格資本/所要資本` 은 百万円 절사 때문에 **구간 검산**(au 점추정 792.31 ≠ 791.7, 구간 [791.64, 792.40] 안). `所要資本(税効果前) = A+B+C+D+E+F+G−H`
는 항별 절사로 au Δ2·MY Δ3. 리스크 부모 ≤ Σ하위(상관 통합, 등식 아님). `Tier1 基礎項目 == EBS 純資産`, `EBS 純資産 = 회계 純資産 + 規制上の準備金 + 経済価値調整額`
(au 9,776+2,222+1,882 / MY 23,367+15,389+3,362) 등 T2↔T4 교차 6건 전부 일치. MY 민감도 基準열 9행 = 헤드라인, 差額表 57/57.

**3축 실측.** au: 異常危険準備金 2,222(傷害 1,421·その他 800, 火災 없음) = EBS 規制上の準備金 2,222 정확 일치; 出再 5사·상위5 100%·A이상 80%; AIR 언급 0.
MY 별책: 3축 표 없음(본편 필요). NN Life: 基礎利益 18,523(전기 14,828)·逆ざや 37億円(전기 67, **단위 億円**)→ `interest_margin_sign=negative`, 三利源 분해 없음;
재보험 5사·상위5 100%·A이상 100%·未収再保険金 17,042; AIR 키워드 0 이나 정황 2건(基礎利益에서 제외한 既契約出再 손익 △3,733·관계사 共同保険式/最低保証再保険 각주)을
`air_evidence` 에 기록. ESR 빈 자리 3곳(p11 5개년 표 新基準 `-`(注2) / p15 健全性 box `別途公表予定` / p54 7절 문장만·표 없음) + 구기준도 FY2025 부터 중단(863.9→`-`).

**편차 요약.** ① 문서 배치: au 는 본편 業績データ 장 안(3축과 같은 파일), MY 는 ESR 전용 별책(3축은 본편 따로). ② au 는 (1) 결합표+(2) 요약 2번, MY 요약 1번;
`非保険事業 (i)` 행은 au 결합표에만. ③ 리스크 코드 (I)(J) vs (J)(K) — 라벨로 매칭. ④ au 는 EBS 빈 행 생략, MY 는 전 행 인쇄. ⑤ 민감도: au 값 생략(1%p 미만 주기),
MY 水準表+差額表. ⑥ 정성: au 문장식(내부모형 무언급→`standard_implied`), MY 항목식(該当なし→`standard`). ⑦ 할인율 연한 1/2/3년 vs 5/10/15/20년.
⑧ 단위는 둘 다 百万円, 세효과는 둘 다 세효과후를 (B)로 — 편차 없음(생보 逆ざや 만 億円). ⑨ 경과조치 표는 양식에 없음(두 표본 `経過措置` 0건, 문장 검색 플래그로만).
⑩ 생보/손보: 생보엔 이상위험준비금 없음(危険準備金·積立率), 손보엔 逆ざや·基礎利益 없음; 생보 T3 는 `生命保険リスク` 하위행이 생길 것(표본 없어 미등록, K-ICS 29~34 후보).

**한계.** MY 3축은 별책에 없어 본편 미열람(네트워크 불필요 조건이라 로컬 3건만). `calc_method` 의 `standard_implied` 는 추정(규제상 내부모형은 승인·공시 의무라
무언급=표준식으로 봄). C34(規制上の準備金 브리지)는 표본 2건 관측식이라 告示 정의 확인 전까지 ±2 허용.

## 종결 재확인 (orchestrator 2026-09-12)

스키마 131항목(esr 109 / article_axes 22), K-ICS 대응 32, 검산식 42 확인. 생성기 재실행 → 검산 전부 통과, 헤드라인 census 일치.
3 파일 BOM 없음. 표본값 JSON 은 `J-ESR/raw/`(gitignore) — 생성기로 재생성 가능하므로 커밋 대상 아님. 10월 census 티켓은
`J-ESR/esr_disclosure_schema.json` 의 id 를 열 이름으로 쓴다(도메인 문서 §3 포인터 확인).

status: **resolved**
