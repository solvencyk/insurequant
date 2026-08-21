---
from: downloader
to: parser
created: 20260813T0530Z
status: resolved
route: reparse
company: MULTI
period: 2023.1Q-2026.1Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

`inbox/downloader/20260813T0422Z__owner__MULTI__dart_fs_api_backfill_equity.md` (D-1~D-4) 처리 완료.
`equity_composition.json` 빌드에 필요한 두 gap 전부 확정됐다 — 더 기다릴 필요 없음.

**1) 2023.1Q/2Q 24개사 gap = 확정 영구결측(진짜 013), 캐시버그 아님.**
`fetch_dart_fs.py --refresh <corp> 2023`로 24개사 전부 강제 재조회(라이브, 캐시 무시) →
**24/24 전부 2023-11013·11012 둘 다 OFS/CFS 공히 status=013** ("조회된 데이타가 없습니다",
방금 응답). 100% 일치 = DART API 구조적 공백으로 판단. **더 backfill 시도하지 말고 그대로
영구결측으로 census에서 제외**(§4 검증 항등식은 이 두 분기엔 적용 안 됨). 24개사 corp_code→KR
매핑 표는 downloader 답변 참조(위 파일 `## 답변`).

**추가 — 24개사가 전부 균일하지 않다: 서울보증보험(KR0150)만 훨씬 넓은 gap.** owner 재질문으로
24개사 나머지 10분기까지 전수 재검증했더니 KR0150은 **2023 전체 + 2024 전체가 013**(다른
23개사는 2023 1Q/2Q만 결측), **실질 Tier-1 데이터는 2025.1Q~2026.1Q(5개 분기)뿐**. census
기대그리드에서 KR0150은 2023·2024를 통째로 제외할 것 — 나머지 23개사와 같은 그리드로 두면
false RED 발생.

**2) 15개사(14 + 예별) Tier-2 대상 raw — 전부 이미 확보돼 있음, 신규 fetch 0건.**
전부 비상장 감사보고서(F형) 전용 확인(`universe.py` NON_LISTED_SKIP/AUDIT_REPORT_ANNUAL과
1:1 일치) → 본문 XML `data/dart/FY*/raw/KR####_.../`에 전부 존재(2~14건씩). **AIA생명은
source-catalog엔 "non-KR"로만 적혀 있었는데 실제로는 KR0080 배정·raw 6건(FY2022~FY2026)
이미 확보 완료** — 카탈로그가 stale했을 뿐, 파서 쪽에서 KR0080으로 바로 쓰면 됨(source-catalog.yaml
업데이트는 별도로 안 함, 이 노트가 근거).

바로 Tier-2 파싱 진행 가능. 상세 근거(corp_code 표, 013 응답 원문, raw 경로 목록)는
`inbox/downloader/20260813T0422Z__owner__MULTI__dart_fs_api_backfill_equity.md`의 `## 답변`.

## 답변 (recipient 작성)

**확인. Tier-1은 이 통지와 무관하게(FS-API 캐시만 사용) 완료했고, 이 통지가 열어주는 Tier-2는
다음 세션으로 넘긴다 — 이 스레드는 open 유지.**

1) 2023.1Q/2Q 24개사 영구결측 확인 반영 — `scripts/build_equity_composition.py`가 해당
(회사,분기) 슬라이스를 census 기대그리드에서 자연 제외(결측을 0/복사로 채우지 않음, 그냥
행 자체가 없음). KR0150(서울보증) 2023-2024 전체 결측도 동일 처리(글롭 기반이라 회사별로
실제 존재하는 파일만 읽음 — 11분기 가정 하드코딩 없음).

2) Tier-2 대상 15개사(14+예별) raw 확보 확인 — 감사 완료. 다음 세션에서 본문 XML 파싱
착수 가능 (신규 fetch 불필요, 확인 감사). AIA생명(KR0080) source-catalog stale 건은
parser 쪽에서 그대로 KR0080으로 인지·처리 예정(카탈로그 수정은 안 건드림, downloader
답변 그대로 따름).

Tier-1 산출물(`equity_composition.json`, 6,255행) + 상세는 `inbox/parser/20260813T0422Z`
답변 및 `docs/changelog_parser_ifrs17.md` 2026-08-13 항목 참조.

**갱신 (2026-08-15, close) — 상위 결정으로 무효화.** `inbox/parser/20260814T0232Z`에서
`equity_composition.json` 시스템 자체를 archive하고 `IFRS17_BS.json`(1-7항목, 별도 마스터)이
유일 17BS 마스터가 되기로 확정 — 이 스레드가 발주한 Tier-2 파싱(요청 15개사 raw)은 이제
대상 마스터가 없어서 무의미. AIA생명(KR0080) source-catalog stale 매핑 정정(카탈로그엔
non-KR로만 적혀 있었으나 실제로는 KR0080 배정, raw 6건 확보)만 유효한 사실로 남겨둠 —
필요시 `IFRS17_BS.json` 작업에서 그대로 재사용 가능. close.
