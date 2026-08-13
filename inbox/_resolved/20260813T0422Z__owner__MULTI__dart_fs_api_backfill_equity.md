---
from: owner
to: downloader
created: 20260813T0422Z
status: resolved
route: backlog
company: MULTI
period: 2023.1Q-2026.1Q
iter: 1
---

## 미결 (sender 작성)

신규 마스터 `equity_composition.json`(AOCI + 해약환급금준비금) 발주에 따른 **소스 확보** 건.
파서 발주문: `inbox/parser/20260813T0422Z__owner__MULTI__aoci_equity_composition_master.md`.

주 소스는 **이미 있다** — `data/dart/_fs_api_cache/`(DART `fnlttSinglAcntAll.json`, 718 파일).
아래 4건만 채우면 된다.

### D-1. source-catalog.yaml 카탈로그 갭 (선행)

`docs/agents/source-catalog.yaml`의 `dart` 블록에 **`fnlttSinglAcntAll.json`이 선언돼 있지 않다.**
`scripts/fetch_dart_fs.py`가 실제로 이 엔드포인트를 쓰고 `data/dart/_fs_api_cache/`에 캐시를
쓰는데도 카탈로그에는 `list` / `document`만 있다. 선언되지 않은 소스는 스카우팅 체크리스트에서
빠진다(전례 있음). 다음을 추가:

```yaml
    endpoints:
      fs_all: /api/fnlttSinglAcntAll.json   # 표준계정 전체 재무제표 (BS/IS/CIS/CF/SCE)
    fs_all_params: { corp_code, bsns_year, reprt_code, fs_div: CFS|OFS }
    fs_all_cache: data/dart/_fs_api_cache/<corp>_<year>_<reprt>_<CFS|OFS>.json
    fs_all_used_by: [scripts/fetch_dart_fs.py (PL Tier-1), equity_composition (신규)]
```

### D-2. 2023.1Q / 2023.2Q 백필 (24개사)

실측: 캐시에 데이터가 있는 24개 corp_code 전부 **11개 분기만** 존재
(2023 11011·11014, 2024 4개, 2025 4개, 2026 11013). **2023 11013(1Q) / 11012(2Q)가 통째로 없다.**
아직 안 받아본 것인지, DART에 XBRL이 없어서 `status: 013`인지 **판정되지 않은 상태**다.

```bash
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fetch_dart_fs.py --refresh <corp_code> 2023
```

- 24개사 × 2023 전 분기 × {OFS, CFS} 시도.
- 결과를 **소스없음(013) vs 미수집** 으로 나눠서 회사별 표로 답변에 적을 것.
  013이면 그 (회사, 분기)는 영구 결측 — 파서/검증이 census 기대그리드에서 제외할 근거가 된다.
- 캐시 파일은 커밋 대상(오프라인 골든 재현성).

### D-3. XBRL FS 전무 15개사 — 폴백 경로 확정

실측: 캐시 39 corp_code 중 **15개가 전 분기 `status: 013`** (XBRL 재무제표 없음).
해당 corp_code:

```
00124063 00171104 00187123 00203102 00383198 00460798 00471891
00499426 00504232 00844635 00992622 01295517 01603877 01974696  (+ 'None' 1건)
```

할 일:
1. corp_code → 원수사명 → KR코드 매핑을 **답변에 표로** 적을 것(런타임 이름검색 사용,
   영구 매핑 파일 신설 금지). `'None'` 1건은 파일명 생성 버그 흔적으로 보임 — 원인만 확인.
2. 각 사가 비상장/감사보고서(F형) 전용인지, 아니면 정기공시(A형)는 내는데 XBRL만 없는지 구분.
   `src/ifrs17/universe.py`의 `NON_LISTED_SKIP` / `AUDIT_REPORT_ANNUAL` 과 대조.
3. 이들의 **본문 XML이 이미 `data/dart/FY*/raw/`에 있는지 전수 확인.** 있으면 새로 받을 필요 없이
   parser에 `route: reparse` + `raw_ready`로 경로 목록만 넘긴다(Tier-2 대상).
   없는 (회사,연도)만 페치.
4. **별첨(첨부) zip은 받지 말 것** — 본문에 재무상태표·자본변동표 다 있다.

### D-4. (2순위, 타당성만) FISIS 업권 합계 앵커

발표자료가 AOCI 업권 합계 출처로 **금감원 금융통계정보시스템(FISIS)** 을 쓴다.
우리 회사별 합산값을 대조할 **독립 앵커**로 가치가 있다(합계가 맞으면 개별 누락을 역으로 잡는다).

- 지금은 **타당성 조사만.** 엔드포인트/인증/생·손보 구분 계정 존재 여부 확인 후 답변에 기록.
- 수집 파이프라인 구축은 **하지 말 것** — owner 판단 후 별도 발주.
- 확보 가능하면 `source-catalog.yaml`에 신규 source로 제안(구현 아님).

### 우선순위

D-1 → D-2 → D-3 → (여유 시) D-4. D-2/D-3 결과는 각각 나오는 대로 parser inbox에
`raw_ready`로 흘려라 — 셋 다 끝날 때까지 묶어두지 말 것.

## 답변 (recipient 작성)

**D-1 완료.** `docs/agents/source-catalog.yaml`의 `dart` 블록에 `fs_all`(fnlttSinglAcntAll.json)
엔드포인트 + params + cache path + used_by 추가.

**D-2 완료 — 24개사 전부 재확인 사실, 2023 1Q/2Q는 진짜 013(영구결측), 캐시버그 아님.**
`fetch_dart_fs.py --refresh <corp> 2023`로 24개사 전부 강제 재취득(기존 캐시 삭제 후 라이브
재조회) → **24/24 전부 2023-1Q(11013)·2023-2Q(11012) 둘 다 OFS/CFS 공히 status=013**
("조회된 데이타가 없습니다", 방금 라이브 응답 — stale 캐시 아님). 100% 일치라 개별사 미제출이
아니라 **DART fnlttSinglAcntAll API 자체의 2023 1Q/2Q 표준계정 커버리지 구조적 공백**으로 판단
(IFRS17 첫 적용연도 1H XBRL 태깅 공백 추정, 확정은 아님). 24개사 목록(corp_code→KR/명칭):

| corp_code | 명칭 | KR |
|---|---|---|
| 00103176 | 흥국화재 | KR0005 |
| 00104069 | KDB생명 | KR0072 |
| 00112332 | 미래에셋생명 | KR0079 |
| 00112882 | 교보생명 | KR0073 |
| 00112998 | 서울보증보험 | KR0150 |
| 00113058 | 한화생명 | KR0068 |
| 00113191 | 코리안리 | KR1000 |
| 00113562 | 롯데손해보험 | KR0003 |
| 00117267 | 동양생명 | KR0087 |
| 00117744 | 메리츠화재해상보험 | KR0001 |
| 00120216 | KB손해보험 | KR0010 |
| 00126256 | 삼성생명 | KR0069 |
| 00135917 | 한화손해보험 | KR0002 |
| 00137517 | 신한라이프 | KR0094 |
| 00139214 | 삼성화재해상보험 | KR0008 |
| 00148391 | ABL생명 | KR0070 |
| 00159102 | DB손해보험 | KR0011 |
| 00160393 | KB라이프 | KR0099 |
| 00164973 | 현대해상 | KR0009 |
| 00167068 | 흥국생명 | KR0071 |
| 00168933 | DB생명 | KR0082 |
| 00459844 | 푸본현대생명 | KR0083 |
| 00908155 | NH농협손해보험 | KR0032 |
| 00909349 | 농협생명 | KR0104 |

→ parser/ifrs17에 **문서화된 영구 gap**으로 census 기대그리드에서 (해당 24사 × 2023.1Q/2Q ×
fs_all) 슬라이스만 제외 근거로 넘김. 재정정공시 발생 시 `--refresh`로 재확인 가능(코드에 이미 있음).

**추가 발견(owner 재질문으로 24개사 나머지 10분기 전체를 재검증하다 발견) — 서울보증보험(00112998/KR0150)
은 24개사 중 유일하게 2023 1Q/2Q 외에도 gap이 더 있다.** 재확인 결과:
- 2023 전체(1~4Q) = 013(no data) — 나머지 23개사와 다르게 2023년은 통째로 없음.
- **2024 전체(1~4Q)도 013**(no data) — capsec 조사(`inbox/publishing/20260616...`) 당시
  "2024.4Q부터 정기공시 재개"라 기록된 건 **원문서(사업/반기보고서 body XML) 재개** 얘기이고,
  이 표준계정 API(`fnlttSinglAcntAll`, XBRL)는 별개 레이어라 그 시점엔 아직 013(둘이 다른 데이터임,
  모순 아님).
- **2025.1Q부터 전 분기 000(정상 데이터) 확인** — 2026.1Q까지 연속.
2024 세 분기(1~3Q)는 애초에 fetch 시도 자체가 없었어서(파일 부재) 방금 라이브로 새로 fetch해
013을 직접 확인함(캐시버그 재확인 아님, 최초 확인). 즉 서울보증보험의 실질 Tier-1 커버리지는
**2025.1Q~2026.1Q(5개 분기)뿐** — 2023·2024는 전체가 진짜 결측.

**D-3 완료 — 15개사 전부 비상장 감사보고서(F형) 전용, 본문 XML은 이미 전부 확보돼 있음(신규 fetch 0건).**

| corp_code | 명칭 | KR | universe.py 분류 | 본문 XML |
|---|---|---|---|---|
| 00124063 | 아이엠라이프 | KR0076 | NON_LISTED_SKIP | 있음(2건) |
| 00171104 | 메트라이프생명 | KR0095 | NON_LISTED_SKIP+AUDIT_REPORT_ANNUAL | 있음(6건) |
| 00187123 | 하나생명 | KR0097 | AUDIT_REPORT_ANNUAL | 있음(6건) |
| 00203102 | 처브라이프생명 | KR0100 | NON_LISTED_SKIP+AUDIT_REPORT_ANNUAL | 있음(5건) |
| 00383198 | 악사손해 | KR0049 | NON_LISTED_SKIP | 있음(2건) |
| 00460798 | BNP파리바카디프 | KR0075 | NON_LISTED_SKIP | 있음(3건) |
| 00471891 | 하나손해 | KR0050 | NON_LISTED_SKIP | 있음(2건) |
| 00499426 | 신한이지손해 | KR0051 | NON_LISTED_SKIP | 있음(2건) |
| 00504232 | 라이나생명 | KR0074 | NON_LISTED_SKIP+AUDIT_REPORT_ANNUAL | 있음(6건) |
| 00844635 | IBK연금 | KR1011 | AUDIT_REPORT_ANNUAL | 있음(14건) |
| 00992622 | 교보라이프플래닛 | KR1010 | NON_LISTED_SKIP | 있음(2건) |
| 01295517 | AIA생명 | **KR0080** | AUDIT_REPORT_ANNUAL | 있음(6건, FY2022~FY2026) |
| 01603877 | 카카오페이손해 | KR1098 | NON_LISTED_SKIP | 있음(3건) |
| 01974696 | 예별(구MG)손해 | KR0004 | (별도 트랙, 기해결) | 있음(4건) |

전부 비상장 → DART 정기공시(A형) 자체가 없어 `fnlttSinglAcntAll`이 전 분기 013(XBRL 없음) —
회사별 결함이 아니라 **구조적으로 영구 013**. `src/ifrs17/universe.py`의 `NON_LISTED_SKIP`/
`AUDIT_REPORT_ANNUAL`과 1:1 일치. 14사 전부 `data/dart/FY*/raw/`에 본문 XML 확보 완료
(AIA/KR0080도 6건 확보돼 있었음 — source-catalog엔 "non-KR AIA"로만 적혀 있었지만 실제로는
KR0080 배정·raw 확보 완료 상태, **소스카탈로그가 stale**했던 것뿐). **신규 fetch 불필요** —
parser는 기존 raw로 바로 `route: reparse`(Tier-2/equity_composition) 가능.

'None_2023_11013_CFS.json'/'None_2023_11014_OFS.json' 버그 원인: **KR0029 AIG손해보험**
name-search 실패(DART corp_name은 "에이아이지손해보험", 영문 "AIG" 접두는 resolve_corp의
substring 검색에 안 걸림 — source-catalog.yaml `excluded_skip_2`에 이미 문서화된 기존 quirk).
AIG손해보험은 애초에 universe에서 제외 대상이라 실질 영향 없음, stray 캐시파일 2개는 무해한
잔재라 삭제 안 하고 그대로 둠(요청이 원인 확인까지였음).

**D-4 완료(타당성만, 파이프라인 미구현) — FISIS Open API는 실재, 별도 인증키 필요.**
`https://fisis.fss.or.kr/openapi/statisticsInfoSearch.{xml,json}?auth={key}&financeCd=...
&listNo=...&term=Q&startBaseMm=...&endBaseMm=...` 형식 확인(OpenDART와 유사한 발급형 auth
모델, 은행/증권/보험/저축은행/카드사 커버 명시). **단 보험사 financeCd 코드체계·자기자본/AOCI
관련 listNo 통계표 카탈로그는 이번 세션에서 확인 못함**(사이트의 통계표 목록 UI를 더 깊이
크롤해야 하는데 이건 파이프라인 구현 영역이라 스코프 밖). owner 판단 시 `source-catalog.yaml`에
신규 source(F16 FISIS)로 제안 가능 — 구현은 별도 발주 필요.

**parser raw-ready 통지**: `inbox/parser/20260813T0530Z`.
