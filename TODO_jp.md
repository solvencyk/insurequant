# Insurequant TODO — jp 레인 (일본 ESR)

> Last updated: 2026-09-12 · 도메인 문서: `docs/domains/claude-agent-jp.md` · Changelog: `docs/changelog_jp.md` · inbox: `inbox/jp/`
> Status 는 최신 5개만 유지, 밀린 항목은 [`docs/todo_archive_jp.md`](docs/todo_archive_jp.md) 로(무수정).

## Status

**🟢 2026-09-12 (6) ESR 규제 공시 양식 지도 + 기계 스키마 + 표본값(10월 62사 대비) — 두 층(esr / article_axes).**
티켓 `inbox/jp/20260912T0905Z__owner__JP_MULTI__esr_disclosure_template_map.md`(answered). 로컬 표본 3건(au Non-Life 31p·Meiji Yasuda
Non-Life 별책 14p·NN Life 95p, 전부 텍스트 PDF)을 fitz 로 해부. 산출 (A) `docs/domains/jp_esr_disclosure_template.md`(양식 구조 T1~T8·항목 표
131행·검산식·추출 규칙·K-ICS 대응·회사별 편차) (B) `J-ESR/esr_disclosure_schema.json`(items 131 = esr 109 + article_axes 22, `kics_item_ref`
27개만 대응·근사 사유 문서 §6) (C) `J-ESR/raw/fy2025_samples/extracted_sample_values.json` + 생성기 `J-ESR/extract_esr_template_samples.py`
(exit 0). 검산 au 34/34·MY 41/41·NN 4/4, census 헤드라인 791.7/743.2 일치, NN `not_yet` 일치. 핵심 발견: ESR 비율은 百万円 절사라
**구간 검산**만 맞음(au 점추정 792.31 vs 공시 791.7); 리스크 부모 ≤ Σ하위(상관 통합, 등식 아님); `Tier1 基礎項目 == EBS 純資産` 등 T2↔T4 교차
6건 일치; 경과조치 표는 양식에 없음; au 는 EBS 빈 행 생략·민감도 값 생략(1%p 미만 주기). 3축: au 異常危険準備金 2,222 = EBS 規制上の準備金,
NN Life 逆ざや 37億円(단위 億円)→negative·三利源 없음·AIR 키워드 0(정황 2건 `air_evidence`), MY 3축은 별책에 없어 본편 필요. **10월 census
확장 열 이름 = 스키마 id.** 생보 `生命保険リスク` 하위행은 표본 없어 미등록(발견 즉시 `rc_life_*` 추가).

**🟢 2026-09-12 (5) `jp/index.html` ESR 랭킹 ECharts 가로막대 폐기 → 루트 `index.html` 모바일 리스트 그대로 이식(designer).**
티켓 `inbox/designer/20260912T0810Z__owner__JP_MULTI__jesr_jp_page_v3_korean_list.md`(answered). owner 지적: "한국 사이트
모바일 리스트 레이아웃을 그대로 쓰면 되는데 새로 ECharts 막대를 만들었다" → `#esrChartLife/Nonlife`(echarts bar) 전부
삭제, 루트 `index.html` 82~98행 `.map-list`~`.li-chip` CSS + 877~948행 `renderList()` + 531~547행
`_ratioHsl`/`colorForRatio` 를 그대로 복사해 `esrListLife`/`esrListNonlife` 로 이식. 색 상수만
`RATIO_SCALE={esr:{base:100,strong:300}}`(base=일본 금융청 감독기준 100%, strong=13사 분포 p90 표시 끝점). 데스크톱·모바일
모두 리스트(jp 는 트리맵이 없어 `.map-list{display:block}` 로 상시 표시), top5+더보기(FOLD=5, `isMob` 조건 없이 데스크톱도
적용 — 기존 jp 동작 유지) · 生保/損保 2섹션 · 速報 는 `.li-chip` 로 이름 옆에 이동. 행 클릭/role="link"/keydown 은 뺐다(jp
에 상세 페이지 없음, 티켓 지시) — `title`/`aria-label` 요약 텍스트만 유지. ▲目標水準 마커 제거, 表 備考열에
`目標 190%+` 텍스트로 이관(`target_pct`). 업태색 범례(生保/損保 스와치) 제거 → 감독기준 색 설명으로 교체. 편차 1건:
`.li-row` 의 `cursor:pointer`/`:active` 는 복사하지 않음(클릭 없는데 포인터 커서면 오탐 어포던스 — a11y 관점 직접판단,
값 변경 아닌 어포던스 수정). 정리(orphan 제거): `chartInst`/`GROUP_COLOR`/`isMobile()`/`parseTargetNum()`/`debounce()`
+ resize 리스너(리스트는 뷰포트 무관 렌더라 불필요). 검증: `python -m http.server 8896`(기존 실행 중) +
Claude Browser preview 로 데스크톱 1280px·모바일 375px 렌더 확인(콘솔 에러 0, jsdelivr `ERR_NETWORK_ACCESS_DENIED`
는 이 PC 크로미움 공통 현상— echarts CDN 못 받는 도넛만 영향, 순수 CSS 인 리스트는 무관하게 정상 렌더됨 확인),
더보기 클릭 → 9사 전체 펼침 + 표 동시 펼침 확인. `scripts/a11y_contrast_check.py contrast "#212529" "#ffffff"` →
15.43:1(AA 통과, `.li-name`/`.li-val` 글자색). Playwright(`C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`,
headless는 CDN 차단 없어 도넛도 렌더됨)로 최종 스크린샷 `artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png`
덮어씀(재현: 로컬 스크립트로 1280×1400 / 375×900 viewport full-page capture).

**🟢 2026-09-12 (4) `jp/index.html` 2차 개선 — owner 지적 5건 반영(designer) + orchestrator 재검증·버그 1건 직접수정.**
티켓 `inbox/_resolved/20260912T0530Z__owner__JP_MULTI__jesr_jp_page_v2.md`(resolved). ① category 2단 버킷 정렬
(`HD上場`/`相互会社`/`上場` 선두 vs 그 외, 각 버킷 내 `esr_pct` desc — au損害保険 791.7%가 손보 최하단으로 이동)
② sector 별 top5+더보기(生保 9사→top5+4, 損保 4사=버튼 없음, reinsurance는 損保에 합류) ③ 表의 出所 열 제거 →
公表日 텍스트에 `source_url` 링크 ④ 막대차트 빗금(연결) 인코딩·범례 항목 제거, `scope` 는 表·툴팁 텍스트로만
⑤ 速報 배지 그대로. designer 세션은 Playwright 캡처가 cdn.jsdelivr.net `ERR_NETWORK_ACCESS_DENIED`(이 PC 크로미움
공통 현상)로 차트가 빈 화면으로 찍혀 "다음 세션 재확인 권장"으로 넘겼는데, **orchestrator 가 즉시 재검증**함:
echarts 로컬 임시 사본(검증 후 삭제, `jp/index.html`은 CDN 참조만 유지)으로 실제 렌더 확인 — 2단 정렬·top5 폴드·
au 최하단 이동·빗금 제거 전부 스크린샷으로 확인됨. 그 과정에서 **버그 1건 추가 발견·직접수정**: 모바일(375px)
생명보험 차트 x축 눈금이 "50%00%050%060%090%00%" 로 겹쳐 읽을 수 없었음 → `xAxis.axisLabel.hideOverlap:true` +
모바일 `splitNumber:4`(데스크톱 6)로 수정, "0% 100% 200% 300% 400%" 정상 표시 확인. 최종 스크린샷
`artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png`(덮어씀).

**🟢 2026-09-12 (3) `jp/jesr_esr.json` 부모-자회사 중복 제거 — 15→13 레코드(publishing).**
티켓 `inbox/publishing/20260912T0530Z__owner__JP_MULTI__jesr_dedup_parent_subsidiary.md`. 소니생명保険(parent 소니FG)·明治安田損害保険
(parent 明治安田生命保険) 제외, au損害保険(parent KDDI, 미공시)은 유지. `J-ESR/build_jesr_page_json.py` 에 회사명 비하드코딩 일반 로직
(`jp_insurers.csv` `parent_group` 조인) 추가. `J-ESR/jesr_master.json` 은 15사 그대로. 재현:
`PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_page_json.py`.

**🟢 2026-09-12 (2) `/jp/` 일본어 페이지 초안 — 데이터 `jp/jesr_esr.json`(15사, publishing) + `jp/index.html`(designer).**
티켓 `inbox/_resolved/20260912T0446Z__owner__JP_MULTI__jesr_page_json.md` · `..._jesr_jp_page_draft.md`. owner 결정: IP 차등·`.co.jp` 대신
같은 사이트 `/jp/` 경로(나중에 `jp.insurequant.com` 승격 가능). 라이브 반영은 owner 가 초안을 본 뒤.

## Active follow-ups

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
