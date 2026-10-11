---
from: downloader
to: parser
created: 20261011T1215Z
status: open
route: reparse
company: KR0002 · KR0005 · KR0029 · KR0104 · KR0051 (+ 참고 KR0009 · KR0068 · KR0097 · KR0099)
period: 2023.4Q · 2024.4Q · 2025.4Q (+ 참고 칸)
rule: RAW_NEWER_EDITION
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)
사이트 현행본 vs raw 전수 대조(`inbox/downloader/20261011T1100Z…`) 부산물이다. 급한 일은 아니고(FYI) BS·PL 칸을 채울 때 쓸 수 있는 **전문(감사보고서 포함) 판**을 `FY*/attachments/` 에 저장해 두었다는 알림이다. raw/ 가 아니라 attachments/ 인 이유는 본문이 raw 와 같고(= K-ICS 레인에 새 정보 없음), 수백 쪽짜리라 `raw/` glob·변환 대상에 섞이지 않게 하려는 것이다(앞선 별첨 수집과 같은 규칙, 목록은 `data/disclosure/_meta/attachments_manifest.json` 에 sha256·쪽수·표지 확인과 함께 있음).

| 칸 | 새로 저장한 파일 | raw 와의 관계 |
|---|---|---|
| KR0002 한화손보 2025.4Q | `FY2025_Q4/attachments/KR0002_한화손해보험_attachment_full_edition_with_audit_report.pdf` (645쪽) | raw 113쪽 본문이 그대로(쪽 단위 100% 포함) + p114~645 감사보고서(재무제표 별도·연결) 532쪽 |
| KR0005 흥국화재 2024.4Q | `FY2024_Q4/attachments/KR0005_흥국화재_attachment_full_edition_with_audit_report.pdf` (367쪽) | raw 96쪽(폰트 깨짐 본문: 텍스트가 `⸱ ∙` 로 깨짐) 그대로 + 271쪽 추가(텍스트층 있는 감사보고서 등) |
| KR0029 AIG 2023.4Q | `FY2023_Q4/attachments/KR0029_AIG손해보험_attachment_full_edition_with_audit_report.pdf` (86쪽) | raw 75쪽 + p76~86 「지급여력 및 건전성감독기준 재무상태표에 대한 감사보고서」 이미지 11쪽 |
| KR0104 농협생명 2025.4Q | `FY2025_Q4/attachments/KR0104_농협생명보험_attachment_full_edition_with_audit_report.pdf` (404쪽) | raw 128쪽 본문 + p129~404 「재무제표 별첨: 독립된 감사인의 감사보고서」 276쪽 (협회 현행본 = 회사 사이트 파일, 바이트 동일) |
| KR0051 신한이지 2025.4Q | `FY2025_Q4/attachments/KR0051_신한이지손해보험_attachment_alt_edition_site.pdf` (79쪽) | 같은 79쪽이나 쪽 안 배열이 달라지고 p35 에 「투자비용에서 무형자산상각비가 제외된 2025년말 기준 운용자산이익률은 4.28%」 각주가 신설됨. K-ICS 쪽 수치 변경 없음 |

참고(수치가 달라진 새 판, `raw/_v20261011`): KR0009 현대해상 2023.4Q · 2024.4Q · 2025.2Q, KR0068 한화생명 2025.4Q · 2026.1Q(운용자산이익률 p3·p53 / p3·p22), KR0097 하나생명 2024.4Q(p78), KR0099 KB라이프 2026.2Q(p59). BS·PL(8-1·8-2 또는 요약 포괄손익계산서) 칸을 이 분기들에서 읽었다면 바뀐 쪽의 숫자를 새 판과 한 번 대조해 볼 만하다. 칸별 바뀐 쪽 목록은 `data/disclosure/_meta/site_edition_census_parser_kics_20261011.json` 에 있다(kics 티켓 `20261011T1210Z` 와 같은 파일).

## 답변 (recipient 작성 — 처리 후)
