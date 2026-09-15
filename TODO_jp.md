# Insurequant TODO — jp 레인 (일본 ESR)

> Last updated: 2026-09-15 (33) · 도메인 문서: `docs/domains/claude-agent-jp.md` · Changelog: `docs/changelog_jp.md` · inbox: `inbox/jp/`
> Status 는 최신 5개만 유지, 밀린 항목은 [`docs/todo_archive_jp.md`](docs/todo_archive_jp.md) 로(무수정).

## Status

**🟢 2026-09-15 (33) 손보 법정 BS/PL 추출 — 貸借対照表 5→21사, 損益計算書 5→23사(jp).**
손해율 전수조사로 손보 31사 목록이 생겼는데 **26사는 `bs.status="not_obtained"`, PL 도 보험료 1개뿐**이었다. 그 26사 PDF 를 전부 받아(126MB, gitignore) 법정 単体 貸借対照表/損益計算書를 뽑았다.
**병렬 4개조로 발사했으나 3개조가 세션 한도(429)로 죽어**, A조 7사만 에이전트 산출이고 나머지 19사는 오케스트레이터가 **결정론적 범용 파서**(`scratchpad/bspl/generic.py`)로 직접 뽑았다.
**파서 핵심 2가지** ① **PL 페이지를 표제가 아니라 값으로 앵커링** — `正味収入保険料` 행이 이미 화면에 나가는 (前期, 当期) 쌍과 정확히 일치하는 페이지가 곧 법정 損益計算書다. 표제(`損益計算書`)로 고르면
5년추이표·連結·부속명세를 집어 7사 중 6사가 어긋났다(실측). ② **BS 는 勘定式**(資産=왼쪽, 負債·純資産=오른쪽, 같은 줄)이 흔해 x 중앙에서 반 갈라 파싱하지 않으면 한 행에 좌우가 섞여 4열이 된다.
**검증 4축**(스키마 / `資産合計=負債合計+純資産合計` / 보험료 당기·전기 대조 / **법정 PL 역산 손해율 vs 기존 화면값**). 4축이 제일 세다 — 完全히 다른 표(主要な経営指標等の推移)에서 뽑은 손해율과
소수점까지 맞아야 하므로 다른 회사·다른 연도를 읽으면 반드시 튄다. A조 7사는 손해율 Δ 전건 ±0.0pt.
**4축이 실제로 잡아낸 것**: 全管協れいわ 사업비율 역산이 +1227.8pt 차 → 조사 결과 추출이 아니라 **원문이 "単位未満を切り捨てて表示"인 초소형사**(보험료 26·지급보험금 4백만엔)라 백만엔 반올림으로 비율 재현이
불가능한 것이었다. 그래서 4축을 **규모 인지형**으로 고쳤다(보험료 <1,000백만엔이면 '검증 불가'로 남기고 통과로도 실패로도 치지 않는다).
**적재**: BS 16사 추가(10→26, `extracted_bs_values.json`, tree 조립은 `extract_bs.build_tree` 재사용) · PL 19사(`J-ESR/nonlife_pl_census.json` 신설). 빌더 `profit.items` 자기검사는 **지우지 않고 화이트리스트(`NONLIFE_PL_ITEM_IDS` 18개)로 넓혔다.**
**미완 10사**(전부 이유가 특정됨): ① BS 페이지 미검출 3사(capital·三井ダイレクト·東京海上ダイレクト — PL 은 실었다) ② PL 앵커 실패 2사(楽天·セコム) ③ 보험료 전기 불일치 1사(ペット＆ファミリー) ④ **출처 교체 필요 3사**
(あいおい·MS&AD HD 는 지금 출처가 MS&AD 그룹 IR 덱이라 貸借対照表 표제가 0쪽, ソニー損保는 소니FG 결산덱) ⑤ **스캔 PDF 1사**(レスキュー — 17.8MB/50p 텍스트 0자, OCR 필요).
**다음**: 위 10사. ④는 각 사 자체 ディスクロージャー誌 URL 로 교체(owner 상시 승인), ⑤는 OCR 또는 대체 원본.

**🟢 2026-09-14 (32) 정미수입보험료 26사 수집분을 `jesr_detail.json` 에 적재 — 손해율 31사 전건 보험료 확보(jp).**
버블차트의 원 크기 축(owner 발주)이 쓸 데이터를 `J-ESR/build_jesr_detail_json.py` 가 읽어 싣도록 했다. 입력은 `J-ESR/nonlife_premium_census_{A,B}.json`(26사, `正味収入保険料`, 단위 백만엔,
연도키 `FY20xx` 강제 — 안 맞으면 `SystemExit`). 병렬 에이전트 3개가 연도키를 제각각(`FY2025`/`2025`/맨 float) 쓴 (30) 라운드 사고의 재발 방지로, 이번엔 로더가 키 형식을 검사한다.
**단위 라벨 함정을 그냥 넘기지 않았다**: `ratio_only` 블록은 종전에 `unit:"pct"` 였는데 백만엔 값을 같은 블록에 넣으면 라벨이 거짓이 된다 → 보험료가 있는 회사만 `unit:"JPY_million"`
(비율 항목은 풀컴퍼니 관례대로 `_pct` 접미사로 구분). `profit.items` 가 비어 있어야 한다는 자기검사는 **지우지 않고 좁혔다**(`pl_net_premiums_written` 만 허용 + 그게 있으면 단위 라벨 2곳을 강제).
**ソニー損害保険만 지표가 2개 다르다** — X축은 `E.I.損害率`, 원 크기는 `元受正味保険料`(재보험 출재 **전**). `premium_caveat.code="gross_direct"` 로 화면 툴팁에 사유를 노출한다(owner 상시 지시 "caveat 표시만").
검증: 손해율 31사 · 보험료 **31/31** 적재 · 단위 라벨 전건 `JPY_million` · 빌더 고정점 ④→⑤→④ 3회 바이트 동일(`build_jesr_page_json.py` 가 `jesr_detail.json` 의 `_meta.group_children` 를
읽는 순환 의존 때문에 순서가 정해져 있다) · ESR 16사 값 변경 0사. 최대/최소 배수 124,062배(東京海上日動 2,596,396 vs 全管協れいわ 26백만엔) — 이 배수가 버블 크기 스케일 설계의 입력이 됐다.
**다음**: 大同火災는 여전히 unreachable((31) 그대로) — 10월 말 재census 라운드로.

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
