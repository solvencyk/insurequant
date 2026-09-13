# PM-2026-09-13 — jp 레인 ESR 2건이 2차보도·조정치 기반으로 화면에 올라갔고, 출처 URL 은 다른 문서였다

> 상태: `open` (3번이 **부분 배선** — 2026-09-13 UH-18 로 룰 4종이 빌더 self-check 에 들어갔으나,
> 그 self-check 는 **빌더를 돌릴 때만** 돈다. 빌드 없이 census·배포 JSON 이 push 되는 경로가 남아 있다 → UH-19)
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

**2026-09-13 UH-18 배선 후 상태.** 배선 지점은 한 곳(`J-ESR/build_jesr_page_json.py::source_gate_check`)이고,
`self_check()` 가 그 반환값을 자기 errors 에 `extend` 하므로 `main()` 의 `return 1` 에 **실제로 반영된다**
(변이시험으로 확인: 그 `extend` 한 줄을 지우면 exit-code 케이스 3개가 즉시 FAIL).

| 룰 | 함수/규칙 | 파일 | scope | exit-code 반영 |
|---|---|---|---|---|
| `JP_SOURCE_EXPIRING_HOST` | `source_gate_check` — netloc ∈ `jesr_http.EXPIRING_HOSTS`(import, 재타이핑 금지) | `J-ESR/build_jesr_page_json.py` | census `posted` × `source_url` (= master records ⊇ 배포 records) | ✅ **exit 1** |
| `JP_SOURCE_URL_DEAD` | `source_gate_check` — **증거 기록 판독형**: `source_url_health.json` 행의 `classification == "dead"` | 〃 | 같음 | ✅ **exit 1** |
| `JP_SOURCE_EVIDENCE_STALE` | `source_gate_check` — 증거 파일 부재 · `scope != "all"` · `checked_at` < census 최신 `checked_at` · posted 행 `checked_at` 결측 | 〃 | 증거 파일 1개 + census 전량 | ✅ **exit 1** |
| `JP_SOURCE_EVIDENCE_INCOMPLETE` | `source_gate_check` — posted `source_url` 이 증거 파일 `rows[].url` 에 없음 | 〃 | census `posted` × `source_url` | ✅ **exit 1** |
| `JP_ESR_NOT_IN_SOURCE` | **미배선**(§5) — 선행 단계 규격만 §4c-pre 에 확정 | — | — | ❌ |
| `JP_ESR_EDINET_MISMATCH` | **미배선**(§5) — YELLOW 축이라 차단 룰로 승격하지 않음 | `J-ESR/edinet_esr_probe.py` | EDINET 제출 17사 | ⚠️ 사람이 돌려야 돈다 |
| K-ICS 게이트 | 해당 없음(도메인 밖) | `scripts/validate_kics_disclosure.py` | — | — |
| **push 훅(prepush)** | ✅ **배선됨**(2026-09-13 후속) — `scripts/prepush_check.py` 의 offline 묶음에 `tests/test_jp_source_gate.py`(43케이스) + `tests/test_jp_deploy_matches_census.py`(불변식 1번) 추가. CLAUDE.md §5 의 jp 축소범위 목록에도 두 파일을 넣었다 | `scripts/prepush_check.py` · `CLAUDE.md §5` | jp 전량 | ✅ **push 차단** |
| push 게이트(한국) | 해당 없음 — jp 마스터는 `validate_data_contract` 의 대상이 아니다 | `scripts/validate_data_contract.py` | — | — |
| 수동 점검기 | `check_source_urls.py` (`dead`/`expiring_host` 면 exit 1) | `J-ESR/check_source_urls.py` | 화면+census+insurers | ⚠️ 사람이 돌린다 — **다만 이제 안 돌리면 빌더가 RED** |

**UH-19(빌더를 안 돌리면 게이트도 안 돈다)는 같은 날 닫혔다.** ① 배포 JSON 을 census 기준으로 재생성하고
② `tests/test_jp_deploy_matches_census.py` 를 신설했다 — 빌더를 임시 경로로 재실행해 커밋된 `jp/jesr_esr.json`·
`J-ESR/jesr_master.json` 과 `generated_at` 제외 전량 비교한다. 즉 **"빌더를 돌렸는가" 자체가 검사 대상**이 됐고,
그 테스트가 prepush 묶음에 들어가 있으므로 빌더 미실행 상태로는 push 가 안 된다. 이빨 확인: 배포본의
`records[0].esr_pct` 를 흔들면 즉시 FAIL(사본 아님 — 원본 md5 복원 확인).

**네트워크를 안 타고 어떻게 dead 를 보나.** 갈라놨다. 네트워크가 필요한 판정은 선행 단계
(`check_source_urls.py --all`)가 `J-ESR/source_url_health.json` 에 **박제**하고, 빌더는 그 박제를 읽는다.
빌드는 여전히 완전 오프라인이다. 대신 `JP_SOURCE_URL_DEAD` 의 이빨은 `JP_SOURCE_EVIDENCE_STALE` 이
증거를 최신으로 강제하는 데 전적으로 의존한다 — **둘은 한 쌍이지 독립된 룰이 아니다.** 증거가 낡으면
dead 판정도 같이 낡으므로, 신선도 룰이 죽으면 dead 룰도 같이 죽는다.

**오탐 억제(실측 기반).** 증거 파일에서 RED 로 읽는 분류는 `dead`(404/410) **하나뿐**이다.
2026-09-13 전수 254건 실측에서 `blocked` 20 · `ok_requires_headers` 16 · `tls_client_issue` 4 ·
`spa_shell` 4 · `error` 4 가 나왔고, "ok 가 아니면 RED" 로 짰으면 **48건이 한꺼번에 거짓 RED** 였다.
화면 15사만 봐도 `ok` 12 · `ok_requires_headers` 2(MS&AD·ソニーFG) · `tls_client_issue` 1(ソニー生命) ·
`dead` 0 이다. 회귀 케이스로 6개 분류를 전부 박아 뒀다(`tests/test_jp_source_gate.py`).

**자기검증.** `tests/test_jp_source_gate.py` 43 케이스(위반→RED / 정상→통과 양방향 + 실데이터 1건 +
빌더를 서브프로세스로 돌려 exit code 를 직접 재는 4건). 이빨 검증 5종 전부 발화 확인:
배선 제거 → 3 FAIL · `EXPIRING_HOSTS` 비우기 → 11 FAIL · `DEAD_CLASSIFICATIONS` 비우기 → 1 FAIL ·
절차 룰을 면제 가능으로 → 1 FAIL · 예외 필수키 검사 제거 → 3 FAIL.

## 4. documented exception

- **현재 예외 0건.** 그리고 그게 정상 상태다 — 채워야 할 할당량이 아니다.
- 등재처 **신설 완료**: `J-ESR/jp_source_exceptions.json`(2026-09-13). 소비 코드는
  `build_jesr_page_json.py::load_source_exceptions`. 항목 키는 `(rule, company_jp, field)` 셀 단위라
  한 줄이 축 전체를 눈감기지 못한다(PM-2026-08-24(b) 의 "부재형 면제가 축을 통째로 눈감겼다" 재발 방지).
- **등재는 owner 권한.** 파일 헤더(`_README`)와 소비 함수 docstring 양쪽에 박아 뒀다.
- fail-closed 설계:
  - 파일 **부재** → 면제 0건으로 진행(게이트가 더 엄해지는 방향이라 막지 않는다).
  - 파일이 있는데 **못 읽으면 RED**. "읽을 수 없으니 면제 없음" 으로 넘기면 손상된 레지스트리가 안 보인다.
  - `reason`·`owner_approved_on` 포함 **필수 키 누락 → RED**(익명 면제 차단).
  - **모르는 rule id → RED.** 오타난 id 는 아무것도 면제 못 하면서 "면제해 뒀다" 는 착각만 남긴다.
  - **면제 불가 룰**(`JP_SOURCE_EVIDENCE_STALE`·`JP_SOURCE_EVIDENCE_INCOMPLETE`)을 가리키면 **RED**.
    이 둘은 "점검을 돌렸는가" 를 묻는 절차 룰이라 면제하면 룰 자체가 사라진다.
  - `expires_on` 이 지나면 면제가 **자동으로 꺼진다**(시간이 갈수록 엄해진다).
- `_README` 가 나열한 룰 id ↔ 코드의 `SOURCE_RULE_IDS` 는 테스트가 대조한다
  (`test_registry_readme_names_exactly_the_code_rule_ids`) — 문서·코드가 같은 사실을 두 벌 들고
  조용히 갈라지는 것을 막는다. **이 케이스는 작성 중 실제로 한 번 발화했다**(코드에 `JP_SOURCE_URL_DEAD`
  를 추가하고 `_README` 를 안 고쳤을 때).

## 4c-pre. `JP_ESR_NOT_IN_SOURCE` 선행 단계 규격 (배선은 아직 안 한다)

이번에 **배선하지 않는다**(이유는 §5). 대신 나중에 같은 방식으로 태울 수 있도록 산출 규격만 못 박는다 —
"오탐 억제를 설계할 수 없으면 배선하지 않는다"(UH-5·UH-9 선례)를 여기서도 지킨다.

- 실행 시점: census 라운드의 **선행 단계**. `check_source_urls.py --all` 바로 뒤, census 확정 전.
- 산출: `J-ESR/esr_in_source_health.json` — `source_url_health.json` 과 **같은 봉투**를 쓴다.
  `{"checked_at": "...Z", "scope": "all", "rows": [{company, field, url, esr_pct,
  "verdict": "found"|"not_found"|"skip_image_pdf"|"skip_landing_page", "evidence": "<발췌>"}]}`
- 같은 봉투를 쓰는 이유: 봉투가 같으면 **신선도 검사를 그대로 재사용**할 수 있다
  (`checked_at` < census 최신 `checked_at` → RED, `scope != "all"` → RED, posted URL 미수록 → RED).
  배선 시 `source_gate_check` 에 파일 하나를 더 물리면 되고 새 검사 축을 만들 필요가 없다.
- 배선 전 반드시 채워야 할 것: §2 표의 오탐 억제 3종(이미지형 PDF → SKIP+YELLOW / 랜딩 페이지 →
  YELLOW / ESR 라벨과 **같은 문장** 요구)의 **실측 분포**. 몇 사가 이미지형인지, 랜딩 페이지 정본이
  몇 사인지를 세기 전에는 임계값을 정할 수 없다(2026-09-13 시점 확인분은 "최소 2사 이미지형" 뿐).

## 4c-pre-실측. `JP_ESR_NOT_IN_SOURCE` 의 오탐억제 분포 — 2026-09-13 전수 측정으로 확정

배선을 막고 있던 것은 규격이 아니라 **세어본 적 없는 분포**였다(UH-5·UH-9 선례: 오탐억제를 설계할 수
없으면 배선하지 않는다). posted 15사의 `source_url` 을 전부 열어 세었다.

| 축 | 실측 |
|---|---|
| 문서 유형 | PDF **14사** · 랜딩 페이지 정본 **1사**(T&D) |
| 텍스트 레이어 | 완전 **10사** · 부분 **4사** · **이미지형 0사** |
| 화면값 탐지 | 문서 안에 있음 **14사** · 미탐지 1사(T&D — 문서가 아니라 목록 페이지) |
| 라벨↔값 공존 형태 | 산문 문장 **7사** · **표 행 4사** · **차트 데이터라벨 3사** · 해당없음 1사 |

**§2 의 원래 규격이 틀렸다.** 두 군데를 정정한다.

1. **"이미지형 PDF 는 SKIP" 은 설계할 필요가 없었다** — 표본에 0사다. 부분 추출 4사도 빈 페이지는 전부
   슬라이드 구분면이고 **ESR 이 실제로 있는 페이지는 4사 모두 정상 추출**됐다. §2 가 "최소 2사 이미지형"
   이라고 적었던 것은 추정이었고 실측이 뒤집었다.
2. **진짜 병목은 "ESR 라벨과 같은 문장" 요구였다.** 결산 프레젠테이션·전화회의자료·업적데이터 별책은
   애초에 산문이 거의 없는 문서 유형이라 값과 라벨이 **표 행이나 차트 데이터라벨로만** 공존한다(7/14사 = 50%).
   이 7사는 수치가 전부 진짜인데 문자 그대로 걸면 **거짓 RED 7건**이 난다.

**확정 규격**: 근접 판정을 "같은 문장" → **"같은 표 행 / 같은 차트 범례+데이터라벨 군 / 같은 단락(±200자)"**
으로 넓힌다. 이 기준이면 SKIP+YELLOW 는 **T&D 1사뿐**(랜딩 페이지라 문서가 아니다)이고 14/15 가 정상 통과한다.
산출 봉투는 `source_url_health.json` 과 동일(`checked_at`/`scope`/`rows`)로 내어 신선도 검사를 그대로 재사용한다.

## 5. 미배선 잔여 + 후속 티켓

| 잔여 | 왜 위험 | 후속 티켓 / 우선순위 |
|---|---|---|
| **UH-18 ⚠️ 부분 해소 (2026-09-13)** — 룰 4종(`JP_SOURCE_EXPIRING_HOST`·`JP_SOURCE_URL_DEAD`·`JP_SOURCE_EVIDENCE_STALE`·`JP_SOURCE_EVIDENCE_INCOMPLETE`)을 빌더 self-check 에 배선하고 exit 1 을 실증했다(§3). **남은 것은 `JP_ESR_NOT_IN_SOURCE`** — "그 문서에 그 숫자가 있나" 축은 여전히 아무도 안 본다 | 東京海上HD 238·かんぽ 220 은 **URL 이 살아 있고 만료 호스트도 아니었다.** 이번에 배선한 4종은 그 둘을 못 잡는다 — 잡은 것은 MS&AD 형(출처가 무관한 문서)·T&D 형(만료 호스트)뿐이다 | 규격 §4c-pre 확정. 오탐 억제 실측(이미지형 PDF·랜딩 페이지 분포)이 **선행조건** / **P2** |
| **UH-19** (신규) — **빌더 self-check 는 빌더를 돌릴 때만 돈다.** jp 레인은 `prepush_check.py` 대상이 아니고(CLAUDE.md §5 jp 범위 = `test_deploy_assets` + inbox 위생), 게이트는 "새 `jp/jesr_esr.json` 을 만들 때" 발화한다. census 를 고치고 **빌드 없이** 커밋하면 게이트는 한 번도 안 돈다 | **가정이 아니라 실측이다.** 커밋 `62eed63`(2026-09-13 14:43Z)이 census 와 `esr_target_ranges.json` 만 고치고 `jp/jesr_esr.json` 을 재생성하지 않아, HEAD 의 배포 JSON 이 HEAD 의 census 와 어긋난 채 남았다: 2사 `basis` 가 여전히 `"unconfirmed"`(정정값 `regulatory_standard`·`internal_model`), SOMPO `target_range.high_pct` 가 여전히 `270`(정정값 `null`). 즉 **불변식 1번**(게이트가 검사하는 파일 = 사용자가 보는 파일)이 jp 레인에서 아직 안 닫혔다 | 권고: `tests/test_deploy_assets.py` 나 jp 범위 게이트에 "`jp/jesr_esr.json` = census 로 다시 빌드한 결과(generated_at 제외)" 대조를 넣는다. **지금 넣으면 즉시 RED** 이므로 배포 JSON 재생성이 선행 / **P1** |

**배선 방향(이번에 실행한 것)**: 오프라인/온라인을 갈라서 걸었다.
① 네트워크 없이 되는 `JP_SOURCE_EXPIRING_HOST` 는 netloc 만 보면 되므로 빌더 self-check 에 직접.
② 네트워크가 필요한 판정은 선행 단계(`check_source_urls.py --all`)가 `source_url_health.json` 에
박제하고, 빌더는 **박제를 읽는다**(`JP_SOURCE_URL_DEAD`). 박제가 낡거나 좁거나 빠지면 RED
(`JP_SOURCE_EVIDENCE_STALE`·`JP_SOURCE_EVIDENCE_INCOMPLETE`). 이 방식은 UH-14 가 지적한
"정본 증거가 push 묶음 밖" 문제를 **증거 신선도 검사**로 우회하는 형태다 — 증거를 push 묶음 안으로
가져오는 대신 **증거의 나이**를 검사한다.

**남은 사각을 정확히 말하면**: 이번 배선은 "출처가 살아 있나 / 점검을 돌리긴 했나" 를 닫았고,
**"그 문서에 그 숫자가 있나" 는 못 닫았다.** 사고 3건 중 2건(東京海上HD 238 · かんぽ 220)이 후자였다.
그래서 이 포스트모템은 `open` 이다.

---

## close 체크

- [x] 1 무엇이 통과했나
- [x] 2 구체 룰 정의 (4종, 오탐억제 포함)
- [~] 3 배선 위치 + scope — **4종 배선 + exit 1 실증**(`source_gate_check`, 회귀 43 · 이빨 5/5).
      **`JP_ESR_NOT_IN_SOURCE` 미배선**이고, 배선한 4종도 **빌더를 돌릴 때만** 돈다(UH-19)
- [x] 4 exception 근거·등재 위치 (`J-ESR/jp_source_exceptions.json` 신설, 0건, owner 권한 명시)
- [x] 5 미배선 잔여 + 후속 티켓 (UH-18 부분 해소 / P2 · UH-19 신규 / P1)

**3번이 아직 완전한 "예"가 아니므로 `open` 유지.** close 조건 두 개:
① `JP_ESR_NOT_IN_SOURCE` 배선(§4c-pre 규격 + 오탐 억제 실측 선행), ② UH-19 — 빌드를 거치지 않고
배포 JSON·census 가 push 되는 경로를 막는 대조 검사.
