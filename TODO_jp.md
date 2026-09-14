# Insurequant TODO — jp 레인 (일본 ESR)

> Last updated: 2026-09-14 (31) · 도메인 문서: `docs/domains/claude-agent-jp.md` · Changelog: `docs/changelog_jp.md` · inbox: `inbox/jp/`
> Status 는 최신 5개만 유지, 밀린 항목은 [`docs/todo_archive_jp.md`](docs/todo_archive_jp.md) 로(무수정).

## Status

**🟢 2026-09-14 (31) 손해율 unreachable 3사 재시도 — 2/3 확보(共栄火災·ヤマップ), 大同火災는 여전히 unreachable(jp).**
(30)이 `unreachable` 로 남긴 3사를 **같은 방법을 안 쓰고** 다시 팠다. 산출 `J-ESR/nonlife_ratio_retry.json`(census·`jesr_detail.json`·마스터는 미수정, 병합은 오케스트레이터 소관).
**共栄火災海上保険 — found.** 원인은 TLS 가 아니라 **서버가 중간 인증서를 안 보낸다**(`openssl s_client -showcerts` 로 확인: 리프 인증서 1개뿐, issuer=Cybertrust Japan SureServer EV CA G3인데
체인에 그 인증서가 없음). TLS 검증은 끄지 않고, 그 중간 인증서를 공개 CA 배포 경로(AIA caIssuers URL, crl.cybertrust.ne.jp)에서 받아 프록시 CA번들+certifi 에 합쳐 `verify=` 로 지정하니 200.
FY2025: 正味損害率 60.7 / 正味事業費率 37.0 / 合算率 97.7(원문 표 그대로, 검산 diff 0.0) — ディスクロージャー誌2026 p.71(문서 자체 페이지 "69") 合計행, scope=solo.
**ヤマップネイチャランス損害保険 — found.** Chromium(Playwright)을 이 환경 프록시로 그냥 내보내면 example.com 같은 무관한 사이트까지 전부 `ERR_CONNECTION_RESET`(net-log 로 원인 분리: ①
Chromium 기본 Secure DNS 가 이 환경의 커스텀 CA 를 안 믿음 ② 그걸 꺼도 실제 TLS 핸드셰이크 자체가 프록시 릴레이에서 리셋됨 — 대상 사이트 무관, 이 환경·Chromium 조합의 시스템 문제로 결론).
우회: Chromium 은 JS 실행/DOM 렌더링에만 쓰고 `context.route()` 로 전 요청을 가로채 실제 전송은 검증된 Python `requests` 가 대신하는 방식으로 SPA 를 완전히 hydrate. `/publicnotice`(電子公告)
페이지에서 지난 라운드의 서버렌더 JSON 17페이지 전수조사가 못 본 「ディスクロージャー資料 2026年」 PDF 링크를 발견. FY2025: 正味損害率 50.6 / 正味事業費率 179.5 / 合算率 230.0(원문 표,
검산 50.6+179.5=230.1 vs 표기 230.0, diff 0.1 ±0.15 이내) — p.29(문서 페이지 "27") 合計행, scope=solo.
**大同火災海上保険 — 여전히 unreachable.** TLS 는 정상(Amazon 체인 유효) — **진짜 WAF/ALB 레벨 403**(`Server: awselb/2.0`, JS 챌린지 없는 정적 403 HTML) 이라 헤드리스로도 못 뚫을 가능성이
높다는 근거를 추가했다: 완전히 다른 인프라(r.jina.ai reader, 우리 세션과 무관한 IP)로도 **똑같이 403** — 세션별 IP 문제가 아니라 광범위한 지역/봇 차단으로 보인다. 대체경로 4종 전부 시도:
① 業界団体(日本損害保険協会) 회원 디스크로저 디렉토리 — 자사 링크만 있고 집계자료 없음 ② 등급기관(R&I) 등급 페이지는 열리지만 무료 자료는 정성적 서술뿐, 수치가 있을 발행체 상세 리포트는 유료
페이월(HTML 로그인 페이지 반환) ③ web.archive.org — 도메인 전체 CDX 스캔해도 가장 최근 전면 캡처가 2025-01-26(FY2023 자료까지만), `/2025/07/*`·`/2026/*` 업로드 경로엔 PDF 자체가
안 잡힘(동반 썸네일 이미지만 2025-07-16 에 archived — 아카이브 크롤러도 같은 WAF 에 막힌 정황) ④ archive.ph 는 이 세션 프록시 릴레이 자체가 connection reset(무관한 별도 문제).
**"공시가 없다" 가 아니라 "이 환경에서 못 연다"** — 大同火災는 決算公告·ディスクロージャー誌 를 매년 정상 발행하는 것으로 확인됨(GIAJ 링크·2020~2024 PDF 파일명 패턴 실재).
**다음**: ① census 병합은 오케스트레이터(값 2건 반영 + scope=solo 기록) ② 大同火災는 10월 말 재census 라운드에 사람이 직접 브라우저로 열람하거나 IP 대역이 다른 환경에서 재시도 권고
③ Chromium+프록시 리셋 문제는 이 세션만의 증상인지 다음 라운드에도 재현되는지 확인 필요(재현되면 별도 인프라 티켓 가치 있음).

**🟢 2026-09-14 (30) 손보 손해율 전수조사 — 29사 FY2025 전건 확보, 항등식 69/69. owner 지적으로 재개한 축이다(jp).**
**왜 재개했나**: (17)(2026-09-13)이 손보 6사 표본 중 **3사만 확보**하고 나머지는 네트워크 차단으로 남겨뒀는데, 이 세션이 "막혔던 것 클라우드에서 다시 본다" 고 해놓고 ESR 축만 하고 이 축을 빠뜨렸다. owner 가 그걸 짚었다.
**현황 실측**: census 손보·재보험 34사 중 `jp/jesr_detail.json` 에 손해율이 있던 회사는 **5사**뿐. 나머지 29사를 A(대형·중견 10)·B(중소·특화 9)·C(다이렉트·펫·재보험 10) 3조 병렬로 조사.
**결과**: `found` 24 · `not_applicable_holding` 2(東京海上HD·SOMPO HD — 지주 자료에 그룹 단일 합산치가 없다) · `unreachable` 3(共栄火災 SSL 인증서 체인 · 大同火災 도메인 WAF 403 · ヤマップ Nuxt3 SPA). FY2025 는 기확보 5사 포함 **29사 전건**.
**막혔던 3사 처리**: ① **日新火災 확보** — (17)이 "URL 은 특정했으나 curl 차단으로 미열람" 이라 적은 바로 그 PDF 가 이번엔 200 이다(61.1/36.5/97.6, p81 合計行 직접). ② **あいおいニッセイ同和 확보(우회)** — 자사 사이트는 JS flipbook 뿐이라 PDF 가 없어 모회사 MS&AD HD 결산자료의 **単体 열**에서 확보(64.5/32.6/97.1). ③ **共栄火災 여전히 막힘** — python·curl·WebFetch 세 방법 전부 SSL 인증서 체인 오류. 추정하지 않고 `unreachable` 로 남겼다("못 열었다" ≠ "없다").
**검산**: `合算率 == 正味損害率 + 正味事業費率`(±0.15) 을 전 연도에 돌려 **69건 중 불일치 0**. 값이 맞다는 증명은 아니고 옮겨적기 오류가 없다는 증명이다.
**연도 키 불일치 — 조용히 10사를 잃을 뻔했다**: 3조가 키를 제각각 썼다(A·B `"FY2025"` / C `"2025"` / あいおい는 dict 아닌 float / MS&AD `"FY2025_jgaap"`). 발주 프롬프트에 형식을 안 박은 오케스트레이터 잘못이다. 실측: 순진하게 `["FY2025"]` 로 읽으면 **19사만 잡히고 10사가 사라진다**. `J-ESR/merge_nonlife_ratio_census.py` 로 한 스키마로 합쳐 `J-ESR/nonlife_ratio_census.json` 에 박제.
**같은 열에 놓으면 안 되는 값 4건** (값을 고치지 않고 `caveat` 로 이유만 박제): **トーア再保険**(正味損害率 산식이 LAE 를 분자에 안 더한다 — 이 회사만 과소) · **ソニー損保**(`E.I.損害率`, 경과/발생 기준이라 정의가 다르다. 地震·自賠責 제외) · **レスキュー損保**(이미지 스캔 PDF, 자동추출이 세로쓰기 헤더에서 깨져 **육안 판독** — 신뢰도가 다르다) · **MS&AD HD**(「２社合計（単純合計）」라 자회사 2사를 따로 실으면 중복 계상. IFRS 참고치는 범위가 달라 `alt_values` 로 분리).
`損害調査費` 가 4사에서 검색됐지만 **3사(ジェイアイ·第一アイペット·日本地震再保険)는 표준 산식을 명기한 것**이고 진짜 차이는 トーア 1사뿐이다 — 안 갈랐으면 정상 3사를 이상값으로 몰 뻔했다.
**아직 census·화면 미반영.** 남은 결정 3건은 화면 구조라 owner 판단이 필요하다: ① caveat 4건을 별도 열로 뺄지 라벨만 붙일지 ② `jesr_detail.json` 이 10사 구조인데 24사를 어떻게 실을지 ③ SOMPOダイレクト `source_url` 이 비율표 없는 분책(21p)을 가리킨다 — **다만 그 행은 `not_yet` 이라 게이트 검사 대상이 아니어서 T&D 같은 false-green 이 아니다**(오케스트레이터가 처음에 같은 급으로 말한 것을 정정). census `checked_at` 을 건드리면 전 행 기준으로 수집기 2종이 다시 돌아야 하므로 병합 때 묶는다.
**다음**: ① owner 결정 3건 ② 결정 후 census 병합 + 수집기 재실행 1회 + 빌더 ③ 10/31 재census 와 UH-22 승격 판단.

**🟢 2026-09-14 (29) T&D 222% source_url 검증 — 값은 전부 원문과 일치, source_url 이 랜딩페이지였던 것만 문제(jp).**
긴급 티켓(`esr_in_source_health.json` T&D verdict=skip_landing, adjusted_verdict=not_applicable — census `source_url`
이 PDF 가 아니라 決算短信・補足資料 **목록** 페이지 `ir/document/results.html`). 원인: 그 페이지는 정적 HTML 이 아니라
E-IR Parts(ssl4.eir-parts.net) 외부 SaaS 위젯이 JS 로 채우는 목록이라 실제 PDF 링크가 정적 수집에 안 보인다
(`/ir/event/presentation.html` 決算説明資料 도 같은 위젯). **회사 자체 PDF 로 재검증**: 統合報告書2026(본편·データ編,
`ir/document/annual/pdf/ar2026j_data.pdf`) p8 하이라이트표에 「ESR(内部管理モデル) 222%」가 グループ연결지표(グループ
連結総資産·グループEV·グループ修正利益) 묶음 안에 명시 · 分割版 s4(コーポレートデータ) p3 5개년 트렌드표(…243% 222%)
+ p12 용어집 정의(当社グループ, 内部管理モデル) · 分割版 s3(리스크관리) p24 방법론(VaR 99.5%, 1年). **교차검증**:
有価証券報告書(EDINET S100Y9UP, 2026-06-11提出) p22 「内部管理モデルによるＥＳＲは、222％」(한정어 없음, `scan_pdf`
adjusted_verdict=unqualified) + p53 재구성식 サープラス43,421億円÷エコノミック・キャピタル19,563億円=222%(전기 243% 와
도 정합). **결론: census 값 222/scope=group/basis=internal_management/as_of=2026-03-31/preliminary=no 전부 정정 불필요
— 문제는 source_url 한 필드뿐.** 6개 후보(회사 PDF 4·랜딩페이지 1·EDINET 1) 전수 http_status 200, `check_esr_in_source.py
::scan_pdf` 그대로 import 해서 돌림(재구현 안 함). 산출 `J-ESR/proposal_td_source_url.json`(권고: source_url →
`ar2026j_data.pdf`, doc_type 갱신문구 포함) — census·마스터·증거 파일은 건드리지 않음, 병합은 오케스트레이터 소관.
부수: 같은 세션에서 inbox 티켓(한정어 10종 정본 확정 — 표 현행 유지, T&D 재검증에서도 한정어 0건 재확인) 처리.
**다음**: ① census `source_url`/`doc_type` 셀 병합(오케스트레이터) ② 10/31 재census 때 목표레인지 하단 133% 재확인(이번
조사 4개 문서에 133 언급 없음, 상단 225%(추가환원 트리거)만 재확인됨) ③ 다른 15사 중 landing-page 출처가 더 있는지
`check_source_urls.py` doc_kind 로 스윕.

**🟢 2026-09-13 (28) 출처 게이트 6종 완성 — 사고 3건이 전부 어떤 룰엔가 걸린다, 포스트모템 `closed`(jp).**
(27) 의 "다음" 3건을 다 닫고 UH-21 까지 갔다. ① **`JP_ESR_NOT_IN_SOURCE` 배선**(수집기 `J-ESR/check_esr_in_source.py` 가 증거를 박제 → 빌더는 오프라인으로 읽음, 증거 키 `(url, esr_pct)` — url 만으로 잡으면 값만 고치고 수집기를 안 돌린 상태가 옛 값의 found 를 물려받는다).
**실측이 PM §5 의 전제를 뒤집었다**: 이 축이 잡는 것은 東京海上HD(238, 원문 56p 어디에도 없다 — 문턱 10만 자로 풀어도 not_found)·MS&AD(무관한 합병 보도자료)이고 **かんぽ 220 은 못 잡는다**(그 값은 p35 에 실재, d=1).
초안 "같은 문장" 규격으로 되돌리면 거짓 RED 7건 — §4c-pre 예고치와 정확히 일치. ② **`JP_ESR_ADJUSTED_FIGURE` 신설(UH-21)** — かんぽ형은 "없는 숫자" 가 아니라 **"있는 숫자 중 틀린 것"** 이다.
판정식은 「라벨동반 산문 조각 ≥1(0이면 **기권**) × 전부 한정어 × **같은 문서에 한정어 없는 대안값 존재**」 3곱. 한정어 단독 조건과 정상 상태 답은 같지만, 다음 사람이 목록을 넓히는 경로에서
단독은 정상 3사(日本生命·住友·朝日)를 거짓 발화시키고 대안값 조건만 조용하다 — **표본이 보여줘서** 대안값 조건을 본 룰로 골랐다. 발화 메시지에 「한정어 없는 대안값 181%(p35) 가 있다」 를 같이 찍는다.
재현: 사본 census 를 220 으로 되돌리면 빌더가 그 메시지 + push 묶음 exit 1, 현재값 181 은 미발화. 정상 14사 오탐 0(기권 7·unqualified 7·not_applicable 1).
severity 는 YELLOW 지만 **이빨은 push 묶음**에 뒀다(2026-09-12 에는 census notes 에 조정치라고 적혀 있었는데도 그 값이 나갔다 — 인쇄만 하는 YELLOW 는 통제가 아니다).
③ **한정어 절을 도메인 문서 §3 에 신설** — 실측 관측은 `除いた場合`·`適正水準`·`ターゲットレンジ` 셋뿐이고, 「規制ESR」 같은 **정의 표지는 한정어가 아니다**(넣으면 정상 3사 거짓 발화).
> **정정 2026-09-14 (validation)**: 이 줄이 적은 "UH-23 해소" 는 **과장이었다**. PM 이 요구한 정식 해소는 「§3 절 신설 **+** 코드↔문서 대조 테스트」 둘인데 테스트가 없었고(`tests/test_jp_source_gate.py` 는 ESR **라벨**만 대조했다),
> §3 이 적은 것도 관측 3종뿐이라 코드 10종과 어긋나 있었다 — **실측: 코드 10종 중 §3 에 문자열로라도 있던 것은 4종**이고, 그중 `調整後` 는 §3 이 「추측으로 넣지 말 것」 으로 **지목한** 어휘인데 코드가 실제로 들고 있었다.
> 2026-09-14 에 §3 을 10종 표 + 정의 표지 4종 표로 바꾸고 양방향 대조 테스트 2건을 얹어 닫았다(`TODO_validation.md` 2026-09-14 · 변이 6/6 발화).
④ **포스트모템 `closed`** — 사고 3건이 전부 룰에 걸린다. 잔여 UH-22(severity 승격 판단, 10/31 재측정 조건은 PM §5 에 박음). **UH-23 은 2026-09-14 해소**(위 ③ 정정).
게이트: `prepush_check.py` **REDUCED(jp-scope) gate-clear** 238 passed · 변이 10/10 발화 · `jp/jesr_esr.json` 은 `generated_at` 외 불변. **다음**: ① 10/31 재census 에서 조정치 축 재측정(posted 15→최대 77) ② UH-22 승격 판단. (③ UH-23 대조 테스트 — **2026-09-14 완료**.)

**🟢 2026-09-13 (27) UH-18 출처 게이트 배선(4종·exit code 실증) + UH-19 신규·같은 날 해소 + 산정기준 미확인 0(jp).**
병렬 2건(validation=Opus / jp-collector=Sonnet). ① **배선**: `build_jesr_page_json.py::source_gate_check` 에 4종 —
`JP_SOURCE_EXPIRING_HOST`(netloc ∈ `jesr_http.EXPIRING_HOSTS`, import) · `JP_SOURCE_URL_DEAD`(**증거 판독형**) ·
`JP_SOURCE_EVIDENCE_STALE`(증거 부재·`scope≠all`·census 보다 낡음·posted `checked_at` 결측) · `JP_SOURCE_EVIDENCE_INCOMPLETE`(posted URL 미점검).
`self_check` 가 errors 에 extend → `main()` exit 1 **실증**(그 extend 한 줄을 지우는 변이에서 exit-code 케이스 3개만 정확히 FAIL).
회귀 `tests/test_jp_source_gate.py` **43 케이스**, 이빨 변이 5/5 발화. 예외 등재처 `J-ESR/jp_source_exceptions.json` 신설(0건, fail-closed, **등재는 owner 권한**, 절차 룰 2종은 면제 불가).
**빌드는 여전히 오프라인** — 네트워크 판정은 `check_source_urls.py --all` 이 `source_url_health.json` 에 박제하고 빌더는 그 박제를 읽는다(dead 룰의 이빨은 신선도 룰에 전적으로 의존, **둘은 한 쌍**).
오탐억제: 증거에서 RED 로 읽는 분류는 `dead` 하나뿐 — "ok 아니면 RED" 로 짰으면 254건 중 **48건이 한꺼번에 거짓 RED**(blocked 20·requires_headers 16·tls 4·spa 4·error 4).
② **UH-19(신규)**: jp 게이트는 **빌더를 돌릴 때만 돈다** — census 만 고치고 커밋한 `62eed63`(내 커밋)이 실제 사례로, HEAD 의 배포 JSON 이 census 와 어긋나 있었다(2사 basis=unconfirmed, SOMPO high_pct=270).
같은 날 ① 재빌드 ② `tests/test_jp_deploy_matches_census.py` 신설(빌더를 임시 경로로 재실행해 커밋본과 `generated_at` 제외 전량 비교 — **"빌더를 돌렸는가" 자체가 검사 대상**)로 닫았다. 변이 확인: 배포본 수치 하나 흔들면 즉시 FAIL(원본 md5 복원).
③ **훅 배선**: 두 테스트를 `scripts/prepush_check.py` offline 묶음 + CLAUDE.md §5 jp 축소범위 목록에 넣었다 — 안 넣으면 "배선했는데 push 를 안 막는" 2026-08-21 실패의 반복이다.
④ **산정기준 미확인 0**: ライフネット 333% = **규제 표준식**(決算短信 p5·有報 S100YC7R 동일 문장, 같은 문서의 内部ESR 394% 와 혼동 금지) · SOMPO 270% = **내부모델**(決算説明資料 p14 각주 99.5%VaR, 有報도 「独自にＥＳＲを計算」).
**SOMPO 목표레인지 정정**: 「2025年度通期決算から、ターゲットレンジおよびレンジ上限(250%)を撤廃し、下限 200% をターゲット資本水準として設定」 → 200% 이상 단일 기준. 종전 '200~270%' 는 오류였다(270 은 당기 ESR 값, 폐지 전 상한은 250).
**다음**: ① `JP_ESR_NOT_IN_SOURCE`(사고 3건 중 2건을 잡는 축)는 오탐억제 3종의 **실측 분포**(이미지형 PDF·랜딩페이지 정본 몇 사)가 선행조건 — 규격은 PM §4c-pre 에 확정, 세기 전엔 배선 금지(UH-5·UH-9 선례)
② `self_check` 의 `records count != 15` 하드코딩은 **10/31 재census 에서 그대로 깨진다** ③ ライフネット scope(원문은 連結 서술, census 는 solo) 확인.


## Active follow-ups

- **✅ 해소(2026-09-13, owner 업로드).** `build_jesr_detail_json.py` 가 새 클론에서 못 돌던 문제 — 입력 PDF 가 gitignore 라 `FileNotFoundError` 로 죽었다.
  owner 가 추출 중간산출 4종(`extracted_sample_values.json` · `extracted_bs_values.json` · `life_core_history.json` ·
  `meijiyasuda_nonlife_main_pages_fixture.json`)을 올려 줘서 `.gitignore` 를 좁혀 **JSON 만 추적**한다(PDF 는 계속 제외 — 무겁고 다시 받으면 된다).
  실측: PDF 0개인 클론에서 빌더 완주, SELF-CHECK OK, 日本生命 preliminary 오탐까지 자동 교정. 앞으로 수치 수정은 셀 수술이 아니라 **census 고치고 재빌드**가 정상 경로다.

- **10월 census 선행 절차(2026-09-13 신설).** census 를 돌리기 전에 `python J-ESR/check_source_urls.py --all` 을 먼저 돌린다. 2026-09-13 기준
  blocked 21 · spa_shell 8 · requires_headers 17 — 헤더 없이 훑으면 이 46건이 전부 `not_found` 오탐이 된다. dead 5건은 그 라운드에 대체 URL 확보
  (朝日生命 `company/zaimu/` · キャピタル損害保険 disc PDF · オリックス生命 `company/` · 日本生命 `ir_health_url` 구경로).
- **EDINET 보류 3사**(第一ネオ生命保険 · 大樹生命保険 · 第一アイペット損害保険): 코드리스트에 비슷한 이름이 있어 자동매칭을 막아 뒀다(`edinet_code_match.json`
  의 candidates). 사람이 한 번 보고 확정. 第一ネオ生命 은 그 행 notes 자체가 「第一フロンティア生命と同一?」이라 회사 실체부터 확인할 것.
- **10월 有報 재스캔**: `jesr_edinet_fetch.py --scan --from 2026-10-01 --to 2026-11-30 --doc-types 130,140`(訂正有報·半期). 그 뒤 `edinet_esr_probe.py` 재대조.

- **비공개 프리뷰 경로(owner 2026-09-12 결정).** 저장소는 `jp/` 그대로, main 배포만 `jp-f9027362/`(`scripts/android_push_and_deploy.sh`
  `JP_PRIVATE_DIR`, `deploy_path()` 매핑; 첫 전환 라운드에 main 의 공개 `jp/` 는 자동 삭제). 라이브 주소 = `https://www.insurequant.com/jp-f9027362/`.
  noindex 유지, 한국 페이지 링크 없음. 공개 repo 라 폴더명은 repo 열람자에겐 보인다("링크·검색 비노출" 수준). **공개 전환 체크리스트:**
  ① `JP_PRIVATE_DIR=""` ② 그 라운드 main 에서 `git rm -r jp-f9027362` ③ `jp/*.html` noindex 제거·robots/sitemap 등재 ④ 루트 index.html hreflang·언어전환·안내띠 삽입
  (designer 답변 조각) ⑤ Cloudflare Access 는 유료 인증이 필요해질 때.
- **10월 말 재census** (2026-10-31 기한 직후): 같은 티켓 구조·같은 csv 열로 79사 재조회. notes 에 "패턴 기반 잠정" 이라 적힌 행(Zurich Life·AXA Life 등)부터 연다. 확정치가 나오면 `preliminary` 5사(LifeNet·Asahi·Fukoku·Japan Post·Sumitomo) 갈아끼움.
  **같은 라운드에 3축도 같이 뽑는다(owner 2026-09-12 확정, 아래 스코프 확장 항목과 병합·더는 미결 아님):** 회사별 공시 PDF 를 어차피 다시 여니
  ESR 옆에 열 3개 추가 — `air_used`(자산집약형 재보험 활용 여부·목적에 "ESR 개선" 명시 있는지) · `catastrophe_reserve_adequacy`(이상위험준비금/화재보험
  충족 여부, 생보는 해당없음) · `interest_margin_sign`(이차손익 부호·역마진→이익 전환 서술 유무). 손보 원문에 이상위험준비금 열람이 이미 필요하므로
  추가 비용 작지만, **생보 AIR·이차손익 서술은 다른 섹션**(결산설명자료 리스크관리·계리 파트)이라 놓치기 쉽다 — census 티켓에 이 3열을 명시할 것,
  "ESR 만 보고 넘어가는" 기본 습관으로 되돌아가지 말 것.
  **+ 산정방식 2열**(owner 09-12 질문): `calc_method`(standard/internal_model/unstated) · `confidence_level`. 09-12 census 는 SOMPO 1사만
  "VaR 99.5%" 명시, 14사는 미확인(기본값 `J-ICS`). 도메인 문서 §4b-4. 결과로 `/jp/` 각주("各社で異なる場合があり")를 실측 문구로 교체.
- `/jp/` 라이브 반영(owner 승인 후): publishing 티켓 답변의 "라이브 반영 시 필요한 것" 3건 — 배포 keep-list 가 4페이지 하드코딩(3곳)이라 새 페이지가 게이트에서 안 보임 → 목록화 필요; xlsx 시트 불필요; status_report 4절은 현재 무검사. 루트 `index.html` 에 hreflang 2줄 + 언어 전환 링크(designer 답변 조각).
- `jp_insurers.csv` 완전 중복 2행 정리(행 순서 보존 원칙 때문에 이번엔 보존). not_found 2사(Meiji Yasuda Trust Life·Yamap) 공시 페이지 재탐색.
- **3축 화면 반영은 별도 판단.** census 에 열만 먼저 채우고, `/jp/` 화면에 얹을지(카드 추가·범례 등)는 10월 말 데이터가 실제로 얼마나 뽑히는지
  본 뒤 owner 에게 다시 묻는다(루트 `TODO.md` J-ESR 항목의 기사 원 취지 — insnews #92437, 일본 금융청 2026 보험 모니터링 보고서 참고).
