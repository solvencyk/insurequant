# PM-2026-09-13 — jp 레인 ESR 2건이 2차보도·조정치 기반으로 화면에 올라갔고, 출처 URL 은 다른 문서였다

> 상태: `open` (5칸은 다 찼으나 3번이 **미배선** — 후속 티켓 발주 상태)
> 발견 경로: 타 세션 리허설(출처 URL 생존 점검) → 이 세션에서 원문 대조로 확대
> 관련 inbox: `inbox/_resolved/20260913T1325Z__owner__JP_MULTI__source_url_rehearsal_and_edinet_key.md` ·
> 후속 `inbox/jp/20260913T1500Z__validation__JP_MULTI__jp_source_gate_wiring.md` · 관련 커밋: `04f27f7`

## 0. 사실관계 (blameless)

2026-09-12 census 로 `/jp/` 랭킹 15사가 화면에 올라갔다. 2026-09-13 에 1차 출처 URL 을 전수 두드려
보니 5건이 실패(404 3 · 403 2)했고, 그 5건을 고치려 원문을 직접 열어 본 결과 **URL 뿐 아니라 값도**
틀어져 있었다.

| 회사 | 화면값 | 원문 실측 | 무슨 일이었나 |
|---|---|---|---|
| 東京海上HD | 238% | **268%** | 238% 는 어느 1차 문서에도 없다. 決算プレゼン p5·p44 와 有報 S100YLS8 본문이 모두 268%(自己株取得 반영 255%, 사업계획 리스크테이크까지 234%). census notes 에 "동종사 결산비교 **보도**에서 동일 수치 반복 인용되어 corroborate" 라고 적혀 있었다 — 2차보도끼리의 상호인용을 검증으로 읽었다 |
| かんぽ生命 | 220% | **181%** | 220% 는 「大量解約リスクを除いた場合」의 **조정치**다. 같은 자료 p35·p37 과 有報 S100YD29 가 모두 181%(監査未済 暫定). notes 에 "特定条件を除いた場合の ESR は 220%" 라고 **스스로 적어 놓고** 그 값을 헤드라인으로 썼다 |
| MS&AD | 214% | 214%(일치) | 값은 맞지만 `source_url` 이 2026-02-13 **三井住友海上·あいおいニッセイ同和 합병 보도자료**였다(ESR 한 줄도 없음). 기본 fetcher 에 403 이라 아무도 열어본 적이 없다 |

영향 범위: `/jp/` 랭킹(비공개 프리뷰 경로 `jp-f9027362/`) 15사 중 3사 · 라이브 노출 **있음**
(noindex·미링크 상태). 한국 파이프라인 영향 없음.

---

## 1. 무엇이 통과했나 (어떤 게이트가 왜 못 잡았나)

- 통과 당시 게이트 상태: `build_jesr_page_json.py` self-check **전부 통과**
  (15사 · esr_pct 100~1000% 범위 · source_url https · as_of 일치 · census 합계 79=15+62+2).
  jp 레인은 `prepush_check.py` 대상이 아니다(CLAUDE.md §5 의 jp 범위 = `test_deploy_assets` + inbox 위생).
- **못 잡은 이유**: self-check 가 전부 **자기참조**다. 값의 범위·형식·합계는 census 안에서 닫히고,
  **census 밖(원문 문서)과 대조하는 축이 아예 없다.** 238% 도 220% 도 100~1000% 안이고, 죽은 URL 도
  `https://` 로 시작하며, 2차보도 URL 도 형식은 완벽하다.

> false-green 메커니즘 한 문장: **출처가 살아 있는지도, 그 문서 안에 그 숫자가 있는지도 검사하지 않으므로,
> 형식만 맞으면 어떤 출처에서 온 어떤 숫자든 통과한다.**

유형 대조(SKILL 표): 기존 5유형 중 **"산술만 검사"(PM-2026-06-16)의 jp 판**이다 — 틀린 소스에서 온
숫자끼리도 형식·범위·합계는 닫힌다. 새 유형이 아니라 **같은 뿌리가 새 도메인에서 재발**했다.

## 2. 어떤 룰이었으면 잡았나 (구체 룰 정의)

| 항목 | 내용 |
|---|---|
| 룰 id | `JP_SOURCE_URL_DEAD` |
| 입력 | census csv 의 `fy2025_esr_status == "posted"` 행 × `source_url` |
| 판정식 | `jesr_http.probe(url).classification == "dead"` (404/410) |
| 임계값 | 없음(1건이면 RED) |
| severity | **RED**(차단) |
| 오탐 억제 | `ok_requires_headers`(봇차단·헤더 붙이면 200) · `blocked`(WAF 4xx) · `tls_client_issue`(파이썬만 실패, curl 200) 는 **통과**. 이 세 가지를 dead 와 섞으면 멀쩡한 회사가 RED 로 쏟아진다(2026-09-13 실측: 전수 254건 중 blocked 21·requires_headers 17·tls 4). meta refresh 는 2홉 추적 후 판정 |

| 항목 | 내용 |
|---|---|
| 룰 id | `JP_SOURCE_EXPIRING_HOST` |
| 입력 | 같은 행의 `source_url` netloc |
| 판정식 | `netloc in jesr_http.EXPIRING_HOSTS` (현재 `release.tdnet.info` 등) |
| 임계값 | 없음 |
| severity | **RED**(차단) — 지금 200 이어도 반드시 썩는다 |
| 오탐 억제 | 불필요(호스트 목록이 곧 화이트리스트의 여집합). 목록 추가는 owner 승인 |

| 항목 | 내용 |
|---|---|
| 룰 id | `JP_ESR_NOT_IN_SOURCE` |
| 입력 | `posted` 행 × (`esr_pct`, `source_url`) |
| 판정식 | 문서 텍스트에 `esr_pct` 표기가 **한 번도 안 나오면** 위반. 표기 정규화: `268` / `268.0` / `268％` / 전각 `２６８` 동일 취급 |
| 임계값 | 정확일치(비율은 % 한 자리 표기가 규약, §2) |
| severity | **RED**(차단) |
| 오탐 억제 | ① 텍스트 추출 0자(이미지형 PDF) → `SKIP`+YELLOW(2026-09-13 실측으로 최소 2사가 이미지형) ② `source_url` 이 PDF 가 아닌 랜딩 페이지면 → YELLOW(T&D 처럼 상설 페이지를 정본으로 쓰는 경우) ③ 3자리 숫자가 다른 문맥(페이지번호·연도)에 우연히 있을 수 있으므로 **ESR 라벨(§3 변형 목록)과 같은 문장 안**일 것을 요구 |

| 항목 | 내용 |
|---|---|
| 룰 id | `JP_ESR_EDINET_MISMATCH` |
| 입력 | `edinet_esr_probe.json` 의 `esr_pct_candidates` × 화면 `esr_pct` (EDINET 有報 제출 17사 한정) |
| 판정식 | 후보 집합에 화면값이 **포함되지 않으면** 위반 |
| 임계값 | ±0.5%p |
| severity | **YELLOW**(비차단) |
| 오탐 억제 | 有報는 연결/단체·내부모델/규제·전기/당기를 한 문서에 섞어 싣는다 — 2026-09-13 실측에서 ソニーFG(168=前期 자회사 단체치)와 MS&AD(有報에 기말 수치 없음)가 정확히 이 이유로 오탐이었다. 그래서 **RED 로 올리지 않는다**(기준 차이가 정상인 축) |

## 3. 그 룰이 지금 배선됐나

| | 함수/규칙 | 파일 | scope | exit-code 반영 |
|---|---|---|---|---|
| K-ICS 게이트 | 해당 없음(도메인 밖) | `scripts/validate_kics_disclosure.py` | — | — |
| **push 게이트** | **미배선** | `scripts/validate_data_contract.py` | — | ❌ |
| jp 빌더 self-check | **미배선**(범위·형식·합계만) | `J-ESR/build_jesr_page_json.py` | census 전량 | ❌ |
| 수동 점검기(신설) | `check_source_urls.py` (`dead`/`expiring_host` 면 exit 1) | `J-ESR/check_source_urls.py` | 화면+census+insurers | ⚠️ **사람이 돌려야 돈다** |
| 수동 대조기(신설) | `edinet_esr_probe.py` (`mismatch` 목록 출력) | `J-ESR/edinet_esr_probe.py` | EDINET 제출 17사 | ⚠️ 사람이 돌려야 돈다 |

⚠️ **도구는 생겼지만 게이트는 아니다.** 2026-09-13 기준 jp 레인은 `prepush_check.py` 에 걸려 있지 않고
(CLAUDE.md §5 의 jp 범위 diff 는 `test_deploy_assets` + inbox 위생만 돈다), 빌더 self-check 에도
들어가 있지 않다. **지금 상태는 "다음 사람이 기억하면 잡힌다" = honor system** 이고, 이 저장소가
UH-14·UH-15 에서 이미 같은 실패를 기록했다.

## 4. documented exception

- **없음.** 현재 예외 0건.
- jp 레인에는 K-ICS 처럼 registry 변수(`_MARKET_BREAKDOWN_EXEMPT` 류)가 없다. 배선 시 예외 등재처를
  **같이** 정해야 한다(제안: `J-ESR/jp_source_exceptions.json` — 회사·필드·사유·owner 승인일).
  exemption 추가는 **owner 권한**.

## 5. 미배선 잔여 + 후속 티켓

| 잔여 | 왜 위험 | 후속 티켓 / 우선순위 |
|---|---|---|
| **UH-18** — jp 출처·수치 룰 4종이 어느 게이트에도 안 걸려 있다. `JP_SOURCE_URL_DEAD`·`JP_SOURCE_EXPIRING_HOST` 는 네트워크 없이 못 돌아 빌더 self-check 에 그대로 넣을 수 없고(빌드가 오프라인이어야 한다), `JP_ESR_NOT_IN_SOURCE` 는 PDF 다운로드가 필요해 더 무겁다 | 10/31 재census 는 62사가 한꺼번에 `posted` 로 뒤집히는 라운드다. 지금 구조면 **그 62사도 똑같이 형식만 통과**한다. 오늘 3사에서 3건이 나왔다 | `inbox/jp/20260913T1500Z__validation__JP_MULTI__jp_source_gate_wiring.md` / **P1** |

**배선 방향 제안(티켓에 그대로 옮김)**: 오프라인/온라인을 갈라서 건다.
① 오프라인으로 가능한 `JP_SOURCE_EXPIRING_HOST` 는 **빌더 self-check 에 즉시**(exit 1) —
네트워크 없이 netloc 만 보면 된다. ② 네트워크가 필요한 `JP_SOURCE_URL_DEAD`·`JP_ESR_NOT_IN_SOURCE` 는
census 라운드의 **선행 단계로 규정**하고(§4c), 산출 `source_url_health.json` 의 `checked_at` 이
census `checked_at` 보다 **오래되면 빌더가 RED** — 이러면 네트워크 없이도 "점검을 안 돌렸다"를 잡는다.
이 방식은 UH-14 가 지적한 "정본 증거가 push 묶음 밖" 문제를 **증거 신선도 검사**로 우회하는 형태다.

---

## close 체크

- [x] 1 무엇이 통과했나
- [x] 2 구체 룰 정의 (4종, 오탐억제 포함)
- [x] 3 배선 위치 + scope (**전부 미배선** — 그 사실을 명시)
- [x] 4 exception 근거·등재 위치 (없음 + 등재처 부재를 과제로 등록)
- [x] 5 미배선 잔여 + 후속 티켓 (UH-18 / P1)

**3번이 "아니오"이므로 `open` 유지.** UH-18 배선 후 close.
