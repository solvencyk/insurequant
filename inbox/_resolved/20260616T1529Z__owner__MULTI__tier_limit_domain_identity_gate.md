---
from: owner
to: validation
created: 20260616T1529Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 발주 (owner) — 자본 인정한도 "도메인 항등식" 게이트 룰 추가 (data-contract ②/plausibility)

**배경:** KB손보(KR0010) 보완자본 인정한도 소진율 >100% 적발. 분모/분자 **정의는 소스대로 맞음**(K-ICS 해설서 Ⅲ.2.마 p108·p288, 송미정 [표6] — 보완자본 한도 = **총요구자본(item14)×50%**, 기본자본×100%는 RBC 구제도). 게이트가 못 잡은 이유 = **도메인-항등식 plausibility 룰 부재** + 코드의 `util_over_100`이 flag지 push 막는 RED가 아님.

### 추가할 룰 (신규 "도메인 항등식" class)
- **R-T2-DENOM**: 보완자본 한도(분모) ≈ **item14(SCR) × 0.5** (tol: 해약환급금준비금초과분 제외 조정 ~수%, 또는 PDF "보완자본 한도" 행과 일치). 분모가 **기본자본(item2)** 이나 다른 base로 잡혔으면 **RED** (RBC 룰 오적용 차단).
- **R-T2-UTIL**: 보완자본 인정한도 소진율 ≤ 100%. **>100%면 면제행 추출여부로 분기** — 면제행(기발행 신종자본증권·기발행 후순위채무·해약환급금준비금초과분)이 **추출됐고** 비면제 보완자본>한도면 **legit "100%+"**(over-issuance, 송미정 "2023+ 발행 많은 회사 소진율 높음"); 면제행 **미추출/이미지** 상태의 >100% = **RED(artifact — 분자가 면제분 못 빼서 부풀음)**. 면제행 추출 플래그 없으면 RED.
- **R-T1 동형**: 기본자본 자본증권 인정한도 = SCR×10%(조건부/신종 15%, 해설서 p101). tier1도 동일 패턴 검사. **단 화면 도넛의 발행/한도 >100%는 owner 확정 "100%+" 표기 유지**(display=designer; 게이트는 인정액/한도 축만).

### 정책
- zero-RED 하에서 이 RED도 fix/escalate, self-waive 금지. 회귀 테스트에 "KB류 면제행 미추출 >100% = RED" 추가.
- 주의: python 풀패스. 인라인 멀티라인 `python -c` 금지. UTF-8 no BOM.

## ⚠️ owner 후속 (2026-06-16): 게이트 룰은 owner가 직접 구현함 — 중복 금지
owner가 `scripts/validate_data_contract.py`에 **CHECK 4 (domain identity)** 직접 추가 완료: `check_domain_identity()` = R-T2-DENOM(분모≈item14×0.5) + R-T2-UTIL(소진율>100% & data_source!="table" = RED artifact / table 파싱됨 = YELLOW "100%+"). 라이브 검증: KB손보 218% RED(proxy)·신한이지 분모 스케일버그 적발·한화 정상(미발화)·selftest 7/7. **validation은 이 룰을 재구현하지 말 것** — 리뷰/유지만. (관련 데이터 fix = parser-kics `…kb_tier2_exemption_rows_and_numerator`가 KB 면제표 추출, 그때까지 게이트가 정당하게 push 차단.)

## 답변 (validation 2026-06-20 — CHECK 4 리뷰/유지만, 재구현 0)

owner 지시대로 **재구현 안 함. 리뷰+라이브 검증만.** CHECK 4(`check_domain_identity`)는 설계대로 정확히 작동:

**라이브 게이트 (`prepush_check.py` = data-contract) — RED=4, 전부 CHECK 4:**
| 회사 2026.1Q | util/분모 | rule | 판정 |
|---|---|---|---|
| 동양생명 | 240.23% proxy | T2_UTIL_OVER_100_NO_EXEMPTION | RED (면제표 미파싱 artifact) ✓ |
| KB손해 | 218.42% proxy | T2_UTIL_OVER_100_NO_EXEMPTION | RED (동) ✓ |
| 미래에셋 | 126.45% proxy | T2_UTIL_OVER_100_NO_EXEMPTION | RED (동) ✓ |
| 신한이지 | 분모 2.68억≠268억 | T2_DENOM_NOT_SCR_HALF | RED (1/100 스케일) ✓ |
| 하나손해 | 234.91% table | T2_UTIL_OVER_100_LEGIT | YELLOW (면제표 파싱→designer "100%+") ✓ |
| 악사손해 | 196.78% table | T2_UTIL_OVER_100_LEGIT | YELLOW (동) ✓ |

→ **면제표 파싱사=YELLOW / proxy-gross 미파싱=RED / RBC 분모=RED** 3분기 전부 owner 의도대로 분기. R-T2-DENOM·R-T2-UTIL·R-T1 동형 검사 정상. 회귀 케이스 "KB류 면제행 미추출 >100% = RED"는 CHECK 4가 이미 하드 강제 중 = **요청 충족**.

**RED 4건 처분 = validation 신규발주 0** (전부 owner가 `TODO.md`(2026-06-20) + inbox에 직접 라우팅 완료):
- UTIL×3(동양·KB·미래에셋) = 손fix 불가 documented + downloader OCR(`…20260617T0000Z…tier2_exemption_ocr`).
- DENOM×1(신한이지) = parser ifrs17 `…20260620T0238Z`(후순위채 발행잔액으로 분자 교체) + designer 도넛 잠정숨김.
- **push는 이 4건 해소 후** (owner 명시). 현 push-BLOCKED = 정상.

**부수 확인 (owner 직접수정 무결성, JSON 미변경):**
- 룰7/8 dynamic tolerance(`kics_json_rules.py` line 360-388) 독립검증 = `max(eff_tol, |exp|×0.5/d14 + 50/d14)` dynamic항이 분모 d14에 반비례 → 정상분모 tol=2.0 불변, 카카오 20억만 tol≈124%p. **진짜오류 마스킹 0** (owner 주장 정합). 게이트 실측 K-ICS RED=1(미래에셋 8_life)만 = 타사 미마스킹 확인.
- owner의 PL 121셀+CSM 10셀+MOLE 손정정 → IFRS17 closing **0F**·crosscheck **0F** 유지, **cont 12→6 개선**. 정합성 무손상.

status: resolved (CHECK 4 정상 확인, validation 재구현/신규발주 없음).
