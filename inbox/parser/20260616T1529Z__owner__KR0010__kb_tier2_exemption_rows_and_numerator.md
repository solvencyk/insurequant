---
from: owner
to: parser
created: 20260616T1529Z
status: answered
route: backlog
company: KR0010 KB손해보험 (+ 전사 >100% triage)
period: 2026.1Q
lane: kics
iter: 1
---

## 미결 (owner) — KB 보완자본 인정한도 소진율 >100% 진단 + 분자 PDF-printed 우선

**정의 확정(소스 인용, owner 검증완료):** 분모 = 총요구자본(item14)×50% (해설서 Ⅲ.2.마 p108·p288, 송미정 [표6]). 분자 = 경과조치 후 보완자본 − 해약환급금준비금초과분 − 2022년까지 발행 자본성증권(기발행 신종자본증권+기발행 후순위채무). **정의는 맞다 — 문제는 분자 면제행 파싱 갭 의심.**

### 작업
1. **KB(KR0010) 26.1Q 면제행 추출 확인.** `md_inbox/FY2026_Q1/KR0010_*.md`의 경과조치 5-2-2 표(`보완자본 한도 적용 전`·`보완자본 한도`·`해약환급금부족분…`·`기발행 신종자본증권`·`기발행 후순위채무`)가 `compute_tier2_utilization.py`의 `_extract_common_table`에서 잡히는지. KB 보완자본 72,777억 vs 한도 33,319억(=SCR 66,638×0.5) → 초과분이 경과조치 면제로 안 빠지면 >100% artifact.
2. **이미지/표 부재면** → downloader에 텍스트본/OCR `route: refetch` 바운스 (KB는 이미지 PDF 상습 — 메모리 `reference_kics_company_quirks`).
3. **분자 = PDF에 인정액/면제분이 printed면 `_compute_numerator`의 다분기 휴리스틱(gross vs net 추정) 대신 PDF 값 직접 사용** (fragile 재계산이 오버슈팅 주범). owner: "원래 PDF에 적힌 분자·분모 쓰던 거"로.
4. **전사 26.1Q 소진율 >100% 회사 전수**를 뽑아 **legit over-issuance(면제 빼도 초과) vs artifact(면제행 미추출)**로 분류 보고. legit → designer "100%+" 표기 바운스; artifact → fix.

### 주의
- python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. 인라인 멀티라인 `python -c` 금지. UTF-8 no BOM. `build_csm_waterfall_master.py` 금지.

## 답변 (parser-kics 2026-06-17 — 전사 >100% triage: 5사 전부 artifact, legit 0)

**owner #4 전수 분류 (2026.1Q tier2 >100% = 5사, 전부 면제행 미차감 artifact):**
| 회사 | util | src | 원인 | 라우팅 |
|---|---|---|---|---|
| KR0087 동양생명 | 240% | proxy | **이미지 PDF** → 면제행 추출불가, gross item3 사용 | downloader OCR |
| KR0050 하나손해 | 235% | table | 면제행 off-page/heuristic 미차감 | parser off-page 추출 |
| KR0010 KB손해 | 218% | proxy | **이미지 PDF**(상습) → 면제행 부재, gross | downloader OCR |
| KR0049 악사손해 | 197% | table | 면제행 off-page/heuristic 미차감 | parser off-page 추출 |
| KR0079 미래에셋 | 126% | proxy | **이미지 PDF** → gross | downloader OCR |

**legit over-issuance(면제 빼도 초과) = 0건.** 5사 전부 분자에서 **기발행 자본성증권(면제행)이 안 빠진 artifact**.
→ designer "100%+" 표기 바운스 대상 없음. 전부 fixable.

**owner #1 KB 면제행 확인**: `md_inbox/FY2026_Q1/KR0010_*.md`에 5-2-2 면제행(보완자본 한도/기발행 신종·후순위/
해약환급금초과분) **전부 부재** = KB는 **이미지 PDF**(`reference_kics_company_quirks` 상습). `_extract_common_table`이
잡을 텍스트가 없음 → **owner #2대로 downloader OCR 바운스**(아래 발송). KB 보완자본 72,777 vs 한도 33,319은
면제행(해약환급금초과분+기발행 자본성증권)을 빼면 한도 내일 것 — gross라 218% artifact.

**owner #3 (PDF-printed 분자 직접 사용) 동의 — 근본 처방**: 현 `_compute_numerator`의 다분기 gross-vs-net
휴리스틱이 오버슈팅 주범. PDF에 인정 보완자본/면제분이 printed면 그걸 직접 써야 함. 단 그 값이 (a) 이미지사는
OCR 필요(KB·동양·미래), (b) 텍스트사(농협·하나·악사)는 **경과조치 면제행이 off-page라 localize 누락**(농협 p19 확인,
1530Z 연계) → **full-PDF 면제행 추출기**가 필요. = 1530Z 농협 신종 갭과 동일 뿌리.

**라우팅:**
- → **downloader**: KB·동양·미래에셋 26.1Q 면제행(보완자본 한도/기발행 자본성증권/해약환급금초과분) OCR
  (`inbox/downloader/20260617T…tier2_exemption_ocr`, route: refetch). 발송함.
- → **parser(나) 후속**: 하나손·악사 등 텍스트사의 off-page 면제행 full-PDF 추출 + `_compute_numerator`가
  PDF-printed 인정액 직접 사용하도록 보강 = 별 작업(substantial, 다음 슬라이스).

status: triage 완료(5사 전부 artifact·legit 0)·KB 이미지 확정·OCR 바운스. off-page 면제행 추출기는 후속.
