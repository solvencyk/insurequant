---
from: downloader
to: parser
created: 20260616T0420Z
status: resolved
route: reparse
company: KR0003,KR0079,KR0068,KR0009,KR0008,KR0011,KR0087,KR1000,KR0002,KR0005
period: 2025.2Q · 2025.3Q · 2023.1Q
rule: NB_CSM_HISTORY_CORRUPT
lane: ifrs17
iter: 1
---

## 미결 (downloader 작성) — NB CSM 시계열 복구용 interim DART raw 재fetch 완료 (raw-ready)

연계: parser/ifrs17 발주 `inbox/downloader/20260616T0400Z`(validation `20260616T0230Z` partial-extract 오염 확정).
git-purge로 부재했던 반기/분기보고서 raw를 DART에서 재취득.

`scripts/ifrs17_batch_historical.py --skip-extract`(fetch-only) →
**10사 × {2025.2Q 반기·2025.3Q 분기·2023.1Q 분기} = 30셀**, canonical
`data/dart/FY{Y}_Q{n}/raw/KR####_<canonical>/document.zip(+meta.json)`. **30/30 fetched, 실패 0.**
raw gitignore(git 무관). 추출 미실행(파서 소관) — `build_csm_waterfall_master.py` 미실행(파괴적, 발주 경고 준수).

### CSM 블록 존재 검증 (zip 내 본문 XML 보험계약마진 count)
| 회사 | 2025.2Q(rcept/보험계약마진) | 2025.3Q | 2023.1Q |
|---|---|---|---|
| 롯데손해 KR0003 | 20250814003966 / 50 | 20251114002985 / 50 | 20230515002687 / **0 🔴** |
| 미래에셋 KR0079 | 20250814003532 / 313 | 20251114002791 / 313 | 20230515002900 / 158 |
| 한화생명 KR0068 | 20250813001075 / 501 | 20251113000814 / 349 | 20230515002940 / 75 |
| 현대해상 KR0009 | 20250814004350 / 232 | 20251114003008 / 236 | 20230515002873 / 136 |
| 삼성화재 KR0008 | 20250814004098 / 148 | 20251114002900 / 154 | 20230515002508 / 127 |
| DB손해 KR0011 | 20250814004289 / 172 | 20251114002521 / 172 | 20230515002856 / 129 |
| 동양생명 KR0087 | 20250814002600 / 511 | 20251114002594 / 154 | 20230515002788 / 59 |
| 코리안리 KR1000 | 20250814004233 / 197 | 20251114002756 / 231 | 20230515002794 / 78 |
| 한화손해 KR0002 | 20250813001295 / 128 | 20251113000523 / 128 | 20230515002513 / 72 |
| 흥국화재 KR0005 | 20250814003425 / 65 | 20251114002501 / 65 | 20230515002741 / 22 |

- **29/30 CSM 블록 존재** → `ifrs17_batch_historical.py`(extract 모드)로 재추출 가능.
- **🔴 honest gap 1건**: 롯데손해 **2023.1Q**(20230515002687) 보험계약마진 0(신계약 8 존재). IFRS17 도입초
  분기보고서 = §14 CSM 변동표 축약/미수록 추정. 다운로드 실패 아님(소스 자체 부재). **우선셀 아님**(차순위
  cross-product 부산물). → census whitelist 처리 권장.
- 우선 7셀(발주 priority) 전부 OK — 특히 롯데 2025.2Q(NB=0.0 최악건) CSM표 확보.

### 요청 (파서 ifrs17 lane)
1. `ifrs17_batch_historical.py`로 30셀(롯데 2023.1Q 제외 29) CSM 재추출 → `extracted_history/` →
   NB CSM YTD 재계산. validation `check_nb_csm_history.py` 재실행해 OVER/UNDER 수렴 확인.
2. §14 변동표가 image/분절/라벨변형인 회사는 적시(다운로더는 본문 XML 텍스트 존재만 확인; 표 구조 파싱은 파서).
3. 마스터 rebuild은 **raw 전체 복원 세션에서**(이번은 interim 29셀만 — 발주 경고대로 부분 rebuild 금지).
4. 추가 분기(2026.1Q·기타 2023 분기) 필요하면 재bounce — downloader가 동일 경로로 fetch.

## 답변 (recipient 작성 — 처리 후)

부분처리 2026-06-20 (parser-ifrs17, open 유지): ifrs17_batch_historical.py extract 30셀 실행 → **8 OK(주로 2023.1Q), 22 no_csm_table_found**(2025.2Q/2025.3Q 반기·분기 §14 변동표 — 텍스트는 존재[다운로더 confirm]하나 표 구조 파싱 실패). = extract_csm_tables semantic-scoring이 interim 변동표 레이아웃 미인식=추출기 보강 필요(0420Z item2 예견 케이스). 마스터 rebuild 미실행(발주 경고 준수). 추출기 보강은 후속 dedicated 세션.

후속 확인 2026-07-30 (parser/ifrs17): root `CSM_waterfall.json`을 직접 대조해보니 이 10사 상당수
(롯데·미래에셋·한화생명·현대해상 등)의 2025.2Q/3Q가 이미 정상값(단조증가 YTD)으로 채워져 있음 —
언제·어떻게 고쳐졌는지 이 inbox 스레드엔 기록 없음(다른 경로로 해소 추정). 단 진단 파일
`data/dart/viz/csm_waterfall_history.json`(이 요청이 원래 만든 산출물)은 재생성 안 돼 옛 상태 그대로
— `check_nb_csm_history.py`가 여전히 27건 OVER/UNDER 보고 중(대부분 false-negative, 상세는 자매
스레드 `20260616T0230Z` 참조). extractor 보강(interim 레이아웃 인식) 자체는 여전히 미완 —
다음 dedicated 세션 대상으로 유지.

후속 확인 2026-08-15 (parser/ifrs17): 생성 스크립트 찾아서(archive로 옮겨져 있었음) 실행함 —
partial 6→3 개선됐지만 OVER/UNDER 27건은 안 줄었음(생성기 소스인 `extracted_history/*_csm.json`
자체가 여전히 옛값이라, root가 어떻게 고쳐졌든 그 경로를 안 거침). 진짜 fix는 raw 재추출 또는
root→진단파일 sync 스크립트, 둘 다 별도 세션 필요 — 전체 분석은 `20260616T0230Z`에 기록, 중복
방지 위해 여기는 링크만.

---

### 종결 (owner 지시 relevance 감사, 2026-08-20)

**무효 — 상위 티켓이 drop됐다.** 이 raw(30셀)는 `20260616T0230Z`(NB CSM 진단파일 오염) 처리용으로 받은 것인데, 그 티켓을 owner가 2026-08-20 drop했다: 대상 `csm_waterfall_history.json`은 `IFRS17.html` L1525 주석대로 **이미 폐기**됐고 `ix.hist`를 읽는 코드가 없다. 라이브가 쓰는 `NB_CSM_multiple.json`은 정상(롯데손해 2025년 1,098.5→2,135.4→3,147.3→4,121.7 단조증가). 재추출 불필요. raw는 디스크에 그대로 두면 된다.
