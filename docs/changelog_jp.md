# Changelog — jp 레인 (일본 ESR)

> 이력 저장소. 세션 시작 시 읽지 않는다. 현황은 `TODO_jp.md`.

## 2026-09-12 (8) -- `jp/jesr_detail.json` 신규 조립 (publishing)

- 티켓 `inbox/publishing/20260912T1120Z__owner__JP_MULTI__jesr_detail_json.md`(answered). owner: "2개사에 대해 K-ICS.html 에
  대응되는 페이지 만들어라" — `jp/company.html`(designer 병렬 티켓 `inbox/designer/20260912T1120Z__..._jesr_company_page.md`,
  이 세션은 미접촉)이 fetch 할 회사별 상세 데이터.
- 신규 `J-ESR/build_jesr_detail_json.py`(stdlib only, self-check 내장 — 실패 시 exit 1). 입력: `extracted_sample_values.json`
  (이미 존재, 없으면 `extract_esr_template_samples.py` 자동 선실행) · `esr_disclosure_schema.json`(137 items) ·
  `esr_aggregation_rules.json`(포인터로만 읽음 — known_deviations 는 이미 각 check 의 note 필드에 반영돼 있어 재병합하지 않음) ·
  `jp/jesr_esr.json`(self-check 대조 소스).
- `census.status == "posted"` 인 2사만 채택(au_nonlife·meijiyasuda_nonlife). nnlife 는 ESR 미공시(`not_yet`)라 제외.
- **source_url/doc_type/doc_date/preliminary 는 `J-ESR/jesr_master.json` 에서 조인.** `jp/jesr_esr.json` 은 부모-자회사 중복
  제거(2026-09-12 (3) 항목, archive 이관)로 明治安田損害保険 을 `_meta.excluded_subsidiaries` 에만 `esr_pct` 없이 남겨 저 4필드가
  비어 있다 — `jesr_master.json`(제외 전 15사 원본)에서 회사명(`company_en`)으로 조인해 채웠다. au_nonlife 는 두 파일 값이 동일함을
  확인(중복 아님).
- 계약 고정 키(designer 와 확정, 리네임 금지): `risk` 블록은 `rc_diversification`→`diversification_effect`,
  `rc_tax_effect`→`tax_effect` 로 표시 키를 바꿔 매핑(값은 그대로), `market_sub` 6항목, `sensitivity[]`(scenario 별
  `delta_pp`=기준 대비, `base` 시나리오·미공시 값은 제외), `aggregation.deviations`(informational 실패 체크만, hard fail 은
  자동으로 0 이라 `reproduced`=true).
- 실측(exit 0): au_nonlife esr_pct=791.7·eligible=9,278·required=1,171·reproduced=true·checks=43/43·deviations=0(민감도
  공시 생략사라 sensitivity=[]) / meijiyasuda_nonlife esr_pct=743.2·eligible=40,290·required=5,420·reproduced=true·
  checks=49/51·deviations=2(`G06_nonlife` 다지역 상관통합 순서 차이·`G07_catastrophe`, 둘 다 `esr_aggregation_rules.json
  known_deviations` 등재분과 동일)·sensitivity=7행(엔금리+50bp→esr_pct 736.7/delta -6.5pp 등, 티켓 예시값과 정확히 일치).
  `_meta.coverage`={detail_posted:2, posted_total:13(=`jp/jesr_esr.json` records 길이), census_total:79}.
- self-check 4종 통과: companies==2 · 각 headline.esr_pct 가 `jp/jesr_esr.json`(records ∪ excluded_subsidiaries) 대조 일치 ·
  `risk.rc_post_tax == headline.required_capital` · `items` 의 모든 id 가 `_meta.labels` 에 존재 · 단위 무변환 통과(items.eligible_capital
  == headline.eligible_capital, 억엔 환산 없음).
- 파일 위생: BOM 없음(`xxd` 첫 바이트 `7b0a`=`{\n`) · `ast.parse` 통과 · `git status --short J-ESR/ jp/` = 신규
  `build_jesr_detail_json.py`·`jp/jesr_detail.json` 뿐(루트 마스터·xlsx·public_exports·keep-list·HTML 무변경; `jp/_fixture_jesr_detail.json`
  은 designer 병렬세션 산출물이라 손대지 않음).
- 배포 준비만: `scripts/android_push_and_deploy.sh` `NEW_FILES` 한 줄에 `jp/company.html jp/jesr_detail.json` 추가. 실제 push 는
  `jp/company.html` 완성 + owner 승인 후 별도 라운드.
- 재현: `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_detail_json.py`.

## 2026-09-12 (7) -- 소요자본 합산 규정(상관행렬) 기계화 + √(xᵀRx) 재계산 검산 (jp)

- 티켓 `inbox/jp/20260912T1005Z__owner__JP_MULTI__esr_aggregation_rule.md`(answered). owner 지적: 직전 티켓이 "부모 ≤ Σ하위" 부등식으로 끝냈는데
  당연히 상관행렬 통합이니 규정을 찾아 공시 합산액이 재현되는지 검산해야 한다(K-ICS mmult 검산과 같은 것).
- 규정 원문 확보 `J-ESR/raw/regulation/`: 令和7年金融庁告示第74号(1柱, 167p, fsa.go.jp 통합본 — 2026-03-23 개정 반영 확인)·第75号(3柱 별지양식,
  67p — curl 35KB 절단이라 WebFetch 바이너리 저장본)·令和8年告示第6号(개정 8p, 합산 조문 무변경). 미확보 4건(概要·Q&A·필드테스트 仕様書·3柱
  개정)은 curl 000 으로 남김, 추정으로 채우지 않음.
- 기계본 `J-ESR/esr_aggregation_rules.json`: 최상위 第155条 행렬(生保–損保 0.00, 그 외 0.25) + オペ 선형가산, オペ 상한 第154条(20%×(√+G)),
  세효과 第156条(0.8×法定実効税率×(√+F+G) vs DTA 분기 min), MA 上限超過 第46条, 生保 第81条(死亡–長寿 −0.25 등), 損保 第89条 4단계+別表七,
  巨大災害 第100条(0.00), 市場 第127条(스프레드 上昇/下降 2행렬, 資産集中 0.00), 信用 第128条 단순합, 分散効果 정의(75호 注 6(5)),
  공시 하위행 정의(注 3(2)·4(4)), MA 행은 정보행(注 6(3)). known_deviations 등재부 포함.
- `extract_esr_template_samples.py`: `run_aggregation_checks` G01~G10(gate/informational 구분, known_deviations lookup), `rc_life_*` 6 id
  추가(스키마 esr 109→115, K-ICS 29/30/31/33/34 대응, `stop_before` 로 생보 MA 행이 巨大災害 MA 행을 삼키는 사고 예방). exit 0.
- 재현: 分散効果 au 273.6/274·MY 2,529.5/2,530, 세효과 두 회사 ±1(역산 세율 28.0%), 시장 MY 4,611.8/4,613, au 損保 정확, au オペ 20% 캡 바인딩.
  미재현: MY 損保 +41(다지역 구조, informational 규칙) · MY 巨大災害 +109(注 4(4) 위반 방향 — `その他の巨大災害` 단순합 가설, 10월 재확인).
- 문서: `docs/domains/jp_esr_disclosure_template.md` §8 신설 + §0/§3/§4/§6/§7-4 동기, `claude-agent-jp.md` §3 포인터.

## 2026-09-12 (6) -- ESR 규제 공시 양식 지도 + 기계 스키마 + 표본값 (jp)

- 티켓 `inbox/jp/20260912T0905Z__owner__JP_MULTI__esr_disclosure_template_map.md`(answered). owner 취지: 10월 말 62사가 낼 규제 양식
  (令和7年金融庁告示第74号·第75号)을 지금 표본 2건으로 해부해 두면 회사마다 다른 표를 같은 열로 뽑을 수 있다. 발주 직후 범위 확장(6~8번):
  `kics_item_ref` 열, 기사 3축(異常危険準備金·재보험/AIR·基礎利益/逆ざや) 같은 문서에서 추출, 생보 표본 NN Life 추가, 생보/손보 양식 차이.
- 산출: (A) `docs/domains/jp_esr_disclosure_template.md` (B) `J-ESR/esr_disclosure_schema.json` (C) `J-ESR/raw/fy2025_samples/extracted_sample_values.json`
  + 생성기 `J-ESR/extract_esr_template_samples.py`(fitz, NFKC 정규화, 라벨 순차 커서, 절사 구간 검산; exit 0 게이트). 스크래치 `_item_table_fragment.md` 는
  생성기가 다시 만드는 문서 조각.
- 실측: 스키마 131항목(esr 109 / article_axes 22). 검산 C01~C34 + A01~A05: au 34/34, Meiji Yasuda Non-Life 41/41, NN Life 4/4. census 헤드라인
  791.7 / 743.2 일치, NN `not_yet` 일치.
- 규칙으로 승격한 발견: ① `esr = 適格資本/所要資本` 는 百万円 절사 때문에 소수 첫째자리 반올림으로 안 맞고 구간 [E/(R+1), (E+1)/R] 로만 맞는다.
  ② 리스크 부모(損保·巨大災害·市場)는 Σ하위보다 작다(상관 통합) — 등식 검산 금지. ③ `Tier1 基礎項目 == EBS 純資産`, `EBS 純資産 = 회계 純資産 +
  規制上の準備金 + 経済価値調整額` 이 T2↔T4 교차 게이트. ④ 정성 플래그는 정성 페이지에서만 검색(전체 문서 검색 시 T3 행 라벨 `マネジメント・
  アクションの効果の額` 에 걸려 "적용" 오판 — 실측 후 수정). ⑤ au 는 EBS 빈 행을 생략하므로 미매치 = 0 으로 허용(`ROW_OMITTED`).
- 편차·한계는 티켓 답변란과 문서 §7. MY 3축은 별책에 없어 본편 미열람(로컬 3건 조건). `calc_method=standard_implied` 는 추정.
- `docs/domains/claude-agent-jp.md` §3 에 양식 지도 포인터 1줄 추가.

## 2026-09-12 (5) -- `jp/index.html` ESR 랭킹 ECharts 가로막대 → 루트 모바일 리스트 이식 (designer)

- 티켓 `inbox/designer/20260912T0810Z__owner__JP_MULTI__jesr_jp_page_v3_korean_list.md`. owner 지적 원문 취지: "한국
  insurequant 모바일 리스트(막대) 레이아웃을 그대로 쓰면 되는데 왜 새로 ECharts 막대를 만들었나. 기준 하나 정해서
  그보다 높으면 진한 초록, 낮으면 진한 빨강이 더 직관적이다."
- **삭제**: `#esrChartLife`/`#esrChartNonlife` echarts 컨테이너·CSS(`#esrChartLife, #esrChartNonlife{width:100%}`)·
  `renderChart()` 전체(그리드/축/툴팁/시리즈 옵션, target 삼각 마커 scatter 시리즈 포함)·`chartInst`·`GROUP_COLOR`·
  `isMobile()`·`parseTargetNum()`·`debounce()`·resize 리스너(리스트는 뷰포트 무관 렌더라 불필요, 위 4개 함수는 이
  변경으로 orphan 이 돼 같이 제거).
- **이식**: 루트 `index.html` 82~98행 `.map-list`~`.li-chip` CSS 블록 + 877~948행 `renderList()` + 531~547행
  `_ratioHsl()`/`colorForRatio()` 를 그대로 복사. id 만 jp 스코프로 조정(`esrListLife`/`esrListNonlife`). 원본의
  `#bubble-list .li-name{display:flex}`(칩 병기용 변형)을 jp 의 기본 `.li-name` 규칙으로 채택 — jp 리스트는 速報 칩이
  항상 붙을 수 있어야 하므로.
- **색 상수**: `RATIO_SCALE={esr:{base:100,strong:300}}`. base=일본 금융청 감독기준 100%(미달 시 早期是正措置 대상),
  strong=규제수치 아닌 표시용 끝점(13사 분포 p90≈300 — 루트 kics 색상의 p90 채택과 같은 근거). 상수 옆 2줄 주석으로
  이유 명시(티켓 지시).
- **fold**: FOLD=5 더보기를 `isMob` 조건 없이 데스크톱·모바일 모두 적용(jp 기존 동작 유지 — 원래도 isMob 체크가
  없었다). 生保 9사→top5+더보기, 損保 4사=버튼 없음(≤FOLD). 리스트·표는 `expanded{life,nonlife}` 상태 공유(기존과 동일).
- **인터랙션 제거**: 루트는 행 클릭/`role="link"`/`tabindex`/keydown 으로 K-ICS.html 상세로 이동하지만, jp 에는 상세
  페이지가 없어 이 부분은 이식하지 않음(티켓 명시). `title`/`aria-label` 에는 이전 echarts 툴팁 내용(ESR·範囲·基準日·
  算定基準)을 요약 텍스트로 유지. `.li-row` 의 `cursor:pointer`/`:active` 도 복사하지 않음 — 클릭 동작이 없는데
  포인터 커서를 남기면 오탐 어포던스가 되므로(직접판단, 렌더링되는 수치·레이아웃 변경 아님).
- **▲目標水準 제거**: 리스트에 마커 자리가 없어 표(一覧表) 備考 열에 `目標 190%+`(`target_pct` 그대로) 텍스트로 이관.
- **범례**: 業態 색상 스와치(生保 파랑/損保 주황) 제거 → 감독기준 색 설명 2줄("監督基準100%以上ほど濃い緑"/
  "監督基準100%未満ほど濃い赤")로 교체. 상단 설명 문단도 "色は業態、▲は目標水準" → "色は監督基準(100%)を…" 로 수정.
- **검증**: `python -m http.server 8896`(기존 실행 중) + Claude Browser preview, 데스크톱 1280px·모바일 375px 렌더
  확인(콘솔 에러 0 — jsdelivr `ERR_NETWORK_ACCESS_DENIED` 는 이 PC 크로미움 공통 현상으로 echarts CDN 못 받는 도넛만
  영향, 순수 CSS 인 리스트는 무관). 더보기 클릭 → 生保 9사 전체 펼침 + 표 동시 펼침 확인(DOM 텍스트로 회사 9개 전부
  대조). `scripts/a11y_contrast_check.py contrast "#212529" "#ffffff"` → 15.43:1(AA, `.li-name`/`.li-val`).
  Playwright(headless, CDN 차단 없어 도넛도 렌더) 로 `artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png`
  덮어씀 — 이번엔 실제 막대가 스크린샷에 보임(직전 (4) 의 echarts CDN 차단 문제가 애초에 구조적으로 사라짐).
- Status 아카이브: `TODO_jp.md` Status 최신 5개 유지 원칙에 따라 가장 오래된 (1) FY2025 census 항목을
  `docs/todo_archive_jp.md` 신설 파일로 무수정 이관.

## 2026-09-12 (4) -- `jp/index.html` 2차 개선, owner 실사용 피드백 5건 (designer)

- 티켓 `inbox/designer/20260912T0530Z__owner__JP_MULTI__jesr_jp_page_v2.md`. owner 가 초안(2026-09-12 (2))을 직접 보고
  지적. `jp/jesr_esr.json` 은 publishing 작업(위 (3))으로 이미 13사(부모-자회사 중복 2건 제외) 상태 — 이 페이지에서
  재필터링하지 않고 그대로 fetch.
- **① 정렬 2단 버킷**: `isBucketA(category)` = `/^(HD上場|相互会社|上場)/` 매칭 여부로 버킷A/B 분리, 각 버킷 내
  `esr_pct` desc, `sortBucketed()`. 실측: 生保 9사 전원 버킷A(相互会社/上場/HD上場)라 사실상 esr_pct 단순 desc과 동일하게
  나옴. 損保 4사는 SOMPO/東京海上/MS&AD(버킷A, HD上場) 뒤에 au損害保険(버킷B, `子会社(KDDI)`)이 esr_pct 791.7%로
  압도적 1위임에도 맨 뒤로 밀림 — 의도된 동작(총자산 미공시라 category 로 "주요 시장 플레이어 vs 자회사"를 대신 구분).
- **② sector 별 top5+더보기**: `FOLD=5`, 루트 `index.html` MOB-INDEX-FOLD 패턴(버튼 텍스트만 이 페이지 UI 언어에 맞춰
  일본어 "もっと見る（他N社）"/"閉じる"로 현지화). `groupKey()` 로 reinsurance 를 nonlife 섹션에 합류(현재 0건, 10월
  재census 대비 미리 배선). ESRランキング(차트)·一覧表(표) 두 section 모두 生保/損保 서브섹션으로 재구성, 섹션당 버튼 1개씩
  총 4개지만 `expanded{life,nonlife}` 상태를 공유해 차트/표 어느 버튼을 눌러도 같이 펼쳐짐/접힘. 損保(4사)는 FOLD 이하라
  버튼 자체를 렌더링 안 함(`btn.hidden=true`). **함정 재확인(claude-agent-designer.md §4)**: `.more-btn{display:block}`
  이 특이도 동점으로 UA 기본 `[hidden]{display:none}` 을 이기므로 `.more-btn[hidden]{display:none}` 가드 명시 추가.
- **③ 出所 열 제거 + 공시일자 링크**: 표 헤더 6번째 열을 `出所`→`公表日` 로 교체, 셀 내용을 `doc_type` 텍스트가 아니라
  `jaDateFlexible(doc_date)` 텍스트에 `source_url` 링크(`target="_blank" rel="noopener noreferrer"`, aria-label 에 회사명+
  doc_type(있으면) + "별タブで開く" 유지). `基準日`(as_of) 열은 그대로.
- **④ 연결 시각 인코딩 제거**: ECharts bar `itemStyle.decal`(빗금) 및 범례 `グループ連結` 항목 삭제, `.hatch-sw` CSS 도
  같이 제거(내 편집으로 인한 dead code). `scope` 값은 表 範囲 열(기존 그대로 유지, 원래도 있었음)과 차트 tooltip 신규
  1행(`範囲: 連結/単体`)으로만 텍스트 유지. 차트 bar 색상도 sector 개별색이 아니라 GROUP_COLOR(섹션당 단색, 생보=blue,
  손보=orange)로 단순화 — 섹션 헤더가 이미 業種을 명시하므로 bar 색은 섹션 식별용으로 충분.
- **⑤ 速報 배지**: 무변경.
- 검증: `python -m http.server 8896` + Playwright(`sync_playwright`, chromium) 로 DOM 텍스트·정렬 순서·fold 버튼
  라벨·hidden 상태를 확인(get_page_text 로 生保 top5 순서·損保 4사 全出·표 공표日 링크 텍스트 실측 일치). 콘솔은 이
  세션 진행 중 `cdn.jsdelivr.net`(echarts/pretendard) 이 간헐적으로 `ERR_NETWORK_ACCESS_DENIED` — **jp 페이지만의 결함이
  아님**: 같은 순간 무수정 상태의 루트 `index.html`(같은 CDN 참조)도 동일 에러 재현(`root_verify.py`), 재시도해도 같은
  프로세스 내에서는 지속(브라우저 프로세스 단위로 걸리는 현재 네트워크/보안에이전트 상태로 추정, `project_pc_cannot_push`
  메모리의 "VPN 끄면 외부443 WSAEACCES" 와 정합). ECharts 막대 시각 자체는 이번 세션에서 렌더 확인 불가(canvas count=0,
  `window.echarts===undefined`) — 로직(정렬 리스트→bar/scatter 데이터 변환, aria-label 갱신)은 코드로 확인, 다음 세션
  네트워크 정상화 시 재스크린샷 권장. 데스크톱 1280px·모바일 375px 스크린샷은
  `artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png` 덮어쓰기(레이아웃·표·버튼은 정상 렌더 확인됨).

### 종결 재확인 (orchestrator, 같은 날)

designer 가 "다음 세션 재확인 권장"으로 넘긴 ECharts 렌더를 orchestrator 가 즉시 재검증했다 — echarts.min.js
로컬 임시 사본(검증 후 삭제, `jp/index.html` 은 시종 CDN 참조만 유지, git diff 로 확인)으로 실제 렌더 확인.
2단 정렬(au損害保険 損保 최하단 이동)·top5 폴드·빗금 제거 전부 스크린샷으로 육안 확인. 그 과정에서 **버그 1건 추가
발견·직접수정**: 모바일(375px) 生保 차트 x축 눈금이 값 범위(0~333%)에 눈금 8개가 좁은 폭에 들어차 "50%00%050%060%090%00%"
로 겹쳐 읽을 수 없었음(원인: `xAxis.axisLabel` 에 겹침 방지·모바일 눈금수 조정이 없었음). `hideOverlap:true` +
모바일 `splitNumber:4`(데스크톱 6 유지)로 수정, "0% 100% 200% 300% 400%" 정상 표시로 재확인.
스크린샷 재덮어쓰기(같은 파일명). 티켓 `status: resolved` 로 종결.

## 2026-09-12 (3) -- `jp/jesr_esr.json` 부모-자회사 중복 제거 (publishing)

- 티켓 `inbox/publishing/20260912T0530Z__owner__JP_MULTI__jesr_dedup_parent_subsidiary.md`. owner 실측 지적: 소니생명保険(solo
  162%)의 parent 소니FG(group 177%, posted), 明治安田損害保険(solo 743.2%)의 parent 明治安田生命保険(group 208%, posted) —
  같은 자본이 두 단위(개별법인/그룹연결)로 두 번 랭킹에 올라가 있었음.
- `J-ESR/build_jesr_page_json.py` 에 `apply_subsidiary_dedup()` 추가. 회사명 하드코딩 없이 일반 로직: census `category` 가
  "子会社"로 시작하는 posted 행에 대해, `jp_insurers.csv` 의 `parent_group` 을 다른 posted `company_jp` 안의 (직접 또는
  "HD"→"ホールディングス"/"FG"→"フィナンシャルグループ" 확장) 부분문자열로 매칭 — 걸리면 그 자회사 행을 `jp/jesr_esr.json`
  에서만 제외. `J-ESR/jesr_master.json` 은 15사 전부 그대로(정본).
- self-check 을 "두 파일 바이트 동일" 에서 "master 레코드 수 - 제외 수 == deploy 레코드 수" 로 교체. `_meta.excluded_subsidiaries`
  신설(deploy 파일에만, company_en·parent·esr_pct 3필드, 화면 미사용·감사용).
- 실행 결과: `jesr_master.json` 15 레코드 유지, `jp/jesr_esr.json` 15→13 레코드. 제외 2건 = Sony Life Insurance(parent Sony
  Financial Group) · Meiji Yasuda Non-Life(parent Meiji Yasuda Life Insurance). au Non-Life(parent KDDI, 보험사 아님·미공시)는
  그대로 남음 — 재현: `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_page_json.py`.

## 2026-09-12 -- jp 레인 신설 + FY2025 ESR census 79사 + `/jp/` 초안

- owner 결정 3건: (1) J-ESR 소스 정본은 EDINET 이 아니라 회사별 공시 사이트 PDF(기한 2026-10-31) — 이전 세션 구두 결론이 repo 에 없어
  오케스트레이터가 EDINET 조회를 다시 제안하는 사고 후 재기록. (2) 일본 화면은 IP 차등·`.co.jp` 대신 같은 사이트 `/jp/`. (3) jp 는
  한국 stage 에이전트와 **별개 에이전트**로 부린다(한국 프롬프트 11만 자에 일본 언급 0건 — 비대화 + 규칙 오염).
- census: downloader 에이전트 2개(행 1~41 / 42~81) → `J-ESR/fy2025_esr_census_20260912.csv` 79사, posted 15 / not_yet 62 / not_found 2.
  posted 이상치 2건(au 791.7%·Meiji Yasuda Non-Life 743.2%) 원문 PDF fitz 재확인. `jp_insurers.csv` ir_url 41→2. 커밋 `ca54fca`.
- 초안: publishing 이 `J-ESR/build_jesr_page_json.py` → `J-ESR/jesr_master.json` + `jp/jesr_esr.json`(15사, preliminary 5), designer 가
  `jp/index.html`(일본어 UI, 요약 카드·ESR 랭킹 막대·커버리지 도넛·출처 표·hreflang). 기존 4페이지 무수정.
- 레인 뼈대: `docs/domains/claude-agent-jp.md`, `TODO_jp.md`, 이 파일, `inbox/jp/`, `.claude/agents/jp-collector.md`(로컬).
  `CLAUDE.md` 는 같은 날 룰만 남기고 202→94줄로 축약(전문은 `docs/claude-md-history.md`).

## 2026-09-01 -- 9월 말 킥오프 확정 (owner)

인스뉴스 기사(일본 금융청 2026 보험 모니터링 보고서) 계기. 상세 루트 `TODO.md` J-ESR 항목.

## 2026-07-21 -- MVP 페이지 revert (`167cba1`)

그룹 연결값 11사뿐이라 화면 보류(owner). 근거 메모리 `project_jesr_scope_timing`.

## 2026-06-24 -- 트랙 신설 (당시 downloader/parser 가 처리)

`docs/changelog_downloader.md` 2026-06-24 항목 2건 · `inbox/_resolved/2026062*__*jesr*` 8건.
