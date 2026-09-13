# Insurequant TODO — jp 레인 (일본 ESR)

> Last updated: 2026-09-13 (25) · 도메인 문서: `docs/domains/claude-agent-jp.md` · Changelog: `docs/changelog_jp.md` · inbox: `inbox/jp/`
> Status 는 최신 5개만 유지, 밀린 항목은 [`docs/todo_archive_jp.md`](docs/todo_archive_jp.md) 로(무수정).

## Status

**🟢 2026-09-13 (25) 타 세션 리허설 미결 5건 이관·처리 + EDINET 키 실측 — 출처 URL 점검기 신설·코드 7개 정정·화면 수치 2건 정정(jp).**
티켓 `inbox/jp/20260913T1325Z__owner__JP_MULTI__source_url_rehearsal_and_edinet_key.md`(resolved). 다른 세션(`session_01F9N5Bt…`, `solvencyk/solvency`)이 insurequant
push 권한이 없어 남기지 못한 후속 5건을 이관해 전부 닫았다. ① 공용 헤더 모듈 `J-ESR/jesr_http.py` + 점검기 `J-ESR/check_source_urls.py` — 판정 6종
(ok / ok_requires_headers / blocked / tls_client_issue / spa_shell / dead), 전수 254건·고유 139건에서 blocked 21 · spa_shell 8 · requires_headers 17 · dead 5
(`J-ESR/source_url_health.json`). **리허설의 "東京海上HD IR 은 SPA" 판정은 오진**이었다 — 364바이트의 정체는 `<meta http-equiv="refresh">` 한 줄이고 따라가면
링크 25·PDF 6이 정적으로 다 있다(probe 가 2홉 추적). `sonylife.co.jp` 는 파이썬만 TLS 악수 실패·curl 200 → `tls_client_issue` 로 분리(죽음 아님).
② TDnet 영구인용 금지 규칙화(`jesr_http.EXPIRING_HOSTS`, 도메인 문서 **§4c**) + 404 3건 대체 URL 확보(東京海上HD 게시 디렉토리 이동 · 日本生命 사이트 개편 · T&D 만료).
③ **EDINET 키**: smoke PASS. 호스트 정본 `api.edinet-fsa.go.jp/api/v2`(종전 `disclosure…` 는 301→302, **키 없으면 HTTP 200 + 본문 StatusCode 401** 함정).
공식 코드리스트 11,389건 대조로 **기재 13개 중 7개가 다른 회사 코드**(E04979=パーク24 · E04506=九州電力 …) — `jp_insurers.csv` TBD 62행 해소
(매칭 27 / 미등록 확정 51 / 보류 3), 有報 의무는 17사뿐이 **EDINET 루트의 천장**. FY2025 有報는 이미 6월에 14사 제출(「10월 제출」 가정이 틀렸다 — 10/31 은 J-ICS 공시 기한).
XBRL 태그엔 ESR 없음(기존 결론 유지)이나 **본문 iXBRL 엔 서술로 있다** → `edinet_esr_probe.py` 가 15건 전부 검출, 5사 수치 확정. 도구·증거 4종
(`edinet_codelist.py`/`edinet_code_match.json`, `edinet_esr_probe.py`/`edinet_esr_probe.json`). ④ **화면 수치 정정 2건**(1차 원문 직접 열람):
東京海上HD 238 → **268**(238 은 원문 어디에도 없는 2차보도 인용값; 決算プレゼン p5·p44 와 有報 S100YLS8 본문 모두 268, 自己株取得 후 255·리스크테이크 반영 234),
かんぽ生命 220 → **181**(220 은 「大量解約リスクを除いた場合」 조정치; 원문 p35·p37 과 有報 S100YD29 모두 181 監査未済 暫定). MS&AD 는 출처 URL 이 2026-02-13
**합병 보도자료** 오인용이라 電話会議資料(p17 226→214)로 교체(수치 214 는 유지). 부수 버그: `build_jesr_page_json.py` preliminary 키워드가 한국어뿐이라
일본어 원문(暫定値·監査未済)을 인용하면 확정치로 표시 → 키워드 추가, かんぽ preliminary=true 복귀. **다음**: ① 10월 census 는 `check_source_urls.py --all` 선행
② dead 5건(朝日生命·キャピタル損保·オリックス生命·日本生命 구경로 2) 대체 ③ 第一生命HD 의 EDINET 등록명이 「第一ライフグループ」(E06141)인 것 확인.

**🟢 2026-09-13 (24) 랭킹 색을 각사 ESR 목標レンジ 기준으로 + 第一生命 損益·基礎利益 층 + 貸借対照表 10사(orchestrator).**
owner "목표 레인지 초과 초록(높을수록 진하게) / 100% 초과~레인지 이하 노랑(100% 에 가까울수록 붉게) / 100% 미만 빨강(낮을수록 진하게)". `jp/index.html`
`colorForRange()`·트랙 위 목표 밴드·「目標 ○～○%」칩·툴팁(출처, 자회사는 모회사 목표 상속)·범례 5종. 레인지는 (23) census → `build_jesr_page_json.py::attach_target_ranges()`
→ `jp/jesr_esr.json` record.target_range(4사 부착: TMHD 190%以上 / MS&AD 180~250 / Sompo 200~270 / T&D 133~225; 미공표사는 100% 기준 참고색+툴팁). **검증 필요**: T&D 만
원문 직접 열람, 나머지 3사는 검색 스니펫 — Sompo 上限 270 이 현재 ESR 270 과 같아 의심 → 10월 재조사 1순위. 第一生命: owner 업로드 분책 index_004 로 損益計算書
p25~26·基礎利益 A/B/C p30·再保険 p21·会計方針 p32~33 추출(P01~P16 실패 0, 契約者配当準備金繰入額 항목 신설로 P04 정합), core_history 5개년(p7)·順ざや/危険差(p31, 억엔),
builder 가 損益 층 있는 생보를 상세 회사로 승격(esr_status not_yet 5 = 大型損保 3 + NN·第一; life_core_only 3). 旧基準SMR 파서 전각 대시(ー) 버그 수정(第一 852.9).
貸借対照表 10사 전부(住友 7월 資料編·第一 분책·明治安田損保 열 우선 파서). **다음**: ① 10월 재조사에서 目標レンジ 원문 확인·미공표 12사 재탐색 ② NN·第一 三利源 억엔 통일 표기.

**🟢 2026-09-13 (23) 각사 ESR 목표레인지(자본정책) census 20사 → `J-ESR/esr_target_ranges.json` 신설(jp).**
티켓 `inbox/jp/20260913T1610Z__owner__JP_MULTI__esr_target_ranges.md`(answered). owner "랭킹 막대색이 감독하한 100%뿐이라 전부 초록 — 자본정책 목표레인지로 차등하겠다더니 안 됨" →
`jp/jesr_esr.json` 15사 + `jp/jesr_detail.json` 미중복 5사(Dai-ichi Life Insurance·NN Life·Tokio Marine & Nichido Fire·Mitsui Sumitomo Insurance·Sompo Japan Insurance) 총 20사 WebSearch/WebFetch
census. **확보 6건**: Tokio Marine HD 190%+(2026-03 신규제 전환, 구기준 100~140%/99.95%내부모형에서 99.5%규제로 재설정) · MS&AD HD 180~250% · Sompo HD 200~270%(기존 jesr_esr.json
basis=J-ICS_VaR99.5와 일치) · T&D HD 133~225%(ERM 페이지 직접열람, 신뢰수준99.5% 원문 확인 — 6건 중 유일 직접확인) · Dai-ichi Life 170~200%(그룹+국내3사 공통) — 전부 basis=regulatory·
confidence=99.5%. 자회사 3사(東京海上日動·三井住友海上·損保ジャパン)는 모회사 레인지 상속(`inherited_from`). **null 14건**: 상호회사 5사(日本生命·住友生명·明治安田生命·朝日生命·富国生命)
전원 목표레인지 미공표(추정 금지 원칙대로 null), Sony Financial Group·ソニー生命(모회사도 null이라 상속 불가)·かんぽ生命·ライフネット生명·NN生명·au損保·明治安田損保(모회사 상호회사라 상속 불가) 미확인.
직접 PDF 열람은 T&D 1건뿐, 나머지는 WebFetch가 PDF 텍스트추출 실패(스캔/암호화)하거나 403이라 WebSearch 스니펫 교차확인으로 대체(policy_note에 명시). 산출
`J-ESR/esr_target_ranges.json`(계약대로 low_pct/high_pct/basis/confidence_level/policy_note/source_url/source_doc/as_of/inherited_from). 도메인 문서 §4b 에 `esr_target_range` 항목 추가.
페이지 색 규칙 반영은 오케스트레이터 소관(designer). Sonnet 5, 약 20분, 회사당 검색≤2·fetch≤2 준수. 다음(10월 재census) = Sony FG·かんぽ生命·ライフネット·NN生명·상호회사 5사 재탐색.

**🟢 2026-09-13 (22) 회사별 상세 3페이지 분리(jesr 자본 / jgaap 회계 / disclosure 기타공시) + 所要資本 워터폴 폐지 + 貸借対照表 T자형 패널(orchestrator).**
owner "한국처럼 자본·회계·기타공시로 나눠라, 워터폴은 분산효과만 보여주니 빼라, jgaap 에 IFRS17.html 식 T자 BS". 종전 `jp/jesr.html` 인라인 CSS/JS 를
`jp/jp.css`·`jp/jesr_app.js`(공용, `<body data-page>` 분기·byId 가드·`?company=` 탭 동기화)로 빼고 `jgaap.html`(主要指標 4카드·損益 2블록·워터폴·収益性·
種目別·基礎利益·準備金·**貸借対照表 T자**)·`disclosure.html`(再保険 의존도·その他) 신설, axes 라우팅 reserve→jgaap / reins→disclosure / smr→esr.
`jp/index.html`·`terms.html` 헤더 3탭. T자 패널은 (21)의 `bs.tree` 를 IFRS17.html Panel 1 규칙(존 3개·[+]·負債:純資産 flex 비율·2기 비교표·資産=負債+純資産 배지)로 렌더,
**10사 전부 표시**(같은 날 후속: 住友生命 7월 資料編 WebFetch 확보 p58 / 第一生命 owner 업로드 アニュアルレポート2026 분책 index_004 p23~24 / 明治安田損保 본편 p39~40 열 우선 표에 `col_major_3yr` 파서). Playwright 12케이스×2폭 pageerrors 0, `test_deploy_assets` 11 passed. 배포 NEW_FILES +4(폰 2회).
**다음**: ① 第一生命 분책 index_004(業績に関する諸資料 86p, `others/daiichi_2026_index_004.pdf`)에 損益計算書·基礎利益·5개년 표가 있다 — profit/core_history 층도
채울 수 있다(현재 not_acquired). ② 生保 日本·明治安田는 5월 연결 요약이라 当期末만 — 7월 본편 확보 시 単体 2개년으로 교체. ③ 準備金 표 `cat_reserve_fire` 라벨
"火災 行 × 異常危険準備金 列" → builder `LABEL_JA_DISPLAY_OVERRIDES` 로 「異常危険準備金（火災）」. ④ 前期 出再保険手数料(20).

**🟢 2026-09-13 (21) J-GAAP 貸借対照表 요약 층 `bs` 신설 — 상세 10사 중 7사 extracted, T자형 BS 패널용 tree 18행·checks 3종(jp).**
티켓 `inbox/jp/20260913T1300Z__owner__JP_MULTI__jgaap_balance_sheet.md`(answered). `J-ESR/extract_bs.py`(신규, `extract_esr_template_samples.py` 헬퍼 재사용) →
`extracted_bs_values.json` → builder `build_bs_block()`+`BS_LABELS`+self_check(id↔labels·합계 3행, checks False 는 WARN) → `jp/jesr_detail.json` 10사 전부 `bs` 블록,
`_meta.coverage.bs_extracted=7`, SELF-CHECK OK. 손보 4사(au·TMNF·MSI·Sompo)+NN Life 는 단체 2개년 百万円 checks 3/3 True; 日本生命·明治安田生命은 5월 설명자료 연결 요약(億円→×100,
当期末만, group) 으로 equity 검산 True·준비금 검산 None. not_obtained 3(明治安田損保 별책엔 純資産 없음·住友生命 요약 없음·第一生命 PDF 없음). 함정 3: NN Life `△ 7,608`
부호 뒤 공백, MSI 「純資産の部資本金」 라벨 접합, Sompo 資本剰余金/利益剰余金 은 合計 행에만 값. 문서 §12. 32분(상한 30분 소폭 초과). 다음 = 오케스트레이터 `jgaap.html` T자형 렌더.

## Active follow-ups

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
