---
from: owner
to: downloader
created: 20260803T0057Z
status: resolved
route: backlog
company: ALL
period: N/A
iter: 1
---

## 미결 (owner) — `bonds`(FSC data.go.kr) 소스 폐지: 다운로더 5대 소스 → 4대

> [!warning] **선행조건 (하드 게이트) — 이 둘이 `resolved` 되기 전에는 착수 금지**
> 1. `inbox/parser/20260803T0055Z__owner__MULTI_2026.1Q__forward_capital_rebase_fsc_to_dart.md`
>    → `kics_forward_capital.json`이 FSC 대신 DART per-bond를 읽도록 교체
> 2. `inbox/validation/20260803T0056Z__owner__MULTI__capsec_provenance_source_id_dart.md`
>    → 게이트 `source_id` enum 정정 + `_load_bond_evidence()` 재조준
>
> **지금 소스를 지우면 `forward_capital` 빌드와 push 게이트가 둘 다 깨진다.**
> 착수 전 확인 명령:
> ```bash
> grep -rn "bonds_by_insurer\|src/bonds\|src\.bonds" scripts/ src/ --include=*.py
> ```
> `forward_capital_simulation.py` / `validate_data_contract.py`가 여기 남아있으면 **아직 아니다.**

### 배경

`bonds` 소스(FSC data.go.kr 자본성증권 API `15059611`)는 기본자본/보완자본 **인정한도 소진율**의
발행잔액 분자를 대기 위해 도입했다. 그런데 2026-06-20 owner 결정으로 그 분자는 **DART 사업보고서
per-bond로 교체**됐다 (`scripts/wire_capital_securities_to_utilization.py`). 2026-08-03 전수 조사 결과
FSC에 남은 라이브 의존은 `kics_forward_capital.json` **한 곳뿐**이고, 그것도 선행조건 ①로 DART로 넘어간다.
→ 소스 자체를 접는다.

## 요청 (선행조건 충족 후)

### 1. 카탈로그·프롬프트에서 제거
- `docs/agents/source-catalog.yaml` — `- id: bonds` 블록 (약 `164~178`행) 삭제.
  단 `api_ids`의 `nonlife_metrics: 15061307` / `life_metrics: 15061306` / `private_health: 15094797`는
  **`TODO_downloader.md` F9(P2, `src/finstat/` 신규 모듈)의 유일한 기록**이다 →
  삭제하지 말고 F9 항목 본문이나 별도 블록으로 **이관**할 것.
- `docs/agents/claude-agent-downloader.md` — `:74~76`(패턴·env 키), `:178`("Source 2 (bonds)" 재실행 지시) 정리.
  "5대 소스" → **4대 소스**(손보공시·생보공시·DART·KIDI)로 문구 갱신.
- 루트 `CLAUDE.md`에 소스 개수 언급이 있으면 같이 갱신.

### 2. 코드 아카이브 (삭제 아님)
- `src/bonds/{__init__,config,fsc_client,universe}.py`
- `scripts/ingest_fsc_bonds.py`
- `scripts/normalize_bond_schedule.py`
- `scripts/emit_bonds_provenance.py` — **FSC 절반만**(`:25~65`). `:71` 이후 DART disclosure 절은 살아있는
  경로다(`data/bonds/disclosure/2026q1_capital_securities.json`, `source_id: DART`). **통째로 지우지 말 것.**

**아카이브지 삭제가 아닌 이유:** `TODO_downloader.md:33` F9가 `src/bonds/fsc_client.py`를
data.go.kr API 연동 **참조 패턴**으로 지목하고 있다. 지우면 F9 착수 시 패턴이 사라진다.

### 3. 데이터 디렉토리 — 조심할 것
`data/bonds/`는 **FSC와 DART 산출물이 섞여 있다.** 디렉토리 통째 삭제 금지.

| 경로 | 계보 | 처분 |
|---|---|---|
| `data/bonds/raw/**` | FSC | 아카이브 가능 |
| `data/bonds/normalized/**` | FSC | 아카이브 가능 (선행조건 ②의 `_load_bond_evidence()` 재조준 확인 후) |
| `data/bonds/capital_securities_fy2025.json` | **DART** | **유지 — 라이브 tier1/tier2 소스** |
| `data/bonds/capital_securities_forward_outlook.json` | **DART** | **유지** |
| `data/bonds/capital_securities_utilization_20261Q.json` | DART 파생 | 유지 |
| `data/bonds/disclosure/**` | **DART** | **유지** |
| `data/bonds/_census_fy2025.json` | 확인 필요 | 계보 확인 후 판단 |

### 4. env 키 처분
`TODO_downloader.md:68` D5의 `DATA_GO_KR_BOND_ISSUANCE_KEY` / `DATA_GO_KR_BOND_REDE_KEY`는
F9(`src/finstat/`)가 같은 data.go.kr 포털 키를 쓸 가능성이 있다 → **삭제하지 말고 "bonds 폐지, F9 대기" 주석**으로.
`.env`는 손대지 말 것.

## 완료 조건 (verify)

1. `grep -rn "src/bonds\|src\.bonds\|bonds_by_insurer\|ingest_fsc_bonds" --include=*.py .`
   → 아카이브 경로 외 히트 **0건**.
2. `pytest tests/test_deploy_assets.py` 통과 — 특히
   `test_every_python_file_parses`(아카이브한 `.py`도 BOM 없는 UTF-8이어야 하거나 제외경로여야 함)와
   삭제경로 참조 체크.
3. `python scripts/validate_data_contract.py` → **RED = 0**.
4. `python scripts/report_collection_status.py` 실행 확인 —
   `:271`이 `bonds_by_insurer.json`을 읽는다. 없으면 크래시하지 않고 정상 degrade 하는지 확인,
   아니면 그 절도 같이 정리.
5. `docs/changelog_downloader.md`에 폐지 근거(이 발주 링크 + 2026-06-20 DART 전환) 기록,
   `TODO_downloader.md` 맨 위 갱신.

근거 메모리: `reference_capital_securities_utilization`, `reference_data_sources`.
선행 이력: `inbox/_resolved/20260620T0238Z__owner__MULTI__capital_securities_issuance_from_dart.md`,
`docs/changelog_downloader.md:414` (MISC-BOND-INGEST 도입 시점).

## 답변 (downloader 작성 — 2026-08-03, 완료)

선행조건 재확인: parser `20260803T0055Z` resolved, validation `20260803T0056Z` resolved — 착수.

### 1. 카탈로그·프롬프트
- `source-catalog.yaml`: `- id: bonds` 블록 삭제. api_ids 중 nonlife_metrics(15061307)/life_metrics
  (15061306)/private_health(15094797)는 F9 엔트리로 이관(설명 라벨까지 붙여 보강). capital_securities
  (15059611)는 폐기. `meta.scope` "5→4 data sources"로 갱신.
- `claude-agent-downloader.md`: Mission·헤더·워크플로 전체 5→4 리넘버링(Source 2=DART, 3=KIDI,
  4=IR로 당김), 옛 Source 2 자리에 은퇴 배경 note 삽입(archive 경로·changelog 링크 포함).
- 루트 `CLAUDE.md`: grep 확인 — 소스개수 언급 없음(거기 "5"는 5-stage 파이프라인, 무관), 변경 불필요.

### 2. 코드 아카이브 (삭제 아님)
`git mv`로 `data/_archive/20260803T063432Z/`: `src/bonds/{__init__,config,fsc_client,universe}.py`,
`scripts/ingest_fsc_bonds.py`, `scripts/normalize_bond_schedule.py`. `src/bonds/__pycache__`(비추적)만
삭제, 빈 `src/bonds/` 디렉터리 정리.
`scripts/emit_bonds_provenance.py`는 아카이브 대신 **in-place 트림** — FSC 생성부(bonds/normalized
읽기·bonds_provenance.json 쓰기) 제거, DART supplement부(disclosure_bonds_provenance.json)만 유지.
재실행 확인: `disclosure_bonds_provenance.json` (2 cells) 정상 생성.

### 3. 데이터 디렉토리
같은 archive stamp로 이동: `data/bonds/normalized/**`(3개 stamp dir) + gitignore `[0-9]*/` 패턴 대상이던
레거시 bare-timestamp 잔재 2건(`20260525T050327Z`, `20260616T060238Z` — normalized/ 이전 구조의 FSC raw
pull). `data/bonds/raw/`는 빈 디렉터리라 그냥 제거.
**유지**: `capital_securities_fy2025.json`/`capital_securities_forward_outlook.json`/
`capital_securities_utilization_20261Q.json`/`disclosure/**`(전부 DART lineage). `_census_fy2025.json`도
확인 후 유지 — mtime 2026-06-20(FSC→DART 전환 당일), 필드(`hybrid_hits`/`sub_strict`/`HAVE_BONDS`)가
DART raw 스캔 결과이고 오늘 처리한 validation/parser census 스레드(`20260803T0310Z` 등)가 참조 중인
활성 파일임을 확인.

### 4. env 키
`.env` 미변경. `TODO_downloader.md` D5에 "bonds 폐지, F9가 재사용 가능하니 삭제 안 함" 주석 추가만.

### 완료조건 검증 (4/4 통과)
1. `grep -rn "src/bonds\|src\.bonds\|bonds_by_insurer\|ingest_fsc_bonds" --include=*.py .` →
   archive 경로 외 0건. 잔존 3건은 안전 확인: `fetch_capital_securities_dart.py:6`(주석뿐),
   `report_collection_status.py:271`(디렉토리 없으면 X로 graceful degrade, 크래시 안 함),
   `validate_data_contract.py`(894/1327은 "종전에는" 역사적 주석, 1432는 validation이 이미 lineage-게이트
   해놔서 `lineage=="FSC_BONDS"`가 다시는 안 나오는 이상 호출 자체가 안 되는 dead path — 코드 읽어서 직접 확인).
2. `pytest tests/test_deploy_assets.py` → **9 passed**.
3. `python scripts/validate_data_contract.py` → **RED=0** (YELLOW=219, 기존과 동일).
4. `python scripts/report_collection_status.py --period FY2026_Q1` → 크래시 없음, exit 0.
   ⚠️ **부작용 발견**: "자본성증권 발행" 컬럼이 이제 **영구 0/39(0%)** — `check_bonds()`가 여전히
   `data/bonds/normalized/`(이제 없음)만 보고 DART `capital_securities_fy2025.json`은 안 봄. 이 티켓
   범위 밖("크래시 안 하면 통과"만 요구)이라 코드는 안 건드림 — **이 컬럼을 DART로 재조준할지는 owner
   결정 필요**(원하면 별도 발주).

`docs/changelog_downloader.md` 2026-08-03 항목 + `TODO_downloader.md` 최상단 Status 갱신 완료.

status: **완료** — 4-source 체제 전환, 검증 4/4 통과. 잔여 후속: "자본성증권 발행" 리포트 컬럼 DART
재조준 여부(owner 결정 대기).

### 추가 정정 (검증 중 발견 — git 추적 불일치)
`data/bonds/normalized/`는 원래 `.gitignore` 대상이 **아니었음**(raw/·`[0-9]*/`만 무시) — 그런데
실제로 git에 추적되던 건 3개 stamp dir 중 **`20260525T061945Z` 딱 하나**(3개 파일)뿐이었음(다른
2개는 애초에 untracked). 이 3개를 plain `mv`로 옮겼더니 git이 archive 쪽 새 위치(`data/_archive/`는
gitignore 대상)를 못 보고 옛 경로만 "삭제됨"으로 잡는 상태가 됨 — `git add`로 그 삭제를 정식 스테이지해
정리(로컬 사본은 archive에 그대로 남아 recoverable, 이 저장소의 다른 archive 관행과 동일).
재검증: pytest 9 passed, RED=0 — 변동 없음 확인.
