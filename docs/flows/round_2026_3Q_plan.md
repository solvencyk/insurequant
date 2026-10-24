# 2026.3Q 수집 계획 (홀수분기 라운드)

> 갱신 2026-10-24 · 근거: 지난 3번의 3분기(2023·2024·2025)와 2026.1Q 를 데이터셋별로 실측했다(7개 영역 조사 + 비평 1회; 비평이 사실과 다르다고 확인한 서술은 아래에서 고쳐 적었다).
> 실행 순서는 `docs/flows/kics_quarterly_round.md`(2Q 용, 3Q 는 라벨·스크립트 이름만 바꿔 쓴다) · 달력의 날짜는 모두 2026년이다.
> **owner 가 부르기 전에는 수집을 시작하지 않는다.** §8 의 「지금 해도 되는 준비」도 owner 승인 뒤에 한다. 이 문서는 계획이며 지금 아무것도 실행하지 않았다.
> **owner 결정 확정(2026-10-24, 다시 묻지 않는다):** ① DART 소스 묶음을 먼저 푸시하고 경영공시 묶음을 그다음에 푸시한다(§1-1). ② KIDI 는 늦게 올라오므로 기다리지 않는다(NB 배수는 KIDI 도착 뒤 3차 소배포). 각 단계의 main 배포는 그때 owner 구두 GO 로 한다.

## 1. 요약

- **3분기 경영공시 PDF 는 간이 양식이다.** 쪽수 중앙값이 2025.3Q 31쪽, 2Q 65쪽, 4Q 298쪽이다. 지급여력 헤드라인·요약 손익·재무제표는 있고, 반기·연 단위 표(금리민감도, 금리위험 시나리오, 유지율, 손해율 가정, 경영효율)는 없다.
- **소스는 세 갈래이고 도착 시각이 다르다.** DART 분기보고서 24사(11/13~11/16) · 정기경영공시 PDF 47사(마감 11/30 월요일, 조기 게시 11/26~) · 보험개발원 월납 202609(12월 초 이후 추정, 지연 가능).
- **회사마다 갈리는 것은 회사 집단이 아니라 「경과조치를 적용하는가」다.** 하위위험액(29-35)은 신규 보험위험 경과조치 적용사 20사가 의무(측정상 100% 공시), 시장위험 분해(36-40)는 주식·금리 경과조치 적용사 12사가 의무다. 그 밖에 자율로 인쇄하는 회사가 분기마다 바뀐다.
- **당기순이익은 47사 전부를 뽑는다.** 정본은 `PL_breakdown` 항목 24다. DART 24사는 분기보고서, 나머지 15사와 재보사 8곳은 경영공시 PDF §2-1 요약 포괄손익계산서(누계)에서 가져온다.
- **푸시는 소스별로 세 번에 나눈다**(owner 2026-10-24, §1-1). 그런데 분기 지평(게이트가 도는 분기 목록)이 5개 마스터(`PL_breakdown`·`CSM_waterfall`·`IFRS17_BS`·`kics_disclosure`·`dividend`)의 최댓값에서 자동 파생되므로, 1차 푸시에서 PL·CSM·BS·배당이 2026.3Q 를 담는 순간 아직 소스가 없는 칸(경영공시 15사·재보사 8곳 등)이 전부 hole RED 로 읽힌다. 그래서 1차 푸시 전에 validation 이 「대기 선언」(칸 단위·매 실행 재검산·2차 푸시에서 만료)을 설계해야 한다 — 티켓 `inbox/validation/20261024T0658Z…`. 선언 없이 푸시하지 않고, 지평 규칙을 완화하지 않는다.
- **사용자 사전 가설 확인:** 금리민감도는 「반기마다」가 아니라 「2024.4Q 이후 2Q·4Q 에만」(마스터 행: 2024.4Q·2025.2Q·2025.4Q·2026.2Q), 손해율 가정(표 A·B)은 반기도 아닌 「결산(4Q)에만」이 정확하다. 둘 다 3Q 제외가 맞다.

### 1-1. 푸시 분할 (owner 2026-10-24)

| 단계 | 들어가는 것 | 목표 시점 |
|---|---|---|
| **1차: DART 묶음** | PL 24사 전 항목 · CSM 워터폴 23사 · IFRS17_BS 24사 · dividend 24사 · 3Q 보고서의 전기 열로 고치는 **기존 분기 칸**(구 Wave A: 2025.3Q `null_dangi` 31칸·교보·푸본현대·전년동기 대조) | DART 접수(11/16) → 11/17 수집 → 11/19~20 FS-API·배당 refresh → **11/24 전후** |
| **2차: 경영공시 묶음** | K-ICS 전부(+판정 사이드카) · PL·BS 의 경영공시 15사 + 재보사 8곳 · 라이나 CSM·상각 · ILP 전부 · 자본증권 3종(발행·소진율·전망) · asset_quality·management_indicators · xlsx 시트·public_exports·패널 · 디자이너 라벨 | 11/30 마감 → **12/2~12/3** |
| **3차: KIDI** | NB 배수 분모와 `NB_TARGET_Q` | 보험개발원 202609 도착 뒤 별도 소배포 |

- ILP·자본증권은 DART 에서 오는 조각이 있어도 2차에 한꺼번에 넣는다(한 행·한 소진율을 두 번에 나눠 쓰지 않는다. 소진율 3종은 K-ICS 최신 분기와 같은 분기여야 게이트를 통과한다).
- 1차 푸시에는 NB 분모가 없어 `NB_CENSUS_MISSING` 이 CSM 3Q 칸 수만큼 난다 → 2Q 선례대로 건별 baseline YELLOW 등재(owner 결정 확정으로 본다).
- 1차 푸시의 main 배포는 owner GO 때 정한다. 배포하면 라이브에서 일부 회사만 3Q 인 상태가 되므로 designer 가 5개 페이지의 「전사 최신 분기」 처리(버블맵 ÷2 리터럴·IFRS17 3분기 누계 라벨·compare)를 먼저 확인한다. 이 확인은 아직 하지 않았다.

## 2. 달력

| 날짜 | 할 일 |
|---|---|
| 지금~11/13 | 준비(§8): 라운드 스크립트 3Q 복제·selftest, 메리츠 2026.2Q 정정, owner 결정 수신(§9), 기준선 게이트 1회. 10/31 안내 팝업 점등 → `tests/regression_*.py` 3종에 `iq_notice_seen=2026-3Q` 사전 주입 |
| 10월 말 | KB금융·NH금융 3Q 팩트북(IR) 게시(2025: 10/30·10/31) |
| 11/13(금) | 한화손보·한화생명이 하루 먼저 내는 편(2023~2025 매번). DART 1차 재스카우트 |
| 11/16(월) | **법정기한.** 분기말+45일 = 11/14(토)라 다음 영업일. 22사가 몰릴 것으로 본다(2024.1Q 는 휴일 5/15 대신 5/16 에 18사 선례). 팝업은 「11월 13일」로 적혀 있어 문구 확인 필요(§9 C8) |
| 11/17 | DART 본문 수집(2Q 때 `document.xml` 이 24시간 넘게 014 → 막히면 `fetch_dart_viewer_fallback.py`). 11/19~20 FS-API·배당 `--refresh` |
| **11/24 전후** | **1차 푸시(DART 묶음, §1-1).** 대기 선언(validation 티켓)이 먼저 끝나 있어야 한다. main 배포는 owner GO |
| 11/17~ | 게시 목록 census 주 1회, 11/24 부터 매일. 서울보증은 목록에 2026 3분기가 보이는 즉시 매일 |
| 11/26~28 | 경영공시 조기 게시(2025.3Q 는 46칸 중 37칸이 11/26~28) |
| **11/30(월)** | **마감.** 2Q(8/31 월)처럼 하루에 몰린다. census 10시·15시·19시 3회. 생보협회 일괄 zip 은 2Q 에 마감일 18:44 에 올라왔으므로 19시 이후에 본다 |
| 12/1(화) | 낙오사 1회 확인 · docling 변환과 K-ICS 채움 · 스캔본 렌더 판독 병렬 |
| 12/2(수) | validation RED=0(대기 선언이 비워져 있어야 함) → publishing(이상치 스캔·xlsx 시트 sync·public_exports·전체 게이트 약 11분) = **2차 푸시** |
| 12/2~12/3 | **배포 목표**(팝업 약속 「업로드 후 2~3일」). owner 구두 GO 뒤 `android_push_and_deploy.sh --from-origin` |
| 12/3 이후 | 보험개발원 202609 도착 시점은 미정(202606 은 월말 후 약 64일 ≈ 12/3 추정이나 늦을 수 있다) → 도착하면 **3차 소배포**로 NB 배수(`NB_TARGET_Q`)를 올린다. 기다리지 않는다 |
| 12/14~12/28 | 신판 재확인: sha256 으로 정정판 대조(KDB 2025.3Q·교보 2024.3Q·2025.3Q 전례), KB손보 텍스트판 교체 확인 |
| 12/31 | 안내 팝업 소등 |

## 3. 수집 매트릭스

### 3-A. 수집한다

| 데이터셋 | 대상 | 소스 | 3Q 기대치 · 비고 |
|---|---|---|---|
| K-ICS 1-28 적용전·적용후 | 46~47 버킷(서울보증·하노버 유무에 따라) | 경영공시 PDF | 헤드라인은 3Q 마다 전 버킷에 있었다(44/45/45). 1-5·7·9·11·13-22·27·28 빈칸은 결함(RED). 인쇄된 「-」는 0으로 적재(6·8·10·12·23-26). 27·28 은 `recalc_kics_derived.py` 로 산출. 경과조치 적용 19사는 `값`·`값_적용후` 둘 다 채우고 비적용사는 후=전 거울 |
| K-ICS 29-35 생명장기 하위위험 | 의무 20사: 한화손해·롯데손해·예별·흥국화재·NH농협손해·악사·ABL·흥국생명·KDB·교보·BNP·iM·DB생명·푸본현대·하나생명·처브·농협생명·플래닛·IBK연금·스코리. 자율 3사: 하나손해·메트라이프·뮌헨 | PDF 「② 표」 | **약 23사(21~25).** 2023.3Q 34 → 2024.3Q 25 → 2025.3Q 23 → 2026.1Q 23(항상 7항목 전부, 부분 공개 0). 의무 20사 공백은 RED. 상장 생보 4사(한화생명·삼성생명·미래에셋·동양)는 0이 정상 — 인쇄돼 있으면 원문 확인 |
| K-ICS 36-40 시장위험 분해 | 의무 12사: 예별·흥국화재·ABL·흥국생명·KDB·교보·iM·푸본현대·하나생명·농협생명·플래닛·IBK연금. 자율: 롯데손해·BNP·메트라이프·뮌헨(2026.1Q) | PDF 「③ 주식위험·금리위험 경과조치 표」 | **약 16~19사.** 31 → 21 → 19 → 16으로 줄고 있다. 한화손해·스코리는 2026.1Q 부터 인쇄 중단(2026.1Q p19 「적용하지 않아」 문장만) |
| K-ICS 47-54 (TFI 표·신종/후순위 메모 행) | 전사. 교보플래닛(TFI=X, 표 없음)·AIA(메모 행 없음)는 구조적 공백 | PDF | 47 비공백 42/43/42/45. 인쇄된 0 은 적재하고 정말 빈 칸만 사유를 적는다 |
| 적용후 거울(항목 4-13·24-26·53-54) | 전사 | 후처리 | 독립 추출 없음. 적재 후 `fill_post_transition_to_disclosure.py` 로 거울을 다시 채운다(2026.2Q 에서 10버킷이 빠진 원인 확인) |
| PL 항목 1·22·23·24(보험손익·세전·법인세·**당기순이익**) | **47사 전부** | DART 24사 = 분기보고서 FS-API/XML · 경영공시 15사 + 재보사 8곳 = PDF §2-1 | 지난 3Q 는 45~46/47이고 빈 칸은 전부 원문 부재(서울보증 2023·2024, 마이브라운 개업 전, 하노버 2025.3Q 미게시). **2026.3Q 목표 47/47.** 값은 1~9월 누계(백만원 = 억원×100), `값_당분기` = 3Q 누계 − 2Q 누계(같은 소스끼리만) |
| PL 항목 16·17·20·21 | 17·20·21: DART 24사 + 재보사 7~8곳. 경영공시 15사는 싣지 않음 | 위와 같음 | 경영공시 15사의 17·20·21 은 「투자수익−투자비용(감독회계)」이라 마스터(일반회계)와 개념이 달라 게이트가 막는다(`CONCEPT_REGISTRY`) |
| PL 항목 2-15·18·19·25-32(LOB·CSM상각·위험조정·예실차·OCI) | **DART 24사만** | 분기보고서 | 경영공시 15사·재보사는 3Q 뿐 아니라 4Q 에도 이 항목이 없다(§2-1 표에 줄 없음). 서울보증·NH농협손보·코리안리·미래에셋의 구조 공백은 정상 |
| IFRS17_BS 1-4·30·31 및 세부 | 전사 47. DART 24사 = FS-API OFS(별도), 15사·재보사 = 경영공시 8-1·요약 BS | | 목표 47/47. 정의가 다른 보류 칸(BNP 10·11·13·20·24, 악사 10·13·20·21·24)은 이번에도 보류. 재보사 세부 항목은 원천 부재 |
| CSM_waterfall 항목 1-6 | DART 분기 제출 23사 + 라이나(PDF 주석) = **24행** | 분기보고서 주석 / 라이나는 경영공시 PDF | 3Q 에 널 0(세 해 모두). 값은 9개월 누계, `값_당분기` 는 `build_csm()` 한 함수로 차분. 연 1회 공시 13사·재보사 7사·서울보증·신한이지는 3Q 행이 없는 것이 정상 |
| NB_CSM_multiple | 24행(코리안리 배수 null) | 분자 = 워터폴 항목 2, 분모 = KIDI 월납 초회 | 분자는 1차 푸시(CSM)와 함께 생기고 분모(202609)는 늦게 온다 → 3차 소배포. 그 사이 `NB_CENSUS_MISSING` 은 건별 baseline YELLOW(§1-1) |
| insurance_liability_portfolio 항목 1-9 | 전사 | 경영공시 4-6-2 | 처브(BS 상세 쪽 소실)·서울보증(4-6-2 인쇄 여부)·하노버(PDF 유무)를 먼저 확인 |
| insurance_liability_portfolio 항목 10-15 | DART 23사 + 라이나 | 분기보고서 주석 / 라이나 PDF | 연 1회 공시사의 10-15 는 4Q 전용 — 공란이 정상이다 |
| dividend | DART 24사(손보 9·생보 13·서울보증·코리안리) | `fetch_dart_alotmatter.py --refresh 2026 11014` | 현금배당액은 3Q 에 대부분 0, 중간배당(메리츠화재·KB손보 전례)과 순이익 누계 확보가 목적. 나머지 23사는 DART 배당 공시 자체가 없다 |
| 자본증권(발행 잔액·소진율 3종·전망) | 신규 2건: 하나생명 2026-09-15 1,500억(보완자본형), 교보생명 2026-09 3,000~5,000억 스텝업(금액 미확정). 3Q 콜 4건: NH농협손보 07-19·KB라이프 08-24·교보 09-10·흥국화재 09-29 | DART 주요사항보고서 + 분기보고서 주석 | 소진율 분자가 2026-06-30 기준인 회사가 25사, 2025-12-31 기준이 22사. 분모(SCR)만 3Q 로 올리면 라벨이 어긋난다 → §9 A5 |
| management_indicators 1-1·5-1 | 전사 | PDF | **내부 스테이징**(어떤 HTML·xlsx·훅에도 없음). 게시 마스터 뒤 순서. 순이익은 PL 항목 24 가 정본이므로 항목 4 보강(신한이지·AIA·AIG)은 필수 아님 |
| asset_quality 3-1·3-2 | 전사 | PDF | 내부 스테이징. 재보사 8사는 추출기 코호트(39사)에 한 번도 든 적 없음 → §9 B3. 스캔 3사 + KB손보는 `DOCUMENTED_EXCEPTIONS` 에 3Q 키 추가(예외 등재는 owner) |
| IR 팩트시트·덱 | 13소스(과거 3Q 보유 5~7개) | 각 사이트 | 안 올라온 곳은 `not_posted` 근거를 남긴다 |

### 3-B. owner 결정이 필요한 수집

| 데이터셋 | 쟁점 |
|---|---|
| CSM_amortization 3Q | **구조적 부재가 아니라 수집 정책이다.** DART 3Q 에 표가 있다(메리츠·삼성생명·흥국생명 확인). 분기 행은 라이나뿐. 받으려면 구간형 표를 경과차년 1~10 으로 환산하는 규칙과, 2025.4Q 에서 전기말 표를 물려받은 15사 결함 수정이 선행이다. 권고: 3Q 보류, 2026.4Q 에 같이 |
| 연 1회 공시 13사의 부분 워터폴 | PL 항목 4(CSM상각)가 3Q PDF 에 있는 회사가 있다(처브·뮌헨). 채우면 기초·상각·기말 3점 부분 행이 가능하다. 권고: 3Q 는 비움 |
| `data/ir/nb_csm_ratio.json` | 라이브(IFRS17.html)인데 2025년 IR 에서 멈췄고 아무도 갱신을 계획하지 않았다. 갱신/동결 결정 |
| 과거 구멍 2건 | 하나손해 2026.1Q 36-40(표가 쪽 경계에서 잘려 금리위험 한 행만 적재), AIG 2023.3Q 36-40(PDF 에 인쇄됨). 건별 셀 패치 후보. K-ICS.html 에 보이는 숫자가 바뀌면 owner 승인 |

### 3-C. 3Q 에 수집하지 않는다 (측정 근거)

| 데이터셋 | 근거 |
|---|---|
| 금리민감도(`kics_rate_sensitivity`) | 마스터 행은 2024.4Q 186·2025.2Q 240·2025.4Q 264·2026.2Q 276뿐, 홀수분기 0. PDF 「금리민감도분석」 보유: 2Q/4Q 43~45/46~47사, 홀수분기 0/45~48. 게이트 RS5 도 홀수분기를 요구하지 않는다. 자율 공시하는 회사가 있어도 owner 지시 없이 적재하지 않는다(RS4 가 그 회사의 홀수분기 기대를 만든다) |
| 금리듀레이션갭·K-ICS 41-46(시나리오 순자산) | 홀수분기 315 버킷 전부 0칸. PDF 쪽 단위 스캔(시나리오 라벨 4개 이상) 0/45~48. 마스터는 짝수분기 7개뿐 |
| 유지율(7-6) | 마스터 짝수분기 7개뿐, 3Q PDF 보유 0 |
| 손해율 가정 표 A·B·C | 표 A·B 는 결산(4Q)에만(2023.4Q·2024.4Q·2025.4Q), 표 C(합산비율)는 2Q/4Q. 3Q PDF 보유 0 |
| CSM 가정 민감도 | 사업보고서 주석(4Q)에만. 반기 24사 전수에서도 0건 |
| 경영효율 지표 11-21 | 짝수분기에만. 홀수분기 PDF 보유 0~2/45 |
| 레거시 viz(`net_income_breakdown`·`downstream_kpis`·`csm_bubble`·`bs_snapshot`·`earnings_quadrant`) | 5개 페이지 어디서도 fetch 하지 않는다 |
| 캐롯손해보험 KR1059 | 한화손보 합병(skipped). 세 마스터에 행이 남아 있으나 분모는 47 로 잡는다 |

## 4. 회사 집단과 소스

| 집단 | 회사 | 소스 · 주의 |
|---|---|---|
| DART 분기보고서 24사 | 손보 11(KR0001·0002·0003·0005·0008·0009·0010·0011·0032·0150·1000) + 생보 13(KR0068·0069·0070·0071·0072·0073·0079·0082·0083·0087·0094·0099·0104) | 접수일 2023 전부 11/14 · 2024 11/13~14 · 2025 11/13~14. 서울보증은 2025.3Q 부터. 2025.3Q raw 는 24사 전부 디스크에 있다(10사는 `xml/` 하위 폴더 배치) |
| 경영공시만 내는 국내 15사 | KR0004·0029·0049·0050·0051·0074·0075·0076·0080·0095·0097·0100·1010·1011·1098 | DART 3Q 를 기다리지 않는다(비상장 1~3Q 구조적 미제출). 라이나는 PDF 에 분기 CSM 주석이 있어 CSM 24행에 든다 |
| 재보사 8곳 | KR1101~1108 | **수집 스크립트가 저장소에 한 번도 커밋된 적이 없다**(10월 수집은 세션 임시 스크립트). 스위스리(Cloudflare)·하노버(403)·퍼시픽라이프리(Incapsula)·마이브라운(JS 셸) 4곳은 owner 브라우저 수령 이력. 하노버는 늘 지각하고 2025.3Q 는 아예 미게시 |
| 서울보증 KR0150 | | DART(PL·BS·배당) + sgic.co.kr PDF(K-ICS·자산건전성). **사이트가 최신 분기만 두고 이전 분기를 내린다** — 게시 당일 받고 sha256 기록. 2025.3Q 까지의 NO_RAW_PDF 최종 판정은 2026.3Q 에 적용하지 않는다 |
| 스캔(이미지) PDF | KB손보 KR0010(1Q·3Q 스캔, 2Q 는 텍스트판 `_v20261011` 로 교체됨) · 미래에셋 KR0079(전 분기) · 동양 KR0087(2026.1Q 부터) · AIA KR0080(경계) · 카카오페이 KR1098(2024.3Q 전례) | 키워드 0회를 「원천 없음」으로 단정하지 않는다. 240dpi 렌더링으로 읽는다(`render_kics_page.py`). 이 사들이 12/1~12/2 일정의 가장 긴 가닥이다 |
| 장문판을 내는 3사 | 한화손보 KR0002(240~263쪽) · 흥국화재 KR0005(136쪽) · 라이나 KR0074(165쪽) | docling 변환 시간을 따로 잡는다. 동시 docling ≤2 |

## 5. 단계별 할 일

**downloader**
- 3Q 복제본 신규: `download_disclosure_2026q3_{nonlife,life,life_sites}.py` · `download_ir_2026q3.py` · `scout_2026q3_quarter.py` · `_probes/census_q3_{disclosure_listings,life_own_sites}.py` · `_probes/verify_q3_disclosure_content.py`. 기간 상수(`OUT_DIR`·`META_DIR`·`PERIODS`)와 2Q 전용 정규식(2분기·상반기·6월 30일)을 바꾼다.
- **위치로 고르는 셀렉터**(KR0001 첫 행, KR0010 `tr[3]`)는 라벨 앵커로 바꾸고 `period_include/exclude_regex` 를 17사 전원에 건다(2Q 에서 12사가 1Q 파일을 다시 받아 ok 로 보고한 전례).
- **검증 프로브 함정:** `verify_q2_disclosure_content.py` 는 존재하지 않는 `FY2026_Q2/pdf` 를 읽어 「nothing to verify」로 exit 0 한다. 3Q 복제본은 `raw/` 로 읽고 쓰며 대상 0건이면 exit 2 로 실패하게 한다. 텍스트 200자 미만은 reject 가 아니라 「렌더링 확인 필요」로 분리한다. 3Q 양성: 3분기·3/4분기·3Q·1~9월·2026.09.30, 음성: 1분기·상반기·2026.06.30·결산. `공시 예정임` 문구 스캔을 4번째 검사로 넣는다.
- 3Q 라벨은 회사마다 다르다(AIA 「3분기 결산」, 미래에셋 「3/4 분기」, 삼성생명 「회계연도(3분기)」, 신한라이프 날짜 범위). 한화생명·동양·교보생명·ABL·한화손보는 3Q 라벨 형태를 아직 모른다 → 11월 첫 census 에서 기록한다.
- 생보협회 그리드 census 는 `headers.index('3분기')` 열과 기준년 select 가 2026 인지 같이 본다. `extract_life_bulk_zip.py` 는 `pdf/` 에 쓰므로 `raw/` 로 옮긴다.
- 쪽수 수락 기준: 3Q 는 15쪽 미만이면 의심(2Q 의 60쪽 기준을 쓰지 않는다).
- DART: 11/13·11/16 두 번 재스카우트, 014 정체 시 viewer fallback, 접수 직후 `fetch_dart_alotmatter.py --refresh 2026 11014` 와 `fetch_dart_fs.py --refresh`, `check_dart_raw_coverage.py --update`. 기존 013 파일은 skip 되므로 refresh 가 필수다. 연 1회 공시사에 `meta.json` 의 `no_filing` 표지를 정확히 남긴다(BS 이월 면제 게이트가 읽는다).
- `report_collection_status.py` 는 `PERIOD_TO_YYYYMM` 에 FY2026_Q2·Q3 가 없고 KIDI 열이 `FY2026_Q1` 문자열로 박혀 있으며 자본증권 열이 폐지된 소스를 본다 → 상수를 고친 뒤 FY2026_Q3 로 돌린다.
- KIDI: `ingest_kidi_monthly_premium.py` 의 `DEFAULT_PERIODS` 에 202609 추가. 11/16 부터 주 1회 LastYM 만 읽고(미게시 월은 0 껍데기가 온다), 11/30 라운드를 KIDI 때문에 막지 않는다.

**parser-kics**
- 순서: `build_kics_source_textlayer.py` → `extract_transition_applicability.py`(판정 사이드카 2종을 먼저 갱신해야 최신 분기 강제 RED 를 피한다; UNKNOWN 은 X 가 아니다) → `run_harness.py --stage parse --period FY2026_Q3 --pdf-root data/disclosure/FY2026_Q3/raw`(인자 없는 명령은 `pdf/` 를 찾아 실패) → `fill_period`·`fill_subitems`·`fill_market_subitems`·`fill_post_transition` → `recalc_kics_derived.py`. 맨 `python` 금지, venv 풀패스.
- 29-35·36-40 은 **회사 분류가 아니라 PDF 쪽 단위**로 판정한다(하위위험 라벨 5개 이상, 시장위험 라벨 4개 이상). 파싱된 MD 가 47개인지 게이트 전에 센다(MD 가 없으면 홀수분기 시장위험 검사가 SKIP 으로 조용히 꺼진다).
- 스캔본(KB손보·미래에셋·동양·AIA): `ocr_parse_scanned_disclosure.py` → 렌더 판독 → 항등식(MARKET_M·rule 5)으로 교차 확인. OCR 텍스트는 단서일 뿐이다.
- 재보사는 `latest_disclosure_pdfs()` 로 최신 판만 쓴다. 퍼시픽(KR1107)의 영점 자리표시 표(p23-24)는 적재하지 않는다(`MARKET_BREAKDOWN_EXEMPT`).
- 적재 직후 `detect_kics_restatement.py --period FY2026_Q3 --prior FY2026_Q2`(기본값이 2Q 라 인자 필수) — 3Q 문서는 직전분기 열에 2026.2Q 를 다시 인쇄한다. **먼저 메리츠화재 2026.2Q 항목 2·3·28 적용후 정정**(오늘 마스터 확인: 52538/52538, 92894/92894, 83.25; 원문은 기본자본 54,329.57억·보완자본 91,102.49억; 티켓 `20260919T1400Z`)을 끝내야 소급재작성으로 오인하지 않는다.
- 적재 후 PDF 라벨 밀도 스캔을 (회사, 홀수분기) 전수에 돈다: 항목 19 가 있는데 36-40 이 빈 칸인 곳(현 게이트가 못 잡는 사각 — 하나손해 2026.1Q 가 이렇게 샜다). 측정 스크립트는 세션 임시 파일이라 저장소에 없다. 도입하려면 `scripts/` 에 새로 만든다.
- 자본증권: `fetch_capital_securities_dart.py`(FILINGS 가 3개사 rcept 하드코딩 → 확장) → `build_capital_securities_fy2026h1.py` 의 3Q판(RAW_DIR·출력명 고정) → `wire_capital_securities_to_utilization.py --quarter 2026.3Q` → `apply_disclosure_utilization.py` → `build_capital_securities_timeline.py` → `forward_capital_simulation.py --baseline-quarter 2026.3Q` → `add_reinsurers_to_capsec_panels.py --apply`(빌더가 재보사 8레코드를 지운다; 이 스크립트의 `QUARTER`·`AS_OF` 리터럴 2개도 바꾼다) → `emit_capsec_provenance.py`. 기본 인자가 낡은 스크립트가 많으니 전부 명시한다.

**parser-ifrs17**
- **1차 푸시(DART 묶음, 11/24 전후):** (a) 기존 분기 칸: 3Q 보고서의 전기 열로 `null_dangi` 2025.3Q 31칸(8사: 한화생명·삼성생명·ABL·흥국생명·교보·동양·신한라이프·농협생명)을 해제/고정하고, 교보 PL·CSM 2025.3Q 재갱신과 푸본현대 2025.3Q 26칸을 처리한다. 24사 전년동기 6항목을 칸 단위로 대조해 어긋나면 최신 비교열로 올린다(재작성 전례: 교보·KB라이프·ABL·롯데·푸본현대·미래에셋을 먼저). (b) 2026.3Q 신규 행: CSM(DART 23사, `build_csm()` 만; `build_root_masters.main()` 금지) · PL(DART 24사 FS-API/XML) · IFRS17_BS(24사, `build_ifrs17_bs.py`) · dividend(`build_dividend.py` 는 refresh 뒤). 대기 선언(validation 티켓)이 끝난 뒤에만 푸시한다. 라이나(PDF)·15사·재보사는 이 푸시에 넣지 않는다.
- **2차 푸시(경영공시 묶음, 12/2):** PL·BS 의 경영공시 15사 + 재보사 §2-1 · 라이나 CSM·상각 · ILP 전부(`load_ilp_*.py`; 항목 15 == IFRS17_BS 항목 20 검산) · NB 분자(1차에 이미 CSM 이 있으므로 분자 갱신분만) · 대기 선언을 모두 비운다.
- 적재 직후 점검: 2026.3Q 기초 누계 == 2026.2Q 기초 누계, 3Q 당분기 기초 == 2Q 기말, 6개월 누계가 재작성된 회사는 `null_dangi` 에 등재해 그 단일분기를 비운다. 누계가 줄거나 부호가 뒤집힌 순이익 칸은 필링의 3개월 열과 대조한다(지난 3Q 에 11건 있었고 전부 원문 확인 전).
- 분기마다 사람 손이 필요한 gold 칸을 먼저 점검: KB손보 항목 16(`_zero_other_expense` 가 매 분기 0 으로 덮음), ABL 항목 5·10·7·12, 흥국화재 CSM 3-7.
- 경영공시 PL 백필 도구가 삭제됐다(§7). 복구 또는 새 병합기 1회 작성.

**validation**
- **선행 과제(1차 푸시 전):** 「대기 선언」 설계(티켓 `20261024T0658Z`; 새 게이트 룰 설계라 Opus 대상). 먼저 1차 푸시 상태를 모의로 만들어 어떤 게이트가 무엇을 RED 로 내는지 측정하고(추정: PL·BS `MASTER_HOLE` 약 22~23사, CSM 라이나 1사, `NB_CENSUS_MISSING` 24건), 칸 단위·매 실행 재검산(raw 가 아직 없을 때만 인정)·2차 푸시에서 만료하는 선언을 만든다. 지평 규칙은 완화하지 않는다.
- 기준선 먼저(11/6): 전체 게이트 1회 — data_contract RED=0·YELLOW 168, K-ICS blocking 0 기록.
- 3Q 에 요구하지 않는 것(RS5·듀레이션갭·36_irr)이 RED 로 안 나오는지 확인. 새 게이트는 만들지 않는다(§9 D6 제외).
- 적재 후: `validate_kics_disclosure.py`·`validate_data_contract.py`·`validate_master_tables.py --no-build`·`validate_golden_input_fingerprints.py` · 훅에 안 걸린 4종(`validate_asset_quality`·`validate_management_indicators`·`validate_insurance_liability_portfolio`·`validate_insurance_liability_lic`)을 손으로 돌려 RED 확인. `validate_disclosure_freshness` 는 `FY2026_Q3` 폴더가 비면 GREEN 0건으로 통과하므로 **GREEN 47건인지 개수까지** 본다.
- 8_life_census YELLOW(UNKNOWN) 반복 사: KB손보·삼성생명·미래에셋·KB라이프·AIA·동양·한화생명·신한라이프·카카오페이 — 원문 쪽으로 ② 표 유무를 확인해 YELLOW 를 닫는다(`table_absent` 등재는 owner).
- 단일분기 항등식 게이트는 3Q 푸시 전에 켜지 않는다(켜면 RED 94). 대신 2026.3Q 단일분기 칸만 그림자 census 로 새 이음매를 선별한다.
- 골든은 RED=0 확인 뒤에만 `--update`(RED 가 박제된다). 박제 숫자 갱신은 해당 데이터 커밋과 같은 커밋에서: `tests/test_rule_coverage_manifest.py` 의 `GOLD_OVERLAY_CENSUS`·`KICS_RESTATEMENT_CENSUS`·`CENSUS_SOURCE_ABSENT_CENSUS`·xlsx 시트 수.

**publishing**
- 순서(두 번의 푸시마다 반복; 1차에는 17BS·CSM워터폴·손익분해PL·배당·신계약CSM배수 시트만, 2차에 나머지): 마스터 커밋 → 바뀐 시트만 `sync_master_xlsx_sheet.py "<시트>" --dry-run` 후 실행(K-ICS공시·17BS·CSM워터폴·손익분해PL·배당·신계약CSM배수·기본/보완자본소진율·자본성증권발행현황·자본비율전망·보험계약부채) → `check_master_xlsx_drift.py` → `export_public_sheets.py`(커밋된 HEAD 를 읽는다) → 재커밋 → 패널 재빌드(`viz_build_compare_panel.py` 는 모든 마스터가 3Q 로 채워진 뒤 한 번).
- 첫 푸시 전 `scan_generic_anomalies.py`(+skeptic) 1회. provenance 사이드카(`emit_kics_provenance.py`·`emit_ifrs17_provenance.py`·`emit_pl_provenance.py`·`emit_ilp_includes_lic.py`·`emit_capsec_provenance.py`)의 재발행 대상을 `validate_data_contract.py` 의 `MISSING_PROVENANCE` 검사 범위를 읽어 확정한다(PL 의 경영공시 23사 셀은 계보 `DISCLOSURE` 를 같이 발행하지 않으면 DART 용 엄격 그리드로 떨어져 HOLE RED).
- 모든 커밋은 `git add -A` 금지·파일 명시, 커밋 전 `branch --show-current`·`diff --cached --stat`(루트 미추적 개인 문서·연락망 보호).

**designer**
- **1차 푸시를 배포하기 전:** 일부 회사만 3Q 인 라이브 상태에서 5개 페이지의 「전사 최신 분기」 처리(버블맵 스케일·IFRS17 3분기 누계 라벨·공시보고서·compare)를 렌더로 확인한다(`viz_build_compare_panel.py` 의 `LAST_Q` 는 K-ICS 마지막 분기라 1차에는 2Q 로 남는다는 점도 확인). 아직 측정하지 않았다.
- `index.html` 버블맵의 연 1회 공시사 추정 스케일: 전사 최신이 3Q(9개월 누계)가 되면 12개월 값을 ÷2 가 아니라 ×0.75 로 맞춰야 한다. 리터럴이 L199·L1178·L1313·L1362 네 곳이고 분기 번호(qn/4)에서 배율을 파생하도록 고친다(2Q 에서 같은 리터럴이 오표시된 전례 2026-09-02). 고친 뒤 `÷2` 를 파일 전체에서 grep.
- `report-widget.js` `QUARTERS` 에 2026.3Q 추가(12/2 묶음) · `index.html` `NB_TARGET_Q` 는 NB 에 2026.3Q 행이 생길 때까지 2026.2Q 유지(회사별 이월 폴백이 추정 표시) · `theme.js` `NOTICE` 문구 · `viz_build_csm_combo_panel.py` 의 `PENDING_NAMES`(하나생명 2026.2Q) 해소 여부.
- `tests/regression_*.py` 3종과 `scripts/check_report_widget_internal.py` 의 2026.1Q 단언을 최신 분기 파생으로 바꾼다. `sitemap.xml` `lastmod` 는 이미 낡았으니 실제로 바뀐 페이지만 배포일로 갱신한다.
- 유지율·손해율의 3Q 칸이 비어도 비교 화면이 정상인지 확인(의도된 공란; 「반기/연 1회 공시」 안내 문구를 둘지 owner 결정).

## 6. 신분기 점검표 (코드가 손으로 고쳐야 하는 곳 · 푸시가 막히는 조건)

- **자동 파생이라 고칠 필요 없는 곳:** `_quarter_horizon.py`·`validate_disclosure_freshness`·`validate_stale_quarter_tables`·`status_report`·`check_dart_raw_coverage`·5개 HTML 의 최신 분기 표시(IFRS17 3분기 누계 라벨·공시보고서 「2026.3Q누계」·compare ROE 연환산 ×4/3은 이미 코드에 있다).
- **기본값이 낡아 인자를 항상 명시:** `run_harness.py`(FY2025_Q4) · `fill_tfi_table_to_disclosure.py`(FY2026_Q2) · `detect_kics_restatement.py`(FY2026_Q2/Q1) · `extract_asset_quality.py`(FY2026_Q2) · `wire_capital_securities_to_utilization.py`·`forward_capital_simulation.py`(2026.1Q) · `apply_disclosure_utilization.py`·`build_capital_securities_recognition.py`(2026.2Q). 인자 없이 돌리면 이전 분기를 조용히 다시 처리하고 게이트는 구분하지 못한다.
- **리터럴 수정:** `extract_pl_backfill_disclosure.py` `QUARTERS_NON4Q`(2026.2Q 에서 끝남, 재보사 없음, 출력 경로가 기존 근거 파일을 덮음) · `extract_insurance_liability_lic.py`(`FY_DIRS`·`QMAP`) · `emit_ilp_includes_lic.py`(`QUARTERS`) · `ifrs17_batch_historical.py`(표가 2026.1Q 에서 끝남 → 2Q 처럼 로컬 PeriodTarget 스크립트 복제) · `tests/test_disclosure_selector_hardcoding.py`(ENGINE 이 `download_disclosure_2026q2_nonlife.py` 로 고정 → 3Q 복제본이 무방비로 남지 않게 옮김).
- **짝수분기 전용이라 3Q 에 건드리지 않는 곳:** `build_kics_duration_gap.py` · `extract_kics_irr_balance.py` · `extract_persistency_channel.py` · `extract_loss_ratio.py`(`QUARTERS` 가 `[:14]` 로 2026.2Q 에서 잘림 — 2026.4Q 부터 늘려야 함).
- **3Q 적재 직후 첫 푸시에서 깨지는 것:** `test_kics_rules_golden`·`test_master_tables_golden`(라이브 마스터 해시 박제) · 골든 입력 지문 6종 · 자본증권 3종과 사이드카 2종의 「최신 분기 강제」(`STALE_AS_OF`·`SIDECAR_STALE_LATEST_QUARTER`, 모두 RED) · `NB_CENSUS_MISSING`(NB 에 3Q 행이 없고 워터폴에 있으면 24건 RED) · `MASTER_XLSX_ROW_MISSING`·`PUBLIC_EXPORT_MISSING_CELL`.
- **서울보증 K-ICS census 뒤집힘:** 정규 공시사 문턱이 7분기(`max(2, 분기수//2)`)이고 서울보증은 6분기라 지금은 점검 밖이다. 2026.3Q 를 적재하면 7분기가 되어 2025.2Q·2025.3Q 2칸(표시 범위 밖 옛 분기 6칸 포함 시 8칸)이 `MISSING_FILER_CELL` RED 가 된다(합성 모의 실행으로 확인). 이전 분기는 사이트에서 내려가 재수집이 불가하다 → §9 A1.
- **PL 계보:** 경영공시 계보 23사(예별·AIG·악사·하나손보·신한EZ·라이나·BNP·iM·AIA·메트라이프·하나생명·처브·플래닛·IBK·카카오페이 + 재보사 8)는 `PL_breakdown_provenance.json` 에 `income_statement` 블록 `DISCLOSURE` 계보를 같이 발행해야 한다. 마이브라운 KR1108 은 PL 5분기 + 3Q = 6분기이고 2026.4Q 에 7분기가 되면 2024.1Q~2025.1Q 5칸이 실제 HOLE 이 되므로 4Q 전에 원천부재 등재 여부를 정한다.
- **BS 이월 면제:** 연 1회 공시사의 3Q BS 이월은 `data/dart/FY2026_Q3/raw/<코드>_*/meta.json` 이 `no_filing` 이거나 폴더가 없을 때만 인정된다.

## 7. 삭제된 스크립트 중 3Q 에 필요할 수 있는 것

2026-10-24 정리 커밋 `b4a04580` 에서 지워졌다. 복구: `git show b4a04580^:<경로>` 를 3Q 이름의 새 파일로 저장하고 상수(행 수 가드 등)를 현재 값(PL 13,801행)에 맞춘다.

| 필요한 때 | 파일 |
|---|---|
| 라이나 3Q CSM·상각 적재 | `scripts/_lina_csm_ext_20261011.py` · `_lina_csm_tables_20261011.py` · `extract_lina_csm_rows_20261011.py` · `fill_lina_csm_dangi_20261011.py` · `load_lina_csm_backfill_20261011.py` (상각 분할표까지 읽으면 `extract_amort_split_tables_20261012.py` · `load_amort_split_tables_20261012.py`) |
| 경영공시 PL 병합·재보사 적재 | `scripts/merge_pl_backfill_disclosure_20261008.py`(또는 `_20260920.py`) · `reinsurer_resweep_pl_apply.py` · `reinsurer_resweep_pl_followup.py`. `extract_pl_g5_disclosure_20261008.py` 는 2023.1Q·2Q 전용이라 불필요 |
| 재보사 BS 셀 단위 UPSERT | `reinsurer_resweep_bs_apply.py` · `reinsurer_resweep_bs_overlay.py` |
| gold 마스크 칸 박제 | `scripts/_probes/seed_20260830_gold_overlay_ledger.py` · `probe_20260829_trace_builder_reads.py` |
| 단일분기 마감 census(그림자 점검) | `data/_derived/kyobo_validation_20261022/census_quarterly_closure.py` |
| 자본증권 분류 census | `data/_derived/capital_securities_classification_census_20261012/` |
| 유지됨(복구 불필요) | `scripts/_probes/{census_q2_disclosure_listings,census_q2_life_own_sites,verify_q2_disclosure_content,render_kics_page,render_kics_pages}.py` · `fix_20260829_kr0050_2026q2_onboarding.py` · `merge_bs_disclosure_parts.py` · `extract_bs_from_disclosure.py` · `load_ilp_*.py` |

## 8. 지금 해도 되는 준비 (owner 승인 뒤)

수집 라운드 자체는 owner 호출 전에 시작하지 않는다. 아래는 복제·읽기 전용·건조 실행이다.

1. 3Q 스크립트 복제와 selftest(지난해 3Q 라벨 문자열을 양성 코퍼스로 써서 `FY2026_Q2/_meta/*_listing_labels.txt` 에 새 정규식을 돌린다).
2. 메리츠화재 KR0001 2026.2Q 적용후 항목 2·3·28 정정 발주(parser-kics 티켓 `20260919T1400Z`).
3. `CORPCODE.xml`(2026-06-14, 132일 경과) 갱신과 24사 canonical 이름 대조. 2026 `11014` 013 캐시 89파일(FS 50 + 배당 39)은 3Q 데이터가 나온 뒤 refresh 전까지 「없음」으로 서빙된다.
4. `fetch_dart_viewer_fallback.py` 를 2Q 접수 1건으로 읽기 전용 건조 시험.
5. 47개 호스트 도달성 확인 `curl --ssl-no-revoke -m 30`(막히면 재시도 루프 없이 기록하고 보고).
6. OpenDART `list.json` 읽기 전용 호출로 2026.1Q 접수 18건(마감일 5/15 가 아닌 5/29 16건 등)의 `report_nm` 확인 — 3Q 선택 로직이 정정본을 잡을 수 있는지.
7. 재보사 수집기 `download_disclosure_2026q3_reinsurers.py` 신규 작성(registry 의 URL 패턴, 상태 `ok/not_posted/blocked/unverified`).
8. KB금융·NH금융 3Q 팩트북 사전 수집(이번 주 게시 가능; 「owner 호출 전 시작 금지」 규칙과의 관계는 §9 C3).
9. 기준선 전체 게이트 1회(약 11분)와 `build_kics_source_textlayer.py` 가 최신 `_v` 파일을 우선 읽도록 고칠지 결정(KB손보 2026.2Q 는 텍스트판이 이미 있는데 사이드카는 UNREADABLE 로 남아 있다).

## 9. owner 결정 대기

**A. 3Q 푸시를 막는 것(1차 푸시 11/24 전후 이전에). A2·A4 는 2026-10-24 owner 결정으로 확정**
1. 서울보증 K-ICS 3Q 적재 전에 빈 분기 8칸을 (a) 「사이트 철거」 원천부재로 등재(종류 신설 + raw 박제 근거 원장 필요; `tests/test_rule_coverage_manifest.py` 의 `CENSUS_SOURCE_ABSENT_CENSUS` 도 같이) 할지 (b) 정규 공시사 규칙을 바꿀지. 권고 (a) — 문턱을 건드리면 다른 회사의 검사가 약해진다.
2. **[확정] DART 묶음 먼저, 경영공시 묶음 그다음**(§1-1). 이전 권고(한 번에 푸시)는 폐기. 대신 validation 이 「대기 선언」을 설계한다(티켓 `20261024T0658Z`).
3. 하노버 2026.3Q 가 11/30 까지 안 올라오면: 기다릴지, 면제 등재(owner 전용)를 요청할지. 권고: 12/1 에 목록 스냅샷을 근거로 면제 요청, 기다리지 않는다.
4. **[확정]** NB 배수: KIDI 는 늦게 올라오므로 기다리지 않는다 = (b) 2Q 처럼 `NB_CENSUS_MISSING` 건별 YELLOW 등재 후 푸시, `NB_TARGET_Q` 는 2026.2Q 유지, 202609 도착 뒤 3차 소배포.
5. 자본증권 3종: 분자 기준일이 직전 분기인 채 분모만 2026.3Q 로 올리는 것(YELLOW 표시) 허용 여부. 권고 허용 + 라벨 정직 표시.

**B. 수집 범위**
1. §3-B 의 CSM_amortization 3Q · 부분 워터폴 · `nb_csm_ratio.json` · 과거 구멍 2건.
2. 순이익 정본 = `PL_breakdown` 항목 24 로 확정하고 `management_indicators` 항목 4 보강(신한이지·AIA·AIG 이미지 판독)은 필수에서 뺄지. 두 마스터를 게시 마스터 뒤 순서로 미루고 캐롯 행을 정리할지.
3. 재보사 8사를 `asset_quality` 에 편입할지(편입한다면 3Q 부터만인지 2025.4Q 편입 시점까지 소급인지).
4. 스캔 PDF 4~5사의 렌더 판독을 매 홀수분기에 할지(권고) 아니면 29-40·53-54 를 영구 YELLOW 로 둘지. 판독 불가 셀의 「미공시」 단정 금지.
5. 자율 공시 회사의 29-35·36-40 은 인쇄돼 있으면 적재(권고; 항등식 19_market·8_life 가 닫힌다). 과거의 인쇄된 「-」 빈칸(한화손해 23-26, AIA 항목 8 등)은 0 으로 소급할지.
6. IR 13소스 전부 vs 과거 3Q 보유 6개(현대·DB손보·한화생명·미래에셋·KB그룹·NH그룹).
7. 교보 신종 스텝업·하나생명 1,500억의 tier 분류 근거(원문)와 `step_up` 플래그 작업을 3Q 전에 착수할지.

**C. 준비 작업 승인**
1. 라운드 스크립트 복제와 `report_collection_status.py` 상수 수정(`_probes` 복제 포함).
2. 재보사 수집기 신규 작성 + 스위스리·하노버·퍼시픽·마이브라운 4곳을 11/30~12/1 에 owner 가 브라우저로 받거나 브라우저 탭 사용을 허락.
3. KB금융·NH금융 팩트북 사전 수집과 스크립트 건조 실행을 「owner 호출 전 시작 금지」 규칙의 예외로 볼지.
4. `CORPCODE.xml` 갱신과 013 캐시 refresh 계획.
5. OpenDART `list.json` 읽기 전용 호출.
6. 메리츠화재 정정 발주.
7. 판정 사이드카 생성기가 최신 `_v` 파일을 우선 읽게 고치기.
8. 안내 팝업의 「DART 공시 기한 11월 13일」을 「11/13~11/16」으로 바꿀지(11/14 는 토요일).
9. `report_collection_status.py` 의 자본증권 열을 N/A 로 둘지 DART 채권 기준으로 다시 정의할지.

**D. 이월된 결정(3Q 적재는 막지 않지만 12/1 파싱 전에 정하면 이중 작업이 없다)**
1. KDB생명 재적재 A/B/C(`TODO.md` 「owner 결정 대기」 ①) — KDB 2026.3Q PL 6항목이 같은 기준 혼합 위험을 갖는다.
2. 동양 재보험 항목 9·10 부호 규약(미루면 2026 칸까지 다시 뒤집어야 한다).
3. KB손보 항목 16(박제 6건 / `_zero_other_expense` 변경 / 분기마다 수동 gold)·흥국화재 항목 16 박제 2건.
4. KB라이프 2024.1Q~3Q CSM 연쇄 면제(승인하면 11월 초 별도 푸시로 끝내 3Q 기준선을 RED=0 으로 유지).
5. 소급재작성 장부 `_policy` 기본값을 「최신 공시 채택」으로 전환할지 · 자본증권 공개본 `비고`·`출처` 열 제거 여부.
6. 단일분기 항등식 게이트는 3Q 푸시 이후로 미루고 그 사이 그림자 점검만 할지.
7. K-ICS·IFRS17 규정 개정이나 경과조치 단계 변경 중 시행일이 2026.3Q 부근인 것이 있는지 — 저장소 전수 검색에 기록이 없어 확인할 수 없다. 경과조치 적용 19사 집합은 14분기 내내 같았고 감소폭도 21.8~24.8%로 3Q 전용 단절이 없다.

## 10. 위험

- 마감일(11/30 월) 하루에 47칸의 절반 이상이 몰린다(2Q: 8/31 에 25칸). 전체 게이트 11분 + 스캔본 판독이 12/2 목표의 임계 경로다. 푸시를 두 번 이상 하게 되면 시간이 모자란다.
- 같은 날 협회 zip 은 저녁에 올라온다 → census 를 시간대별로 나눠 돌리지 않으면 22사를 미게시로 잘못 판정한다. `unreachable` 은 미게시가 아니다.
- 위치 기반 셀렉터가 새 분기 전에 직전 분기를 조용히 다시 받는다 → 라벨 앵커 + period 가드 + 내용검증(`GREEN 47건`).
- 첫 수집 뒤 K-ICS 수치가 바뀐 정정판 전례(KDB 2025.3Q, 교보 2024.3Q·2025.3Q) → 12/14~12/28 재확인을 일정에서 빼지 않는다.
- 3Q 단일분기(9개월 누계 − 6개월 누계)는 어떤 게이트도 검산하지 않는다. 6개월 누계가 3Q 필링에서 재작성되면 틀린 값이 조용히 들어간다 → `null_dangi`(빈 칸이 틀린 값보다 낫다, owner 2026-10-22).
- 골든을 RED 가 남은 채 `--update` 하면 RED 가 박제된다. 서브에이전트 프롬프트에 「python 은 스크립트 파일로만, stdin·heredoc 금지」를 다시 명시한다(이번 조사에서도 에이전트 3곳이 위반했다).
- TODO 가 인용하는 증거 경로 약 20개가 `b4a04580` 에서 삭제됐다(`remaining_20261022` 하위 등) — 근거를 열 때 먼저 복구한다.

## 11. 측정 근거와 한계

- 측정 대상: `kics_disclosure.json`·`PL_breakdown.json`·`IFRS17_BS.json`·`CSM_waterfall.json`·`insurance_liability_portfolio.json`·`dividend.json` 등 마스터의 분기별 건수, `data/disclosure/FY*_Q*/raw` PDF(쪽 단위 키워드 스캔 183개·PDF 생성일), `data/dart/FY*_Q*/raw/*/meta.json` 접수일, 판정 사이드카, 게이트 코드와 `artifacts/kics_validation/report_latest.json`(2026-10-24T03:00Z). 측정 스크립트는 세션 임시 폴더에 있어 저장소에 없다.
- 비평이 바로잡은 것: DART 3Q 제출사는 25사가 아니라 **24사**(2025.3Q 25폴더 중 IBK연금 1곳이 `no_filing` 스텁) · 2025.3Q DART raw 는 24사 전부 디스크에 있음 · 경영공시 PDF 는 2026.2Q 도 `raw/` 에 있음(`pdf/` 폴더 없음) · 신한이지·AIA·AIG 순이익은 `PL_breakdown` 항목 24 에 이미 있음(없는 것은 `management_indicators` 항목 4) · 서울보증의 경영공시 PDF 는 K-ICS·자산건전성 때문에 필요하다.
- **검증하지 못한 것:** PDF 키워드 스캔 수치 일부(사망위험 24/45, 경영효율 1/45 등은 재현하지 않았다) · KIDI 202609 게시 시점 · 3Q 회사별 목록 라벨 · 하노버 게시 여부 · 규제 개정 시행일 · provenance 사이드카가 마스터마다 셀 단위로 강제되는지(`MISSING_PROVENANCE` 범위) · 이미지 PDF 회사의 29-40 「미공시」 여부(텍스트 층이 없어 증명 불가).
- 전체 pre-push 훅은 실행하지 않았다. K-ICS census 만 합성 행으로 모의 실행했고 나머지 게이트의 3Q 반응은 코드 판독과 현재 데이터 통계로 추정한 것이다.
