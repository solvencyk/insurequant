---
from: owner
to: parser
created: 20260616T0007Z
status: open
route: backlog
company: 흥국생명, KR0083 푸본현대, 하나생명
period: 2025
lane: ifrs17
iter: 1
---

## 미결 (sender 작성 — owner 라이브 QA 3차) — IFRS17 데이터 3건

**P1. 흥국생명 해지율 shock 방향 — 아직 안 고쳐진 듯.** 25.4Q 기준 해지율 영향이 **CSM과 손익이 같은 방향**이어야 하는데 사이트는 반대방향. 현 사이트 heatmap = **FY2024 stale**(FY2025 phase2 미반영)일 가능성 높음 — FY2024는 해지율↑ csm=−1445/pl=+61로 부호 반대. → **0435Z `…fy2025_reextract` phase2(product-row 일반화)로 흥국 FY2025 반영 시 해소되는지 우선 확인.** 그래도 반대면 sign 버그.

**P2. 푸본현대생명(KR0083) 투자손익 대폭 적자 — 진짜인지 검증.** `PL_breakdown` 추출값이 소스(DART)와 맞는지 대조. 부호/컬럼 오매핑 가능성.

**P3. 하나생명 투자손익 0 — disposition.** 추출 누락/0매핑 vs 실제 0인지 소스 대조.

**주의**: Windows 인라인 멀티라인 `python -c` 금지. python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. raw purge — FY2025 raw는 디스크 복귀돼 있음(extracted 우선).

## 답변 (parser 2026-06-16 — round3 IFRS17 3건 처리)

### P1 흥국생명 해지율 방향 — ✅ FIXED (staleness, sign 버그 아님)
heatmap 흥국이 FY2024 stale(rcept 20250331003642)였음 — FY2024 해지율↑ csm=−1445.2/pl=**+**61.12(부호 반대)
가 owner가 본 "반대방향". FY2025 재추출(rcept 20260331004251) 검증: 해지율↑ csm=−1731.86/pl=**−**32.83 =
**같은 방향(둘 다 −)** ✓, 사망률↑ +27.95/+5.78 = owner 기대(+28/+6) 일치, 6개 시나리오 전부 csm/pl 부호 일치.
조치: 흥국 FY2025 extracted 생성 → build_panel best-status dedup이 **흥국 1社만 FY2025로 교체**, 나머지 27社
byte-identical(FY2024 유지), 가비지사(농협/케이디비) 미혼입, 타 패널 3종 byte-identical, pytest 110. → sign 버그 아님.

### P2 푸본현대(KR0083) 투자손익 대폭 적자 — ✅ REAL (검증완료, 조치 불요)
FY2025 별도 포괄손익계산서(20260331002089.xml) line-by-line + 요약 별도손익계산서 교차검증:
투자손익 −148,769.74백만(−1,487.7억) ✓ — 투자영업수익 +10,910억을 순보험금융비용 −2,941억 + FVPL/파생/FX 손실이
상쇄. 보험금융손익 −294,006.54 ✓(부호 정상), 투자이익 +145,236.80 ✓, 당기순이익 −118,696.60백만(**FY2025 연간
순손실 실재**). 24개 항목 전부 마스터와 백만단위 일치, 부호/컬럼 오매핑 없음. → P2 flag clear.

### P3 하나생명 투자손익 0 — 🟡 PARSE MISS (실제 0 아님), 정확값 확정 + override 적용
하나생명은 투자를 단일 "투자손익" 행이 아니라 **II.투자수익 / III.투자비용 2개 번호행**으로 공시 →
build_pl_breakdown.py L275 단일 `L("투자손익")` 룩업 미스 → item17/18만 None(나머지 정상). 별도 00760 검증(원):
II.투자수익 669,653,289,200 − III.투자비용 351,762,230,334 = **투자이익 317,891.06백만**, item17 = 18+19(−317,069.65)
= **+821.41백만(+8.2억)**. item1(33,699.87)+item17(821.41)=34,521.27 = 영업이익 Ⅴ 정확 일치(gap 0).
- ⚠️ owner flag 예측 +15,037.82/+332,107.48은 **잘못된 폐합식**(영업이익=item1+item17−item16, 기타사업비용 이중차감).
  마스터 gold 컨벤션(KR0095 메트라이프 override: item1=item2−item16 → 기타사업비용 이미 item1에 netted;
  영업이익=item1+item17)으로는 **item17=+821.41**이 정답.
- 조치: `_GOLD_CELL_OVERRIDE[("KR0097","2025.4Q")] = {18:317891.06, 17:821.41}` 추가(메트라이프 audit-only 패턴 동일).
- ⚠️ 단, 라이브 master JSON 반영은 `build_pl_breakdown.py` rebuild 필요 = **이 브랜치에서 파괴적**(raw purge,
  [[project-git-purge]]). override는 들어갔으나 raw-enabled rebuild 전까지 사이트 하나생명 투자손익은 여전히 null
  (NB CSM FY2025와 동일 제약). 즉시 사이트 반영 원하면 master 2종 JSON 수기패치 가능 — owner 판단.

status: P1 fixed+verified / P2 real(no-op) / P3 parse_miss 정확값확정+override적용(라이브반영=rebuild대기).

