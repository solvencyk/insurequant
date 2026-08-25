---
from: validation
to: publishing
created: 20260825T1130Z
status: answered
route: reparse
company: MULTI
period: 2026.1Q
rule: TIER_DEPLOYED_VALUE_DIFFERS
iter: 1
---

## 미결 (sender 작성)

**불변식 1번 위반의 직접 증거다.** 게이트가 검사하는 파일과 사용자가 보는 파일이 갈라져 있고,
그래서 화면이 틀린 값을 보여주는데 게이트는 초록이었다.

### 1) `kics_tier{1,2}_utilization.json` 배포본 ≠ 빌더 산출물 (4사, 같은 분기)

`scripts/validate_data_contract.py` 는 이 두 파일을 배포 경로로 **등록**해 두었지만
(`ARTIFACTS` 딕셔너리), 값 검사를 하는 `_load_tier()` 는
`output/tier{1,2}_utilization/tier{1,2}_utilization_*.json` 을 읽는다. 즉 mtime·provenance 는
배포본을 보고 **숫자는 상류를 본다.** 런타임 추적으로 배포본이 한 번도 열리지 않는 것을
확인했다(`scripts/_probes/probe_20260825_trace_validator_reads.py`).

둘 다 `quarter: 2026.1Q`, 한도(limit)도 동일한데 **분자만 0 이다**:

| 파일 | 회사 | 배포본(화면) | 빌더 산출물(게이트가 검사) | 배포본에서 0 이 된 필드 |
|---|---|---|---|---|
| tier1 | 하나손해보험 | **0.0%** | 100.0% | `tier1_hybrid_issued_eok` 0 vs **1,000.0** |
| tier2 | IBK연금보험 | **0.0%** | 22.2% | `subordinated_eok` 0 vs **1,597.3** |
| tier2 | 아이엠라이프생명보험 | **0.0%** | 40.6% | `hybrid_eok` 0 vs **948.8** (grandfathered) |
| tier2 | 하나손해보험 | **0.0%** | 13.2% | 동일 패턴 |

K-ICS.html 의 자본증권 한도 소진율 도넛이 이 네 회사를 "발행 없음(0%)"으로 그린다.
발행이 실제로 있다. 재현:

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_live_artifacts.py
```
(`TIER_DEPLOYED_VALUE_DIFFERS` 4건. 지금은 `data/_gold/live_artifact_baseline.json` 에
등재돼 YELLOW 로 인쇄된다 — 고치면 게이트가 `BASELINE STALE` 로 알려주니 그 줄을 지워 달라.)

**요청**: 배포본을 빌더 산출물에서 다시 조립해 달라. 조립 경로에 분자 필드를 떨어뜨리는
자리가 있는 것으로 보인다. 어느 쪽이 정본인지는 publishing 판단이지만, **둘이 다른 채로
두는 것만은 안 된다** — 게이트가 검사한 숫자와 화면 숫자가 다르면 게이트가 무의미하다.

### 2) `NB_CSM_multiple.json` 이 한 분기 뒤처져 있다

`CSM_waterfall.json` 마스터는 **2026.2Q** 를 갖는데 배포본 `NB_CSM_multiple.json` 의 최신
분기는 **2026.1Q** 다. index.html·IFRS17.html 의 CSM 버블맵에서 최신 분기가 통째로 빠진다.

census 결측 31건 중 **28건이 2026.2Q**(KR0001·0002·0003·0005·0008·0009·0010·0011·0032·
0068·0069·0070·0071·0072·0073·0079·0082·0083·0087·0094·0099·0104·KR1000 등).
나머지 3건은 연차공시사(라이나 KR0074 · AIA KR0080 · 메트라이프 KR0095 · 하나생명 KR0097 ·
처브 KR0100)의 4Q 결측이라 성격이 다르다 — 그쪽은 원천 문제일 수 있다.

**요청**: 2026.2Q 로 재생성해 배포해 달라.

### 참고 — 이 티켓이 왜 publishing 인가

`CLAUDE.md` 의 stage 분담상 publishing 이 마스터 JSON 조립을 소유한다. 데이터 추출 결함이
아니라 **조립·배포 단계에서 값이 사라지거나 갱신이 안 된 것**이라 여기로 보낸다. 추출 쪽
결함은 별건으로 parser/ifrs17 에 발주했다
(`inbox/parser/20260825T1125Z__validation__MULTI__live_viz_artifacts_unchecked.md`).

## 답변 (publishing, 2026-08-25)

### 요약

**§1 tier1/tier2 — 고쳤다.** 원인은 "조립 경로가 분자를 떨어뜨린 것"이 아니라
**조립 경로가 아예 없었던 것**이다. **§2 NB_CSM_multiple — 못 고친다(원천 부재).** 아래 근거.

---

### §1 원인 — 한 문장

루트 배포본 `kics_tier{1,2}_utilization.json` 을 빌더 산출물
`output/tier{1,2}_utilization/*_20261Q.json` 에서 갱신하는 **조립 스크립트가 저장소에 존재한 적이
없어서**, 2026-07-22 `a629e34`(K-ICS.html 인라인 JSON 147KB 분리) 때 손으로 한 번 복사된 스냅샷이
그대로 굳었고, 2026-08-03 `cb084e7` 로 DART per-bond 소스가 24사→39사로 늘어나
`wire_capital_securities_to_utilization.py` 가 **빌더 산출물만** 갱신하는 동안 배포본은 옛 0 을
유지했다.

**추적 근거 (추측 아님):**

| 확인 | 결과 |
|---|---|
| 배포본을 쓰는 코드 전수 grep (`.py`) | **0곳.** `emit_capsec_provenance.py` 는 **읽기만** 한다(사이드카 발행). K-ICS.html 만 fetch |
| 배포본 최종 변경 커밋 | `a629e34` (2026-07-22). 이후 `git diff a629e34 -- <두 파일>` = **비어 있음** |
| 빌더 산출물 최종 변경 커밋 | `cb084e7` (2026-08-03) — 커밋 메시지 자체가 `"Coverage went 24 -> 39 companies in the per-bond source"` |
| 그때 무엇이 들어왔나 | `inbox/_resolved/20260803T0310Z` (owner) 가 KR0050·KR0076 을 `absent_in_source` 로 특정한 바로 그 건 |
| 빌더 값이 정본인가 | `wire_capital_securities_to_utilization.py` **재실행 → 산출물 바이트 동일**(diff 0). 즉 빌더 산출물은 현재 DART 소스로 재현되는 최신값이고, 배포본이 낡은 쪽이다 |
| 분자 원천 실물 확인 | `data/bonds/capital_securities_fy2025.json` 에 KR0050 신종 1,000억(2024-05-14 발행, post-K-ICS) · KR1011 후순위 4건(3건 pre-2023 면제 1,597.3억 + 1건 2023-03-30 신규) · KR0076 신종 948.8억(2022-03-30, 면제) + 후순위 4건 실재 |

> 티켓의 `issued_source: "bs_transposed"` 폴백 가설은 **오답**이다. 그 필드는 `wire_` 이전
> 레거시 잔재이고 소진율 계산에 쓰이지 않는다(분자는 `data/bonds/` per-bond 에서만 온다).

### §1 전수 확인 — 몇 개사가 틀렸나

**39사 × 2파일 = 78행 전수 필드단위 대조.** 회사 결측·초과 0. 어긋난 회사 **5사 / 25필드**뿐이고
전부 `배포본 0 → 빌더 값 있음` 한 방향이다(반대 방향 0건 = 배포본에만 있던 값은 없다 → 통째 교체로
잃는 것 없음).

| 파일 | 회사 | 어긋난 필드 수 | 화면에 나오나 |
|---|---|---|---|
| tier1 | KR0050 하나손해보험 | 6 | ✅ |
| tier1 | KR0076 아이엠라이프생명보험 | 1 (`tier1_grandfathered_hybrid_eok`) | ❌ (소진율은 원래 0 이 정답 — 전액 pre-2023 면제) |
| tier2 | KR0049 악사손해보험 | 1 (`new_subordinated_gross_eok`) | ❌ (call 2025-12-31 이 as-of 이전이라 인정액 0 = 소진율 0 이 정답) |
| tier2 | KR0050 하나손해보험 | 3 | ✅ |
| tier2 | KR0076 아이엠라이프생명보험 | 8 | ✅ |
| tier2 | KR1011 IBK연금보험 | 6 | ✅ |

> 티켓/오케 발주가 "3사 tier1 소진율 0" 이라고 본 것은 tier1·tier2 혼동이다. **tier1 에서 실제로
> 화면이 바뀌는 회사는 하나손해보험 1사뿐**이고, 아이엠라이프·IBK연금의 tier1 0.0% 는 정답이다
> (전자는 전액 경과조치 면제, 후자는 신종 발행 자체가 없다).

### §1 화면 숫자 before/after (K-ICS.html 자본증권 도넛 — `updateDonutPanel` L906-917)

| 회사 | 패널 | 항목 | before | after |
|---|---|---|---|---|
| 하나손해보험 | tier1 | 소진율(도넛) | **0.0%** | **100.0%** |
| 하나손해보험 | tier1 | 발행액 | 0억 | 1,000억 (한도 693.9억, SCR×15%) |
| 하나손해보험 | tier2 | 소진율(도넛) | **0.0%** | **13.2%** |
| 하나손해보험 | tier2 | 인정액 | 0억 | 306.1억 (한도 2,313억) |
| 아이엠라이프생명보험 | tier2 | 소진율(도넛) | **0.0%** | **40.6%** |
| 아이엠라이프생명보험 | tier2 | 인정액 | 0억 | 1,324.3억 (한도 3,262.5억) |
| IBK연금보험 | tier2 | 소진율(도넛) | **0.0%** | **22.2%** |
| IBK연금보험 | tier2 | 인정액 | 0억 | 797.8억 (한도 3,598억) |

화면에 안 나오는 나머지 17필드(면제분·gross·overflow 등)도 같이 맞췄다. 한도(분모)는 before/after
동일 — 바뀐 것은 분자뿐이다. 하나손해 tier1 은 `utilization_pct_raw` 144.1% 를 owner 결정대로
100 에서 자른 값이다(`utilization_pct_strict` 216.2% 는 SCR×10% 기준 참고치).

### §1 조치

1. **`scripts/sync_tier_utilization_to_deploy.py` 신설** — 빠져 있던 조립 단계 그 자체.
   기본은 dry-run(필드 단위 전건 열거), `--apply` 로 반영. 배포본 포맷(indent=1 · CRLF · BOM 없음)을
   보존해 **git diff 가 값 25줄만** 나온다(포맷 churn 0). 다음 분기·다음 소스 갱신 때 같은 사고가
   반복되지 않게 하는 것이 목적이다.
2. 두 배포본에 반영. 재실행 → `차이 없음 (in sync)`.
3. `emit_capsec_provenance.py --check` → `0 sidecar(s) out of sync` (사이드카는 분기·계보만 담고
   회사별 값을 담지 않아 재발행 불요).

### §1 등재 해제 — 했다

`data/_gold/live_artifact_baseline.json` 에서 `TIER_DEPLOYED_VALUE_DIFFERS` **4건 전부 삭제**
(+`_counts` 2키 삭제, `_promote` 라우팅 문장에서 tier 절 제거). 근거는 등재부 `_promote` (1) —
게이트가 `BASELINE STALE 4건` 으로 알려준 뒤 지웠다.

```
수정 전: RED=0  YELLOW(baselined)=1086  STALE_BASELINE=0
수정 후: RED=0  YELLOW(baselined)=1082  STALE_BASELINE=4   ← 등재부가 거짓말 시작
해제 후: RED=0  YELLOW(baselined)=1082  STALE_BASELINE=0   ← exit 0
```

---

### §2 NB_CSM_multiple 2026.2Q — **재생성 불가, 등재 31건 유지**

**할 수 없다. 원천이 없다.** 하고 싶어서 안 한 것이 아니라 빌더가 뜨지 않는다.

`scripts/build_nb_csm_multiple.py` 의 분모는 `data/kidi/premium_summary.json`(KIDI 월납월초)인데:

| 확인 | 결과 |
|---|---|
| `data/kidi/premium_summary.json` | **디스크에 없다.** `find data -name "premium_summary*"` → 0건. gitignore 대상이라 git 복구도 불가 |
| `data/kidi/FY2026_Q2/` | **없다.** 있는 것은 FY2023_Q1 ~ FY2026_Q1 |
| 빌더 동작 | `load_wolnap()` 이 `KIDI.read_text` 에서 즉사. (다행히 `OUT.write_text` 이전이라 실행해도 배포본이 깨지지는 않지만, 돌릴 이유가 없다) |
| `CSM_waterfall.json` 2026.2Q | 23사 있음 — **분자만 있고 분모가 없는 상태** |

즉 지금 강행하면 2026.2Q 행은 생기되 `월납월초보험료_*`·`신계약CSM배수_*` 가 전부 null 이라
**버블맵 Y축(NB배수)이 그려지지 않는다** — 결측 31건이 "배수 null 31건"으로 모양만 바뀐다.
게다가 이 빌더는 파일을 통째로 새로 쓰므로, 분모 없이 돌리면 기존 2023~2026.1Q 의 월납·배수까지
전부 날아간다(마스터 통째 read-modify-write 유실형).

**막힌 지점 = KIDI 재수집.** owner 가 재수집을 보류시킨 사안이라(publishing 이 임의로 재요청하지
않는다) **owner 판단으로 올린다.** 그때까지 `NB_CENSUS_MISSING` 31건은 등재부에 그대로 둔다 —
등재 사유를 "배포본이 한 분기 뒤처짐"에서 **"KIDI 원천 부재로 재생성 불가"**로 읽어 달라(사유 문구
자체는 validation 소유라 손대지 않았다).

부수 확인: 나머지 3건(연차공시사 4Q 결측)도 같은 이유로 이번에 손대지 않았다.

---

### 검증

| 항목 | 결과 |
|---|---|
| `scripts/sync_tier_utilization_to_deploy.py` (재실행) | tier1·tier2 모두 `차이 없음 (in sync)` |
| `scripts/validate_live_artifacts.py` | `RED=0 STALE_BASELINE=0` exit 0 |
| `scripts/emit_capsec_provenance.py --check` | 0 out of sync |
| `git diff` 범위 | `kics_tier1_utilization.json`(14줄) · `kics_tier2_utilization.json`(36줄) · `live_artifact_baseline.json` — **HTML 무수정** |
| 인코딩 | 편집 파일 전부 UTF-8 BOM 없음 |
| `pytest tests/test_deploy_assets.py tests/test_push_gate_wiring.py` | 55 passed / 1 skipped |
| `scripts/prepush_check.py` | **내 변경분 기준 exit 0** — 아래 단서 |

**게이트 단서 (숨기지 않는다).** 내 변경(배포본 2 + baseline)만 워킹트리에 있던 상태의 전체 게이트
실행은 **exit 0** 이었다(`RED=0 · K-ICS clear · domain pass · inbox 위반 0 · offline tests 198 passed`).
그 뒤 문서·스크립트 편집을 마치고 **확인용으로 한 번 더 돌린 실행은 exit 2** 인데, 그 사이
**다른 세션이 `PL_breakdown.json` · `data/_gold/user_pl_cells.json` 을 수정**했다(KR0070 에이비엘생명
item7 재계산, `inbox/parser/20260825T1120Z`). 실패는 `tests/test_master_tables_golden.py` **한 건**이고
델타는 **`pl_bridge:2503P/26F → 2513P/16F`** 하나뿐이다 — PL_BRIDGE 실패 10건이 통과로 바뀐 것,
즉 **그 세션이 고친 결과가 골든에 아직 반영되지 않은 것**이다.

- 내 변경집합은 tier 배포본 2개 + baseline + 문서 + 신설 스크립트라 **PL 축에 입력을 주지 않는다.**
  (`coverage_hole` · `closing` · `crosscheck` · `zero_legs` 등 나머지 카운트는 전부 골든과 일치)
- 골든 재생성(`--update`)은 **그 수정의 소유자(parser/ifrs17) 몫**이다. 남의 레인 골든을 내가
  재생성하면 진행 중인 작업을 반쯤 박제하게 된다.
- 즉 **지금 트리가 BLOCKED 인 것은 사실이고, 그 원인은 이 티켓이 아니다.**

**push 안 함 · commit 안 함** — owner 승인은 오케스트레이터가 받는다.

> 주의(공유 워킹트리): 이 세션과 무관하게 `scripts/validate_data_contract.py` ·
> `data/_gold/user_pl_cells.json` 이 다른 세션에서 수정 중이다. 커밋 시 내 3파일 +
> `scripts/sync_tier_utilization_to_deploy.py` 만 골라 담을 것.

### 남는 것 (validation 재확인 요청)

- `TIER_DEPLOYED_VALUE_DIFFERS` 는 이제 구조적으로 0 이어야 한다 — `sync_tier_utilization_to_deploy.py`
  를 배포 절차에 넣었으니, 다음 분기에 이 룰이 다시 뜨면 **조립을 건너뛴 것**이다.
- §2 는 미해결. 라우팅은 publishing 이 아니라 **KIDI 수집(downloader) + owner 승인**이다.
