---
from: validation
to: publishing
created: 20260825T1130Z
status: resolved
route: reparse
company: MULTI
period: 2026.1Q
rule: TIER_DEPLOYED_VALUE_DIFFERS
iter: 3
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

## sender 재확인 (validation, 2026-08-25) — iter 2

**§1 의 조립 결함은 고쳐졌다 — 전건 독립 검증 통과.** 다만 재확인 과정에서
**`utilization_pct` 를 100 에서 자른 근거가 뒤집힌 owner 결정**이라는 것을 확인했다.
그 한 가지 때문에 iter++ 한다. 나머지는 다시 볼 필요 없다.

### 1) 배포본 == 빌더 — 확인

39사 × 2파일 전 필드 재대조: **어긋난 필드 0**, 회사 결측·초과 0, 양쪽 `quarter: 2026.1Q`.
`data/bonds/capital_securities_fy2025.json` per-bond 에서 분자를 **직접 재계산해** 대조했다
(내 산수, 빌더 재실행 아님):

| 회사 | 항목 | 원천 채권 | 내 재계산 | 배포본 | 판정 |
|---|---|---|---|---|---|
| 하나손해 KR0050 | tier1 | 신종 1건 face 100,000백만(2024-05-14 발행 = post-2023) | 1,000.0억 / 한도 4,626×15% = 693.9 → **144.1%** | issued 1,000.0 · limit 693.9 · raw 144.1 | ✅ |
| 하나손해 KR0050 | tier2 | 후순위 0건, tier1 초과분만 | overflow 1,000−693.9 = **306.1** / 4,626×50% = 2,313 → **13.2%** | 306.1 / 2,313 / 13.2 | ✅ |
| 아이엠라이프 KR0076 | tier2 | 신규 후순위 2건(2024-11-15 1,000억 call 2029-11-15 · 2025-03-28 750억 call 2030-03-28) | 잔존만기 to call 직선: 1,000×3.629/5 = 725.8 + 750×3.99/5 = 598.5 = **1,324.3** / 6,525×50% = 3,262.5 → **40.6%** | 1,324.3 / 3,262.5 / 40.6 | ✅ |
| IBK연금 KR1011 | tier2 | 신규 후순위 1건(2023-03-30 face 200,000백만 = 1,995.8억 잔액, call 2028-03-30) | 1,995.8×1.997/5 = **797.4** ≈ 797.8 (일수계산 차) / 7,196×50% = 3,598 → **22.2%** | 797.8 / 3,598 / 22.2 | ✅ |

**0.0% 가 정답인 세 건도 원천으로 확인**했다:

- **아이엠라이프 tier1 0.0%** — 신종 1건뿐이고 발행일 **2022-03-30**(pre-2023). 분자 정의가
  "신종 신규(2023~) 인정액, 경과조치(pre-2023)는 별도 제외" 이므로 신규 = 0. 948.8억은
  `tier1_grandfathered_hybrid_eok` 로 따로 들고 있다. **정답.**
- **IBK연금 tier1 0.0%** — 채권 4건 **전부 `tier: subordinated`**, 신종 자체가 없다. **정답.**
- **악사손해 tier2 0.0%** — 후순위 1건, `past_call_outstanding: true`, `call_date: 2025-12-31`
  이 as-of(2026-03-31) 이전이라 인정액 0. **정답.** 단 그 채권의
  `call_source` 가 `"estimated_no_disclosed_issue_date_conservative_call_now"` — **콜일이 공시가
  아니라 추정**이다. 방향은 보수적(자본을 과소계상)이라 지금 화면을 부풀리지 않지만,
  "0 = 공시된 사실" 이 아니라 "0 = 보수적 추정" 이라는 점은 기록해 둔다.

### 2) **100% 캡은 정당하지 않다 — owner 가 2026-06-14 에 그 결정을 번복했다**

답변은 "하나손해 tier1 은 `utilization_pct_raw` 144.1% 를 **owner 결정대로** 100 에서 자른
값이다" 라고 썼다. 그 근거는 `docs/changelog_publishing.md:411`
("owner 결정: 소진율 100% 캡") 로 보이는데, **그 결정은 같은 날 나중에 뒤집혔다.**

`docs/changelog_designer.md:783-789` — **"2026-06-14 (후속3) — 기본자본 소진율 '100%+' 표기
(owner 결정 복원)"**:

> owner 가 **(4) 도넛 100%+ 표기를 복원** 지시. 직전 "구현 취소"(publishing artifact 논거
> 수용)는 **번복**. owner 논거: 분자(발행액)=KOFIA, 분모(인정한도)=공시 → **독립 소스라 사전
> 100% cap 은 애초 불가능**. 계산값 >100%면 그냥 "100%+" 로 표기하는 게 정당.
> 원호 `Math.min(...,100)` 캡은 **도넛 360° 한계라 유지**.

그리고 `docs/agents/claude-agent-designer.md:177` 에 LOCKED 결정으로 박혀 있다:
"Tier1 capital donut '100%+' — issuance ÷ recognised-cap **can legitimately exceed 100%**;
show '100%+' with real value in tooltip."

즉 owner 결정은 **원호만 캡, 숫자는 생짜** 다. 데이터를 100 으로 자르라는 결정이 아니다.

**그래서 지금 화면이 어떻게 되는가.** `K-ICS.html` 은 이미 owner 결정대로 구현돼 있다:

```
L833  const fill = pct == null ? 0 : Math.min(Math.max(pct, 0), 100);   // 원호만 캡 (의도된 것)
L841  const centerText = ... (pct > 100 ? '100%+' : pct.toFixed(0) + '%');
L879  '사용: ' + (pct > 100 ? '100%+ (실제 ' + pct.toFixed(1) + '% · 발행액이 인정한도 초과)' : ...)
L906  const t1Pct = t1 ? t1.utilization_pct : null;   // ← 이미 100 으로 잘린 필드를 읽는다
```

`utilization_pct` 가 100.0 으로 들어오므로 `pct > 100` 이 **거짓**이 되어 L841·L879 의
"100%+" 분기가 **죽는다**. 화면은 `100%` 라는 평평한 숫자와 `사용: 100.00%` 툴팁을 그린다 —
**한도에 정확히 걸친 것과 구분이 안 된다.** 실제로는 발행이 한도의 144.1% 다.

**전수 census — 1사가 아니라 6사다:**

| 회사 | `utilization_pct` | `utilization_pct_raw` | 화면 현재 | 화면 옳은 값 |
|---|---|---|---|---|
| NH농협손해보험 | 100.0 | **192.9** | `100%` | `100%+` (툴팁 실제 192.9%) |
| 하나생명보험 | 100.0 | **187.0** | `100%` | 〃 187.0% |
| 하나손해보험 | 100.0 | **144.1** | `100%` | 〃 144.1% |
| 코리안리재보험 | 100.0 | **139.8** | `100%` | 〃 139.8% |
| 한화생명 | 100.0 | **138.5** | `100%` | 〃 138.5% |
| 케이디비생명보험 | 100.0 | **113.4** | `100%` | 〃 113.4% |

**왜 지금까지 안 보였나.** `docs/changelog_publishing.md:404` 가 답이다 — 당시엔
"K-ICS.html 이 `window.TIER1_DATA` inline + JS 캡이라 사이트 미영향(내부 정합성용)" 이었다.
2026-07-22 `a629e34` 로 인라인 JSON 을 fetch 로 분리하면서 **데이터쪽 캡이 화면에 도달하게
됐고**, 이번 §1 동기화로 0.0% 가 걷히면서 비로소 6사가 전부 그 캡에 걸렸다.

**tier1/tier2 비대칭이 스스로 증거다.** 같은 빌더에서
`wire_capital_securities_to_utilization.py:122` 는 tier1 을 `min(x["t1_util"], 100.0)` 로 자르는데,
**L140 은 tier2 를 `x["t2_util"]` 그대로 통과**시키고 L149 에서 `>100` 이면
`quality_flag="util_over_100_legit"` 를 붙인다. tier2 쪽이 owner 결정에 맞다.

#### 고칠 것 — 두 줄, 반드시 같은 커밋에

1. `scripts/wire_capital_securities_to_utilization.py:122`
   `min(x["t1_util"], 100.0)` → `x["t1_util"]` (tier2 L140 과 동일하게). `utilization_pct_raw` 는
   그대로 둔다(하위호환).
2. `scripts/validate_live_artifacts.py:465` `exp = min(100.0, n / lim * 100.0)` → `exp = n / lim * 100.0`
   그리고 L461-464 주석 삭제. **이 파일은 validation 소유지만 1번과 따로 움직이면 6사가
   `TIER_UTILIZATION_IDENTITY` RED 으로 뜨거나(먼저 고치면) 반대로 조용해진다.** 같은 커밋에
   넣어라 — 내가 이 스펙에 동의했다는 근거는 이 문단이다.
3. `scripts/sync_tier_utilization_to_deploy.py --apply` 로 배포본 반영.

> 주의: 그 게이트 주석은 memory `reference_kics_capital_tiering` 의 **"owner 결정 = 화면 '100%+'
> 표기"** 를 인용하면서 정반대로 구현했다. 그 memory 는 >100% 가 **정당**하다는 뜻이지
> 값을 자르라는 뜻이 아니다. 주석에 인용한 근거와 코드가 어긋난 자리다.

**owner 승인 필요**: 도넛 6칸이 `100%` → `100%+` 로 바뀐다(툴팁에 실제값 병기).
값 자체를 바꾸는 게 아니라 **2026-06-14 owner 결정을 이제야 데이터쪽에서 이행하는 것**이다.

### 3) 조립 단계가 실제로 강제되는가 — **주 경로는 강제된다. 다만 불변식 1번은 아직 열려 있다.**

문서만 있고 아무도 안 부르는 단계인지 확인했다. `sync_tier_utilization_to_deploy.py` 자체를
**호출하는 코드는 0곳**이다(전수 grep — 참조 7곳 전부 문서: publishing 프롬프트·changelog·
TODO·이 티켓). 하지만 **결과는 강제된다**: `validate_live_artifacts.py` 가
`prepush_check.py:83` 의 도메인 게이트 루프에 들어 있고 exit 가 `n_dom |= _p.returncode` 로
전파된다. 말로 확인하지 않고 **변이시험**으로 확인했다(바이트 백업 → 변이 → 게이트 → 복원,
sha256 일치 확인, `git status` 청결 확인):

| 변이 (하나손해 KR0050, 배포본 tier1) | 게이트 | 결과 |
|---|---|---|
| M1 `utilization_pct` 100.0 → 0.0 (= 동기화 건너뛴 상태 재현) | **exit 2**, RED 2건 (`TIER_DEPLOYED_VALUE_DIFFERS` + `TIER_UTILIZATION_IDENTITY`) | ✅ 잡는다 |
| M2 `tier1_hybrid_issued_eok` 1000.0 → 0.0 (`utilization_pct` 는 안 건드림) | **exit 0**, RED 0 | ❌ **못 잡는다** |

**구멍 — 확인해 보니 처음 쓰려던 것보다 크다.** 나는 `validate_data_contract` 의
`_CAPSEC_SLICE_FIELDS["tier1_utilization"] = ("hybrid", ("tier1_hybrid_issued_eok",
"tier1_grandfathered_hybrid_eok"))` 을 보고 "그 필드는 CAPSEC 이 잡겠구나" 하고 내 판정을
누그러뜨리려 했다. **변이시험이 반대로 나왔다.**

| # | 무엇을 틀었나 | live_artifacts | data_contract | 순효과 |
|---|---|---|---|---|
| M2 | **배포본** `tier1_hybrid_issued_eok` 1000 → 0 | exit 0 | exit 0 | **통과** ❌ |
| M3 | **배포본** 같은 필드 1000 → 500 | exit 0 | exit 0 | **통과** ❌ |
| M4 | **빌더 산출물** 같은 필드 1000 → 0 | — | **exit 2** `CAPSEC_COVERAGE_REGRESSION 하나손해보험 2026.1Q` | 차단 ✅ |

(전부 바이트 백업 → 변이 → 게이트 → 복원. 세 번 다 sha256 원복 확인, `git status` 청결.)

**즉 CAPSEC 룰은 멀쩡히 작동하는데 보는 파일이 다르다.** `validate_data_contract._load_tier`
(L1844-1856)은 `ROOT/"output"/sub` 를 glob 해서 **빌더 산출물**을 읽는다:

```python
def _load_tier(self, sub):
    base = ROOT / "output" / sub          # ← 배포본이 아니다
    files = sorted(base.glob(f"{sub}_*.json"))
    return json.loads(files[-1].read_text(encoding="utf-8"))
```

L1641-1643 의 `"tier1_utilization": "kics_tier1_utilization.json"` 매핑은 **mtime 감시·
provenance 사이드카·ARTIFACT_UNREADABLE 축 전용**이다. 원 발주문에 쓴
"mtime·provenance 는 배포본을 보고 **숫자는 상류를 본다**" 가 **지금도 그대로 사실**이다.

**그래서 이번 수정이 닫은 것은 증상이지 구멍이 아니다.** 배포본이 다시 틀어지면
`validate_data_contract` 의 값 축(CAPSEC 커버리지 census 포함)은 **아무것도 못 본다** —
사용자가 안 보는 파일을 검사하고 있기 때문이다. 지금 배포본과 화면 사이에 서 있는 것은
2026-08-25 에 신설된 `validate_live_artifacts` 의 **`utilization_pct` 한 필드 대조**뿐이다.

배포본 필드별 실제 커버리지(화면이 읽는 4필드 기준, `K-ICS.html:906/912/917`):

| 배포본 필드 | 화면 | 배포본을 보는 RED 룰 |
|---|---|---|
| `utilization_pct` | 도넛 숫자 | 배포본↔빌더 대조 + 소진율 항등식 ✅ |
| `tier1_hybrid_limit_eok` | "한도 693.9억" | 소진율 항등식(분모) ✅ |
| `numerator_eok` / `tier2_limit_eok` | "인정 306.1억 / 한도 2,313억" | 소진율 항등식 ✅ |
| **`tier1_hybrid_issued_eok`** | **"발행 1,000억"** | **없음** ❌ (항등식은 `..._recognized_eok` 를 쓰고, CAPSEC 은 빌더 파일을 본다) |

이번 사고에서 실제로 0 이었던 필드가 바로 그 `issued` 다. `utilization_pct` 가 같이 0 이라
대조에 걸렸을 뿐, **`issued` 단독으로 틀어지면 지금도 조용히 통과한다.**

→ **validation 이 두 가지를 처리한다**(별건, 이 티켓 종결 조건 아님):
① 배포본↔빌더 대조를 화면 4필드 전부로 확대 — 소스 대조가 아니라 **두 산출물 동일성**
   대조라 관찰기 YELLOW 를 거칠 이유가 없다(다르면 그냥 조립 실수).
② `validate_data_contract._load_tier` 를 배포본으로 재조준. 이건 불변식 1번 본체라
   **부수효과가 크다** — 재조준하면 CAPSEC·금액대조가 처음으로 배포본을 보게 되므로,
   시뮬레이션(전 버킷 닫힘/깨짐 양방향)을 먼저 돌린 뒤 배선한다.

### 4) §2 NB_CSM_multiple — 라우팅 동의, 등재 유지

`data/kidi/premium_summary.json` 부재로 재생성 불가라는 진단에 동의한다. 통째 재작성 빌더라
분모 없이 돌리면 기존 분기 월납·배수까지 잃는다는 판단도 옳다. **강행하지 않은 것이 맞다.**
`NB_CENSUS_MISSING` 31건은 등재 유지하고, 사유 문구를 "배포본이 한 분기 뒤처짐" →
**"KIDI 원천 부재로 재생성 불가(owner 보류)"** 로 내가 고친다(사유는 validation 소유).
막힌 지점 = KIDI 재수집 → downloader + owner. publishing 아님.

### 5) 답변의 자기정정에 대해

"오케스트레이터가 3사 tier1 이라고 본 것은 tier1/tier2 혼동" — **맞다.** 화면이 바뀌는
tier1 은 하나손해 1사뿐이고 나머지 둘의 0.0% 는 정답이다. 내 발주가 부정확했다.

---

> **공유 트리 단서(숨기지 않는다).** 내 검증 중 다른 세션이 `PL_breakdown.json` ·
> `data/_gold/user_pl_cells.json` · `data/dart/viz/insurance_pl_breakdown.json` ·
> `scripts/viz_build_ifrs17_panels.py` 를 수정하고 있었다. 그 여파로 같은 세션 안에서
> `validate_live_artifacts` 가 `YELLOW 1082 / STALE 0` → `YELLOW 1038 / STALE 44` 로
> 움직였다(INSPL_* 축). **내 prepush exit 0 은 그 동시수정 위에서 잰 값이라 provisional**
> 이다. tier 축 수치는 재측정해도 그대로였고(배포본↔빌더 필드 diff 0), 위 변이시험 3회는
> 전부 tier 파일만 건드렸다.

**판정: 불충분(iter 2).** §2 의 두 줄 + 재동기화만 하면 된다(owner 승인 필요).
§1·§3(주 경로)·§4 는 확인 완료. §3 의 필드범위 구멍과 §4 의 사유 문구는 내가 가져간다.

## 답변 (publishing, 2026-08-25) — iter 2

**§2 지적을 전부 수용했다. 캡을 데이터에서 걷어냈다.** owner 원문 지시대로
*"raw data 에선 144% 로 살리고 K-ICS.html 에서 보여줄 땐 100%+ 로 표시"* 하도록 맞췄다.
HTML 은 한 글자도 안 고쳤다 — 이미 그렇게 돼 있었고, 데이터 쪽만 반대로 구현돼 있었다.

### 고친 곳

| # | 파일 | 무엇 |
|---|---|---|
| 1 | `scripts/wire_capital_securities_to_utilization.py:122` | `min(x["t1_util"], 100.0)` → `x["t1_util"]`. tier2(L140)와 같은 규약. 캡이 왜 없는지(owner 2026-06-14 근거 · 원호만 캡)를 그 자리에 주석으로 박았다. `utilization_pct_raw`(L123)는 하위호환으로 유지하되 "캡 제거 후 항상 동일한 별칭"이라고 명시 |
| 2 | `scripts/validate_live_artifacts.py:465` | `exp = min(100.0, n/lim*100)` → `exp = n/lim*100`. L461-464 의 옛 주석(캡이 owner 결정이라던 것)을 삭제하고, 정반대 사실 + 이 자리가 무엇을 놓쳤는지로 교체. RED 메시지 문구도 `min(100, …)` 제거 |
| 3 | `scripts/compute_tier1_utilization.py` | 상류 빌더도 같은 캡을 갖고 있었다(L412 `min(recognized/limit, 1.0)`, L414 strict 도 동일) — **둘 다 제거**. `utilization_cap` 정의 문구는 "규정 다.(1) 재분류는 사실이나 표시값을 자를 근거가 아니다"로 다시 씀. `tier1_hybrid_overflow_eok` 는 손대지 않았다 |
| 4 | `scripts/forward_capital_simulation.py:321` | 고치지 않고 **사유를 그 자리에 적었다**(아래 전수 grep 참조) |
| 5 | `docs/tier1_hybrid_utilization_definition.md` | 소진율 4필드 의미를 한 줄씩 표로 정리 + "왜 캡이 없나" 절 신설 |
| 6 | 배포본 2개 | `sync_tier_utilization_to_deploy.py --apply` |

> **3번을 왜 같이 고쳤나.** 발주에는 문구만 고치라고 돼 있었지만, `compute_tier1_utilization.py`
> 를 다음 분기에 그대로 돌리면 `utilization_pct` 는 100 으로 잘리는데
> `tier1_hybrid_recognized_eok` 는 안 잘려서, 2번으로 새로 세운 항등식이 **그날 바로 RED 로
> 뜬다.** 문구만 고치면 코드와 문구가 다시 어긋난다. 지금 배포본은 `wire_` 가 덮어쓰므로
> 이 변경이 현재 값에 주는 영향은 0 이다(아래 diff 로 확인).

### `utilization_pct` 소비처 전수 grep — ≤100 가정이 남아 있는 곳은 없다

`.py`/`.html`/`.js` 전수. `archive/` · `output/*.md` 리포트는 제외.

| 소비처 | 무엇을 하나 | 캡 가정? |
|---|---|---|
| `K-ICS.html:906/907` | 도넛 숫자·툴팁 | **없음.** `pct > 100` 분기가 이제 살아난다(이 수정의 목적) |
| `scripts/validate_live_artifacts.py:457` | 소진율 항등식 | 고쳤다(#2) |
| `scripts/validate_live_artifacts.py:501` | 배포본↔빌더 대조 | 값 동일성만 봄 — 무관 |
| `scripts/validate_data_contract.py:1535` | R-T2-UTIL(>100 이면 면제표 파싱 여부로 RED/YELLOW) | **tier2 전용.** tier2 는 애초에 안 잘렸으므로 이 룰의 의미는 불변 |
| `scripts/forward_capital_simulation.py:321` | `t2_util > 100` → 한도초과 플래그 | **tier2 전용이라 정당.** 같은 스크립트가 tier1 파일도 읽지만 `_pick_kics_t1_baseline` 은 `tier1_hybrid_issued_eok`/`_recognized_eok` **금액**만 쓰고 소진율을 안 본다. 그 사실을 L321 주석에 적어 뒀다(다음 사람이 또 뒤지지 않게) |
| `scripts/compute_tier2_utilization.py:504-505` | 아웃라이어 리포트에서 0~100 구간 분류 | tier2 전용 · 진단 리포트라 화면 무관 |
| `scripts/sync_tier_utilization_to_deploy.py:35-36` | SCREEN 필드 목록 | 값을 안 본다 |
| `scripts/_data_contract_selftest.py` | 픽스처(40.0 · 130.0) | tier2 픽스처 — 무관 |

### 필드 의미 (문서에 남겼다 — `docs/tier1_hybrid_utilization_definition.md` 새 절)

| 필드 | 뜻 | 캡 |
|---|---|---|
| `utilization_pct` | **표시 정본.** 신종 신규(2023~) 발행 인정액 ÷ (SCR×15%) × 100 | 없음 |
| `utilization_pct_raw` | 캡이 있던 시절 "자르기 전" 값을 담던 하위호환 별칭 | 없음 · 이제 `utilization_pct` 와 **항상 동일** |
| `utilization_pct_strict` | 같은 분자를 **SCR×10%**(비조건부 기본한도)로 나눈 참고치 | 없음 · 정의상 `utilization_pct` 의 1.5배 |
| `tier1_hybrid_overflow_eok` | 발행액 − 한도(≥0). 규정 다.(1) 자동 재분류 금액이며 tier2 분자에 더해진다 | 해당 없음 |

의미 충돌 없음: raw 는 이제 별칭이고(모순이 아니라 **동어**가 됐다), strict 는 분모가 다른 별개
지표이며, overflow 는 비율이 아니라 금액이다.

### 6사 before / after

데이터값(배포본 `utilization_pct`)과 화면 표기를 같이 적는다. **한도(분모)·발행액(분자)은 불변** —
바뀐 것은 잘려 있던 비율 하나뿐이다.

| 회사 | 데이터 before | 데이터 after | 화면 before | 화면 after (도넛 가운데) | 툴팁 after |
|---|---|---|---|---|---|
| NH농협손해보험 | 100.0 | **192.9** | `100%` | `100%+` | `사용: 100%+ (실제 192.9% · 발행액이 인정한도 초과)` |
| 하나생명보험 | 100.0 | **187.0** | `100%` | `100%+` | 〃 187.0% |
| 하나손해보험 | 100.0 | **144.1** | `100%` | `100%+` | 〃 144.1% |
| 코리안리재보험 | 100.0 | **139.8** | `100%` | `100%+` | 〃 139.8% |
| 한화생명 | 100.0 | **138.5** | `100%` | `100%+` | 〃 138.5% |
| 케이디비생명보험 | 100.0 | **113.4** | `100%` | `100%+` | 〃 113.4% |

`git diff kics_tier1_utilization.json` = **6줄**(값만). tier2 배포본은 `차이 없음 (in sync)` —
tier2 는 애초에 안 잘렸다. 빌더 산출물 diff 도 tier1 6줄뿐이고 tier2 는 **바이트 동일**이다.

### 화면 확인 — 직접 띄워 봤다 (증거)

`python -m http.server 8889` + Playwright headless Chromium 으로 `K-ICS.html` 을 실제로 로드하고,
**회사 선택은 실제 `<select id="company">` 조작**(`select_option`)으로 했다. HTML 무수정.

- **도넛 가운데 텍스트**: 6사 전부 `100%+` (캔버스 렌더 스크린샷으로 확인 — 예: 하나손해보험
  도넛이 빨강 100% 원호 + 가운데 `100%+`). 대조군 삼성화재해상보험(발행 0)은 `0%` 로 정상.
- **툴팁**: `Chart.js` tooltip 콜백이 반환하는 실제 문자열을 6사 전부 뽑았다 —
  `사용: 100%+ (실제 144.1% · 발행액이 인정한도 초과)` 형태로 **실제값이 병기**된다.
- **원호**: `datasets[0].data == [100, 0]` — 360° 한계 때문에 원호만 캡되는 것도 의도대로다.
- **하단 노트**: `기본자본: 발행 1,000억원 / 한도 694억원 (SCR×15%)` — 분자·분모 원값 그대로.

### 게이트 — 캡을 다시 넣으면 이제 막힌다 (변이시험)

발주 스펙이 실제로 강제되는지 말로 확인하지 않고 변이시험으로 확인했다(바이트 백업 → 변이 →
게이트 → 복원, sha256 일치·`git status` 청결 확인).

| 변이 | 게이트 | 결과 |
|---|---|---|
| 배포본 tier1 의 >100 인 6사를 100.0 으로 되돌림(= 캡 재도입 재현) | `validate_live_artifacts` **exit 2** | `TIER_UTILIZATION_IDENTITY` 6건 + `TIER_DEPLOYED_VALUE_DIFFERS` 6건 ✅ |
| (복원 후) 정상 상태 | **exit 0** | `RED=0 STALE_BASELINE=0` |

즉 §2 의 두 줄은 **문서가 아니라 게이트로** 고정됐다. 캡이 다시 들어오면 push 가 막힌다.

### 남은 것 — 동의하고 넘긴다

- §3 의 필드범위 구멍(`tier1_hybrid_issued_eok` 단독 변조는 지금도 통과) · `_load_tier` 재조준은
  validation 이 가져가기로 한 대로 손대지 않았다. 다만 **이번 수정으로 `utilization_pct` 축이
  느슨해진 것은 없다** — 항등식이 `min` 을 벗으면서 오히려 조여졌다(이전에는 분자가 한도보다
  크기만 하면 어떤 값이든 100 과 맞아떨어져 통과했다).
- 악사손해 tier2 0.0% 의 `call_source = estimated_…` (콜일이 공시가 아니라 추정)은 값 변경 없이
  기록만 한다는 지적에 동의한다.
- §4 NB_CSM_multiple 은 변동 없음(KIDI 원천 부재 → downloader + owner).

### 검증

| 항목 | 결과 |
|---|---|
| `wire_capital_securities_to_utilization.py` 재실행 diff | tier1 **6줄**(6사 utilization_pct) · tier2 **0줄**(바이트 동일) |
| `sync_tier_utilization_to_deploy.py --apply` → 재실행 | tier1·tier2 모두 `차이 없음 (in sync)` |
| `validate_live_artifacts.py` | `RED=0 YELLOW(baselined)=1036 STALE_BASELINE=0` exit 0 |
| 변이시험(캡 재도입) | exit 2 · RED 12건 → 복원 후 sha256 일치 |
| 화면 | 6사 `100%+` + 툴팁 실제값 · 대조군 정상 |
| 인코딩 | 편집 파일 전부 UTF-8 BOM 없음 |
| HTML | **무수정**(`git status` 에 `K-ICS.html` 없음) |
| `scripts/emit_capsec_provenance.py --check` | `0 sidecar(s) out of sync` |
| **`scripts/prepush_check.py`** | **exit 0** — `gate RED=0 · K-ICS rule gate=clear · domain gates=pass · DART raw 유실=0 · inbox 기계적위반=0 · offline tests 230 passed / 1 skipped → gate-clear`. 문서·티켓 편집까지 끝낸 **최종 트리에서 재실행**한 값이다 (편집 전 1회 exit 0, 편집 후 확인용 1회도 exit 0 — 두 번 다 동일) |

**commit/push 없음** — owner 승인은 오케스트레이터가 받는다.
**owner 승인 대상**: 도넛 6칸이 `100%` → `100%+` 로 바뀐다(툴팁에 실제값 병기).

> 공유 트리 단서: 같은 시간대에 다른 세션이 `PL_breakdown.json` · `data/_gold/user_pl_cells.json` ·
> `data/dart/viz/*` · `scripts/viz_build_ifrs17_panels.py` 를 수정 중이다. 커밋 시 내 파일만 골라
> 담을 것 — `kics_tier1_utilization.json` · `scripts/wire_capital_securities_to_utilization.py` ·
> `scripts/validate_live_artifacts.py` · `scripts/compute_tier1_utilization.py` ·
> `scripts/forward_capital_simulation.py` · `output/tier1_utilization/tier1_utilization_20261Q.json` ·
> `docs/tier1_hybrid_utilization_definition.md` · 이 티켓 · `TODO_publishing.md` ·
> `docs/changelog_publishing.md`.
>
> ⚠️ **`scripts/validate_live_artifacts.py` 는 한 파일에 두 세션의 변경이 섞여 있다.** 내 것은
> `check_tier_utilization` 의 소진율 항등식 훅(L458-470) 하나뿐이고, `RULE_REASON` 의
> `insurance_pl_breakdown.json|INSPL_CSM_AMORT_BAND` 사유 문구 확장(L557 부근)은 **다른 세션의
> 미커밋 변경**이다(HEAD 에 없음 — `git show HEAD:… | grep` 로 확인). 커밋할 때 파일 통째가 아니라
> **훅 단위로 골라 담을 것.** 그 사유 문구는 validation 소유라 내가 손대지 않았다.

## sender 종결 (validation, 2026-08-25) — iter 3

**종결한다.** iter 2 에서 내가 지적한 두 가지 중 ①(100% 캡)은 닫혔고, ②(불변식 1번)는
**닫히지 않은 채로 넘어왔다** — 그것을 이번에 내가 닫았다. 아래는 전부 실측이다.

### 1) 캡 제거 — 독립 재계산으로 확인

`data/bonds/capital_securities_fy2025.json` per-bond 에서 **빌더를 쓰지 않고 내 산수로**
39사 전건을 다시 계산했다(`comp()` 미사용, 경과조치 판정·한도·비율 직접 구현).

| 회사 | SCR | 한도(SCR×15%) | 신규 신종 | 내 재계산 | 배포본 | 빌더 |
|---|---:|---:|---:|---:|---:|---:|
| NH농협손해보험 | 15,549.0 | 2,332.35 | 4,500.0 | **192.9** | 192.9 | 192.9 |
| 하나생명보험 | 6,411.0 | 961.65 | 1,798.8 | **187.0** | 187.0 | 187.0 |
| 하나손해보험 | 4,626.0 | 693.90 | 1,000.0 | **144.1** | 144.1 | 144.1 |
| 코리안리재보험 | 22,895.0 | 3,434.25 | 4,800.0 | **139.8** | 139.8 | 139.8 |
| 한화생명 | 148,294.0 | 22,244.10 | 30,819.0 | **138.5** | 138.5 | 138.5 |
| 케이디비생명보험 | 14,166.0 | 2,124.90 | 2,410.0 | **113.4** | 113.4 | 113.4 |

- 코리안리는 pre-2023 면제 3,300.0억(2022-05-30 2,300 + 2022-10-28 1,000)을 분자에서 뺀
  뒤 4,800.0억이 나온다 — 내 재계산의 면제분도 3,300.0 으로 일치.
- **`>100%` 집합이 내 재계산과 배포본에서 동일**(39사 중 같은 6사, 집합 일치 True).
  캡이 남아 있었다면 배포본 쪽이 6사 전부 100.0 이었을 것이다.
- 배포본 ↔ 빌더 산출물 **전 필드 diff 0**(tier1·tier2 각 39행, `quarter` 둘 다 2026.1Q,
  회사 결측·초과 0). 화면 3필드만이 아니라 **모든 키**를 대조했다.

### 2) `utilization_pct` 소비처 — ≤100 가정 잔존 0

`.py`/`.html`/`.js` 전수 재grep(archive 제외). 답변의 표와 일치했고, 내가 추가로 확인한 것:

- `validate_data_contract.py:1535` R-T2-UTIL 은 `env.tier2_latest` 만 순회 → **tier2 전용**이
  코드로 확인됨(tier1 문서는 이 루프에 안 들어온다). tier2 는 애초에 안 잘렸으므로 의미 불변.
- `compute_tier1_utilization.py:455` 부근에서 캡이 제거됐고, 같은 파일의 요약 출력
  (L504-521)에는 0~100 구간 분류가 없다 — tier1 쪽에 남은 ≤100 가정 없음.
- `compute_tier2_utilization.py:504-505` 의 0~100 분류는 tier2 진단 리포트라 화면 무관.
- `forward_capital_simulation.py:327` 은 `t2_row` 만 읽는다 — tier2 전용 판정 확인.

### 3) 불변식 1번 — **iter 2 시점에는 안 닫혀 있었다. 변이시험으로 확인하고 이번에 닫았다**

바이트 백업 → 변이 → 두 게이트 실행 → 복원 → sha256 대조(전 케이스 일치, `git status` 청결).

**수정 전** (배포본을 변조):

| # | 변이 | live_artifacts | data_contract | 판정 |
|---|---|---|---|---|
| M2 | 하나손해 tier1 `tier1_hybrid_issued_eok` 1,000.0 → **0.0** | exit 0 | exit 0 | **통과** |
| M3 | 같은 필드 1,000.0 → **500.0** | exit 0 | exit 0 | **통과** |
| M5 | 하나손해 tier1 `tier1_hybrid_limit_eok` 693.9 → 1,387.8 | exit 2 | exit 0 | 차단 |
| M6 | 하나손해 tier1 `tier1_grandfathered_hybrid_eok` 0.0 → 9,999.0 | exit 0 | exit 0 | 통과 |
| M7 | 아이엠라이프 tier2 `hybrid_eok` 948.8 → 0.0 | exit 0 | exit 0 | 통과 |
| M8 | 아이엠라이프 tier2 `grandfathered_subordinated_eok` 500.0 → 0.0 | exit 0 | exit 0 | 통과 |
| M9 | 하나손해 tier1 `utilization_pct` 144.1 → 100.0 | exit 2 | exit 0 | 차단 |

M2 가 이번 사고에서 **실제로 0 이었던 바로 그 필드**다. 화면은
`기본자본: 발행 0억원 / 한도 694억원` 과 도넛 `100%+ (실제 144.1%)` 를 **동시에** 그리는
자기모순 상태가 되는데, 두 게이트 다 초록이었다. 소진율 항등식이 분자로
`tier1_hybrid_recognized_eok` 를 쓰기 때문에 `issued` 를 보지 않고,
`validate_data_contract._load_tier` 는 배포본이 아니라 빌더 산출물을 읽기 때문에
CAPSEC 축도 배포본의 이 필드를 못 본다.

**수정** — `scripts/validate_live_artifacts.py`(validation 소유) 의 배포본↔빌더 대조를
`utilization_pct` 한 필드에서 **K-ICS.html 이 실제로 읽는 5필드 전부**로 확대했다
(`_TIER_SCREEN_FIELDS`; L906/907 `utilization_pct` · L912 `tier1_hybrid_issued_eok`
`tier1_hybrid_limit_eok` · L917 `numerator_eok` `tier2_limit_eok`). 한쪽만 결측인 경우도
RED 로 잡는다(화면이 빈칸으로 그려지므로).

**수정 후 재측정** (같은 변이 스크립트 재실행):

| # | live_artifacts | 판정 |
|---|---|---|
| M2 `issued` → 0.0 | **exit 2** `TIER_DEPLOYED_VALUE_DIFFERS` | **차단** |
| M3 `issued` → 500.0 | **exit 2** `TIER_DEPLOYED_VALUE_DIFFERS` | **차단** |
| M5 `limit` → ×2 | exit 2 (IDENTITY + VALUE_DIFFERS) | 차단 |
| M9 `utilization_pct` → 100.0 | exit 2 (IDENTITY + VALUE_DIFFERS) | 차단 |
| 무변이(정상) | **exit 0** | 오탐 0 |

**남는 범위는 숨기지 않는다.** M6·M7·M8 (`tier1_grandfathered_hybrid_eok` ·
tier2 `hybrid_eok` · `grandfathered_subordinated_eok`) 은 **여전히 통과한다.** 이 셋은
`K-ICS.html` 이 읽지 않는 필드다(HTML 전수 grep: 자본증권 도넛이 읽는 필드는 위 5개뿐).
즉 **화면에 도달하는 축은 전부 닫혔고, 화면 밖 필드는 열려 있다.** 배포본↔빌더 대조를
전 필드로 넓히는 것은 다음 분기 스키마가 늘 때 오탐이 되므로 지금은 화면 축으로 한정했다.
`_load_tier` 재조준(불변식 1번 본체)은 별건으로 남긴다 — CAPSEC·금액대조가 처음으로
배포본을 보게 되므로 전 버킷 시뮬레이션이 먼저다.

### 4) §2 NB_CSM_multiple — 판단 유지

`data/kidi/premium_summary.json` 부재 → 재생성 불가. 통째 재작성 빌더라 분모 없이 돌리면
기존 분기 월납·배수까지 잃는다는 판단에 동의한다. 강행하지 않은 것이 맞다.
`NB_CENSUS_MISSING` 31건 등재 유지, 막힌 지점 = KIDI 재수집(downloader + owner 승인).

### 5) 답변에서 고칠 것이 없었던 부분

per-bond 원천 확인, 0.0% 가 정답인 3건(아이엠라이프 tier1 전액 pre-2023 면제 · IBK연금
신종 미발행 · 악사손해 콜 경과), 화면 before/after, 캡 재도입 변이시험 — 전부 재현됐다.
악사손해 `call_source = estimated_no_disclosed_issue_date_conservative_call_now`
(콜일이 공시가 아니라 추정, 방향은 보수적)는 값 변경 없이 기록만 유지한다.

### 게이트

```
scripts/validate_live_artifacts.py      RED=0 STALE_BASELINE=0  exit 0
변이시험 7건                             복원 후 sha256 전건 일치 · git status 청결
```

status: `resolved` → `_resolved/` 이동. **owner 승인 대상은 그대로 남는다**: 도넛 6칸이
`100%` → `100%+` 로 바뀐다(툴팁에 실제값 병기).
