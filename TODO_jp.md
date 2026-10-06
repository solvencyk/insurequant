# Insurequant TODO — jp 레인 (일본 ESR)

> 갱신 2026-10-07 · 도메인 문서 `docs/domains/claude-agent-jp.md` · 이력 `docs/changelog_jp.md` · inbox `inbox/jp/`
> 2026-10-07 정리 전 전문((31)~(35) Status 포함)은 `docs/todo_archive_jp.md` 맨 위에 있다. 한국 stage 프롬프트는 읽지 않는다.

## Status (최신 3개)

- **2026-09-15 (35) F조 출처 교체 — 손보 貸借対照表 29/31사.** あいおいニッセイ同和는 자사 ディスクロージャー資料 법정 계산서류로 싣고
  (有報와 BS 16행·PL 18행 일치), MS&AD HD 는 지주 単体라 보험 BS 가 아니어서 비웠다. ソニー損保는 Akamai 403 으로 원문을 못 열어 싣지 않았다.
- **2026-09-15 (34) 남은 10사 2차 — 貸借対照表 21 → 28사.** 5열 구성비 표·완전괄호(내역 표기) 함정 해결, 커밋된 21사 완전괄호 감사 결과 오염 없음.
- **2026-09-15 (33) 손보 법정 BS/PL 추출 — 貸借対照表 5 → 21사.** PL 페이지를 표제가 아니라 값(`正味収入保険料` 전기·당기 쌍)으로 앵커링, 검증 4축.

## 열린 일

- [ ] **10월 말 재census**(2026-10-31 기한 직후) — 같은 csv 열로 79사 재조회. 패턴 기반 잠정 행부터, `preliminary` 5사(LifeNet·Asahi·Fukoku·Japan Post·Sumitomo) 교체.
  **같은 라운드에 열 5개 추가**(owner 2026-09-12 확정): `air_used` · `catastrophe_reserve_adequacy`(생보 해당없음) · `interest_margin_sign`
  · `calc_method`(standard/internal_model/unstated) · `confidence_level`. 생보 AIR·이차손익 서술은 결산설명자료의 다른 섹션이라 놓치기 쉽다.
- [ ] **census 선행 절차** — `python J-ESR/check_source_urls.py --all` 먼저(2026-09-13 기준 blocked 21 · spa_shell 8 · requires_headers 17 은 헤더 없이 돌리면 전부 `not_found` 오탐).
  dead 5건 대체 URL(朝日生命·キャピタル損害保険·オリックス生命·日本生命 ir_health_url).
- [ ] **10월 有報 재스캔** — `jesr_edinet_fetch.py --scan --from 2026-10-01 --to 2026-11-30 --doc-types 130,140` 후 `edinet_esr_probe.py` 재대조.
- [ ] **사람이 브라우저로 열 것** — 大同火災(WAF 403) · ソニー損保(Akamai 403, 후보 URL `from.sonysonpo.co.jp/company/news/docs/2026/20260514.pdf`). 연 뒤 병합.
- [ ] **`edinet_code_match.json`** — 第一ネオ生命·第一アイペット損保·大樹生命 행의 `agrees_with_record`/`matched` 를 2026-09-16 결론으로 채운다.
- [ ] `jp_insurers.csv` 완전 중복 2행 정리 · not_found 2사(Meiji Yasuda Trust Life·Yamap) 공시 페이지 재탐색.

## owner 판단 대기

- `/jp/` 공개 전환(현재 비공개 프리뷰 `jp-f9027362/`, noindex). 체크리스트: ① `JP_PRIVATE_DIR=""` ② 그 라운드 main 에서 `git rm -r jp-f9027362`
  ③ `jp/*.html` noindex 제거·robots/sitemap 등재 ④ 루트 index.html hreflang·언어전환 ⑤ Cloudflare Access 는 유료 인증이 필요해질 때.
  라이브 반영 시 배포 keep-list 가 4페이지 하드코딩(3곳)이라 목록화가 필요하다.
- 3축(AIR·이상위험준비금·이차손익)을 화면에 올릴지 — 10월 말 데이터가 얼마나 뽑히는지 본 뒤 묻는다.
- 일본 손보 「引受 vs 運用」 축 — `pl_underwriting_profit`/`pl_investment_pl` 이 5~6사뿐이라 수집 타깃으로 넘김(designer 2026-09-22 메모).
