---
from: owner
to: validation
created: 20260803T0056Z
status: resolved
route: blind_spot
company: MULTI
period: 2026.1Q
rule: EFFECTIVE_LIST_NOT_FILTERED
iter: 1
---

## 미결 (owner) — data-contract 게이트가 자본성증권 provenance에 **틀린 소스 라벨을 요구**하고 있다 (false-green 소인)

**발견 경로.** 다운로더 `bonds`(FSC data.go.kr) 소스 폐지 가능성을 전수 조사하던 중 발견.

### 사실관계

`scripts/validate_data_contract.py:383`
```python
_CAPITAL_SECURITIES_MASTERS = {"forward_capital", "tier1_utilization", "tier2_utilization"}
```
`scripts/validate_data_contract.py:438-445`
```python
if cell.get("source_id") != "FSC_BONDS" or cell.get("effective_filtered") is not True:
    ... rule="EFFECTIVE_LIST_NOT_FILTERED"  # "must be FSC_BONDS + effective_filtered==true"
```

→ 게이트는 세 마스터 전부에 **`source_id == "FSC_BONDS"`를 강제**한다.

**그런데 tier1/tier2는 2026-06-20부터 FSC가 아니라 DART다.**
- `scripts/wire_capital_securities_to_utilization.py:28` → 입력 = `data/bonds/capital_securities_fy2025.json`
- 같은 파일 `:130`, `:153` → `"source": "DART FY2025 annual per-bond (...)"`
- 산출 JSON 안에도 `data_source: "dart_bonds_fy2025_경과조치"`로 박혀 있음
- 근거 발주: `inbox/_resolved/20260620T0238Z__owner__MULTI__capital_securities_issuance_from_dart.md`

**결과 = 라벨 거짓말이 게이트를 통과 중.**
`kics_tier1_utilization_provenance.json` / `kics_tier2_utilization_provenance.json`
(둘 다 `generated_at: 20260721T115831Z` — DART 전환보다 **한 달 뒤** 발행) 현재 내용:
```json
"source_id": "FSC_BONDS",
"source_file": "data/bonds/capital_securities_fy2025.json"   ← DART 파일
```
`source_file`은 DART인데 `source_id`는 FSC라고 선언 → **게이트가 "소스를 검증한다"면서
실제로는 틀린 주장을 확인하고 통과시키는 상태.** owner 원칙("게이트가 검사하는 파일 = 사용자가 보는 파일",
data-contract = provenance/as-of 검사) 정면 위배다.

## 요청

### 1. enum을 실제 lineage에 묶기 (하드코딩 `FSC_BONDS` 제거)
단순히 `{FSC_BONDS, DART}` 둘 다 허용으로 넓히면 **검증력이 떨어진다**(아무 라벨이나 통과).
권장: **`source_id`가 `source_file`의 실제 계보와 일치하는지**를 검사하는 형태로 바꿀 것.
- `data/bonds/normalized/**`, `data/bonds/raw/**` → `FSC_BONDS`
- `data/bonds/capital_securities_*.json`, `data/bonds/disclosure/**`, `data/dart/**` → `DART`
- 불일치 → RED (신규 rule id 제안: `SOURCE_ID_LINEAGE_MISMATCH`)

**`effective_filtered == true` 요구는 유지할 것.** 그게 진짜 불변식이다
(상환·콜 도래분이 outstanding 총액에 섞이는 도넛 버그 가드).

### 2. 사이드카 재발행
tier1/tier2 사이드카의 `source_id`를 `DART`로 정정. 이건 `scripts/emit_bonds_provenance.py`가
아니라(그건 `data/bonds/normalized/**/bonds_provenance.json`만 씀 — `:51`에 `FSC_BONDS` 하드코딩,
이쪽은 실제로 FSC라서 맞음) **루트 3개 사이드카를 쓰는 경로**를 찾아 고칠 것.
발행 주체가 스크립트로 존재하지 않으면(손으로 쓴 흔적) **재발행 스크립트를 만들어 배선**할 것 —
안 그러면 다음 리빌드에서 정정이 씻겨나간다.

### 3. `_load_bond_evidence()` 재조준 — 지금 조용히 무력화될 위험
`scripts/validate_data_contract.py:931`
```python
bi = dirs[-1] / "bonds_by_insurer.json"   # data/bonds/normalized/<최신stamp>/ = FSC 전용
if not bi.exists(): return ev             # → snapshot_present=False, 그냥 통과
```
동반 발주 `inbox/parser/20260803T0055Z__owner__MULTI_2026.1Q__forward_capital_rebase_fsc_to_dart.md`가
`forward_capital`을 DART로 옮기면 **이 증거 체크가 빈 껍데기가 된다**(FSC 스냅샷이 사라져도 RED 없이 통과).
→ effective-filter 증거를 **DART per-bond 산출물에서** 확인하도록 재조준할 것.
파일 없음 = `snapshot_present=False`를 **통과가 아니라 RED**로 (owner 원칙 0: SKIP-on-missing 금지).

### 4. as-of 정본 확정 (parser 발주와 물려있음)
`kics_forward_capital_provenance.json`은 `as_of_date: 2026-03-31`(2026.1Q)인데,
산출 JSON baseline은 `baseline_2025_4Q`이고 DART per-bond는 `as_of: 2025-12-31`(2025.4Q).
`:419-429` `STALE_AS_OF`가 걸릴 수 있다. 어느 쪽이 정본인지 확정하고 parser 발주와 값을 맞출 것.

### 5. 포스트모템 1건
게이트를 통과했는데 소스 주장이 틀린 케이스 = false-green. `incident-postmortem` skill 관행대로
`docs/postmortems/PM-2026-08-03_capsec_provenance_label_mismatch.md` 작성 + `README.md` 색인 갱신.
5칸 중 특히 **"그 룰이 지금 어디에 배선됐나"**를 명시할 것 — `prepush_check.py`가
`validate_kics_disclosure.py`를 호출하지 않는 절반-경화 문제도 같이 확인.

## 완료 조건 (verify)

1. `python scripts/validate_data_contract.py` → **RED = 0** (라벨 정정 후에도).
2. 사이드카 `source_id`를 일부러 틀리게 바꿔서 재실행 → **RED이 뜨는지 확인**(mutation test).
   지금은 이게 안 뜬다 = 룰이 죽어있었다는 증거.
3. `pytest tests/test_deploy_assets.py` 통과 (모든 `.py` BOM 없는 UTF-8).
4. 이 발주는 parser 발주와 **독립적으로 먼저 착지 가능** — 라벨이 틀린 건 지금 사실이므로 기다릴 필요 없다.

근거 메모리: `project_data_contract_gate`, `reference_capital_securities_utilization`,
`reference_tier2_utilization_provenance`, `feedback_red_blocks_push`.

## 답변 (validation, 2026-08-03) — 5건 전부 착지. 게이트 RED=0, mutation으로 룰 사망 증명

지적 정확. `source_id` 하드코딩이 사이드카에 거짓 라벨을 **요구**하고 있었고, 게이트가 그 거짓을
확인해주고 통과시켰다. 5건 조치:

**1. enum → 계보 검사 (요청대로 하드코딩 제거).** 신규 룰 **`SOURCE_ID_LINEAGE_MISMATCH`** (RED).
`source_id_for_lineage()` + `_SOURCE_LINEAGE` 매핑을 `scripts/validate_data_contract.py`에 신설,
`verify_provenance_sidecar()`에서 판정. 매핑은 요청한 그대로
(`normalized/**`·`raw/**`→FSC_BONDS / `capital_securities_*`·`disclosure/**`·`data/dart/**`→DART).
**계보 미등록 경로도 RED**(검증 불가 = 통과 아님). `effective_filtered == true` 요구는 **유지**하되
`source_id` 검사와 **분리**해 어느 쪽이 깨졌는지 구분되게 했다.

**2. 사이드카 재발행 + 발행 주체 신설.** 손으로 쓴 흔적 맞다(publishing `faa34cd`, 스크립트 없음).
**`scripts/emit_capsec_provenance.py`** 신설 — `source_id`를 **하드코딩하지 않고** 게이트와 **같은
함수**(`source_id_for_lineage`)로 `source_file`에서 도출한다. `--check`는 drift 시 exit 2.
배선 2중: (a) 게이트가 drift를 RED로 차단, (b) `tests/test_deploy_assets.py::
test_capsec_provenance_source_id_matches_lineage` 신규 — 라벨/계보 일치 + `--check` 무drift 기계검사.
→ 다음 리빌드에서 씻겨나가면 push 전에 잡힌다.

**3. `_load_bond_evidence()` 재조준 — 완료. 단 진단 1건 정정.**
"파일 없음 = 그냥 통과"는 **사실과 달랐다** — 그 경로는 이미 `MISSING_EFFECTIVE_LIST` RED를 방출한다
(`:559`, `if not evid["snapshot_present"]`). **실제 사각은 더 컸다**: 증거를 FSC 스냅샷 **한 파일**에서만
찾았기 때문에, tier1/tier2가 이미 DART로 옮겨간 뒤에도 **서빙되는 DART per-bond 파일의 도넛 가드는
아무도 검사하지 않았다.** 결론(재조준)은 동일하게 유효하므로 그대로 처리:
- `capsec_sources_in_use()`가 **사이드카가 선언한** `{계보: {source_file}}`를 뽑고, **쓰이는 계보마다
  그 선언된 파일**을 검사한다(글롭·최신stamp 추측 없음 = 검사파일 == 서빙파일).
- DART 증거 2축 신설: (i) 아티팩트 자체 as-of에 콜/만기 도래인데 outstanding>0이면
  `past_call_outstanding: true` 필수(흥국식 콜 미행사), (ii) 스냅샷 as-of ~ 마스터 as-of 구간 콜 도래분 —
  후순위는 `amort()`가 0으로 떨어뜨리지만 **신종은 `new_hyb += out`로 tier1 분자에 무조건 합산**되므로
  이 검사만이 막는다. 라이브 실측: 도래·outstanding>0 7건 중 6건 정상 표기, 1건은 스냅샷 이후 콜(대상 아님)
  → 누출 0.
- 파일 부재/판독불가 = **RED** 유지(계보별로).

**4. as-of 정본 확정 — 사이드카가 맞다. 새 결함 1건 적발.**

| 축 | 정본 | 판단 근거 |
|---|---|---|
| 사이드카 `as_of_date` | **2026-03-31 (2026.1Q)** | manifest `baseline_quarter`=2026.1Q, tier doc `quarter`=2026.1Q, `wire_…py:25 AS_OF=2026-03-31`로 인정액 산출 |
| per-bond `as_of: 2025-12-31` | 정상 — **다른 축** | 채권 스냅샷 기준일이지 K-ICS baseline이 아니다. 그 사이 콜 도래분은 3번 축(ii)이 검사 |
| `baseline_2025_4Q` | **stale 키 이름(값은 2026.1Q)** | `forward_capital_simulation.py:45/93`은 `BASELINE_QUARTER="2026.1Q"`로 필터하는데 `:442` 키만 안 따라갔다 |

→ `STALE_AS_OF` 미발화가 정상. 키 misnomer는 `K-ICS.html`이 읽으므로(1곳) validation 단독 수정 금지 →
publishing 발주 `inbox/publishing/20260803T0210Z__validation__…forward_baseline_key_misnomer.md` (UH-7).

**5. 포스트모템.** `docs/postmortems/PM-2026-08-03_capsec_provenance_label_mismatch.md` (5칸 충족) +
`README.md` 색인·미배선표 갱신. 3번 칸: 전부 **push 게이트**(`validate_data_contract` ← `prepush_check`)
배선 = 절반-경화 아님. K-ICS 게이트에는 의도적으로 미배선(자본성증권은 `kics_disclosure.json` 스코프 밖).
**owner가 지목한 절반-경화 재확인**: `prepush_check.py:23`은 `validate_data_contract`·
`triage_anomaly_candidates`만 import — `validate_kics_disclosure.py`를 **호출하지 않는다**. 따라서
K-ICS 게이트 전용 룰은 여전히 push를 못 막는다. 체인 추가는 현 documented RED 8건으로 push를 즉시
차단하므로 **owner 결정 사항**으로 남긴다(본 발주에서 임의 변경 안 함).

### 완료 조건 검증

| # | 조건 | 결과 |
|---|---|---|
| 1 | `validate_data_contract.py` RED=0 | ✅ **RED=0** YELLOW=210(전부 기존 generic anomaly 후보, 비차단) |
| 2 | 라벨 틀리게 하고 재실행 → RED 발화 (mutation) | ✅ **배선 전 RED=0 → 배선 후(정정 전) RED=2** (tier1·tier2 `SOURCE_ID_LINEAGE_MISMATCH`) → 재발행 후 **0**. 추가로 `source_id_for_lineage` 무력화 시 selftest G1 **FAIL**(미검출) 확인 = 룰이 실제 판정 중 |
| 3 | `pytest tests/test_deploy_assets.py` | ✅ **9 passed** (신규 테스트 포함, 모든 `.py` BOM 없는 UTF-8) |
| 4 | parser 발주와 독립 착지 | ✅ 독립 착지. 착지 중 병행 parser 세션이 forward_capital을 DART로 재기준(manifest `bonds_source`가 경로로 변경) → 사이드카가 **도출식**이라 `FSC_BONDS→DART` 자동 추종, 별도 손수정 없이 RED=0 유지 |
| — | 게이트 self-test | ✅ `--selftest` **16/16 PASS** (신규 G1 `SOURCE_ID_LINEAGE_MISMATCH`, G2 `CSM_WATERFALL_PLAUSIBILITY`) |
