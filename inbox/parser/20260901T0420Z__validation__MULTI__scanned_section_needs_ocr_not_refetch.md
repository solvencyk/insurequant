---
from: validation
to: parser
created: 20260901T0420Z
status: open
route: reparse
company: KR0071,KR0079,KR0010,KR0080
period: 2023.4Q,2024.4Q,2025.2Q,2025.4Q
rule: (사이드카) kics_source_textlayer / SCANNED_SECTION
lane: kics
iter: 1
---

## 미결 (sender 작성)

**처방이 재수집이 아니라 OCR 인 파일 6칸을 새로 식별했다.** 종전 사이드카는 이들을
`READABLE`/`BORDERLINE` 으로 찍고 있었다.

### 무엇이 틀렸었나

`data/_derived/kics_source_textlayer.json` 이 판독성을 **문서 전체 평균 chars/page** 로 쟀다.
그 지표는 **"앞은 스캔, 뒤는 감사보고서 텍스트"** 문서를 영원히 READABLE 로 부른다.

실측 — `data/disclosure/FY2024_Q4/raw/KR0071_흥국생명보험.pdf` (538p):
p1-112 이 통째로 이미지(정기경영공시 본문), p113-450 이 텍스트(감사보고서·주석).
전체 평균 532.8자/p → READABLE 로 찍혔지만 **정작 K-ICS 절은 한 글자도 텍스트가 아니다.**

이 오판이 두 번 사람을 속였다. `data/_gold/kics_exemption_provenance.json` `entries[6]` 은
owner 가 2026-07-16 에 `image-only PDF` 로 등재한 것을 validation 이 2026-08-21 에
"538p/286,634자 = 533자/p 이므로 거짓" 이라며 뒤집었는데, 그 반증이 틀렸다(근거로 든 인접 페이지가
전부 텍스트 구간, 즉 감사보고서 주석이었다). 그 결과 처방이 **downloader 재수집**으로 오라우팅됐고
— 재수집해도 같은 스캔본이 온다 — **OCR 이 한 번도 발주되지 않았다.**
(등재부 `entries[6]` 정정은 orchestrator 가 직접 한다. 이 티켓은 정정 대상이 아니다.)

### 고친 것

`scripts/build_kics_source_textlayer.py` 가 이제 페이지별 분포와 K-ICS 절 위치를 같이 잰다.
신규 상태값 **`SCANNED_SECTION`** = 문서는 맞는데 해당 절만 이미지 → **처방은 OCR**.
(판정은 전체평균 판정보다 **느슨해지지 않게** 두 판정 중 엄한 쪽을 쓴다.)

### OCR 이 필요한 칸 (재생성 후 SCANNED_SECTION 6칸)

| 셀 | 파일 | 페이지 | 전체평균 | 앞 연속 스캔 | 종전 판정 |
|---|---|---|---|---|---|
| KR0071 2024.4Q | KR0071_흥국생명보험.pdf | 538p | 532.8 | 112p | READABLE |
| KR0079 2023.4Q | KR0079_미래에셋생명_amended.pdf | 510p | 692.8 | 52p | READABLE |
| KR0079 2024.4Q | KR0079_미래에셋생명.pdf | 559p | 611.3 | 98p | READABLE |
| KR0079 2025.4Q | KR0079_미래에셋생명.pdf | 564p | 626.8 | 56p | READABLE |
| KR0010 2025.4Q | KR0010_KB손해보험.pdf | 136p | 228.6 | 14p | BORDERLINE |
| KR0080 2025.2Q | KR0080_에이아이에이생명보험.pdf | 52p | 100.3 | 47p | BORDERLINE |

**미래에셋생명 연간 필링 3개는 아직 아무도 안 본 상태다.**

재현:
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_kics_source_textlayer.py
```
그 뒤 `data/_derived/kics_source_textlayer.json` 에서 `status == "SCANNED_SECTION"` 인 셀.
각 셀에 `front_scan_run` · `scan_pages` · `anchor_pages` · `section_chars_per_page` 근거가 같이 있다.

### 부탁

위 6칸은 **재수집 대상이 아니다**(다시 받아도 같은 스캔본). 앞부분 스캔 구간을 OCR 해서
K-ICS 절을 텍스트로 만든 뒤 재파싱해 주기 바란다. `front_scan_run` 이 OCR 해야 할 페이지 수다.

## 답변 (recipient 작성 — 처리 후)
