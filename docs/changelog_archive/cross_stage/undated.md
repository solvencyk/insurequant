# claude-changelog.md 보관 — 미분류(옛 압축 보관 절)

> `docs/claude-changelog.md` 에서 무수정으로 옮긴 항목(최신이 위). 현행 항목은 원 파일에 있다. 관리: `scripts/doc_rotate.py changelog`.

## Historical archive (compressed)

Commit-level detail in git log (first push 2026-05-25).

### 2026-05-25 mid-session (gathering/pushing/cross-stage)
- Forward sim v2: confidence per-row, `capacity_exhausted` cap, auto-sync `window.FORWARD_DATA`
- K-ICS.html Phase 4: 자본성증권 도넛 + Forward Outlook 라인 (dual-axis, 130%/50% 기준선)
- KICS-FORWARD-CAPITAL Phase 3 v1: yearly × 5y, 19사. 롯데 2030 94.67%, 한화 158→134%
- Bond calendar v3: 5y Call rule 전 종목, 3-status. 19.60조 outstanding. FSC API per-insurer 1720 rows / 19사
- Meritz xlsx (K-ICS 240.74%, CSM 112.9조, NB mult 12.61x, Group RoE 25.37%)
- K-ICS gate RED=0 ex OCR (report 20260524T180329Z, 12795 rows, 25 tests)
- User-facing Tier1/Tier2 utilization report 2025.4Q (Korean prose); full RED export 99 cases
- Tier-2 utilization numerator fix (KIRI reconcile): in-range 9→34. FSC bond ingest `src/bonds/`

### 2026-05-24 dashboard + HTML viz
- IFRS17 CSM waterfall panel + 7-panel dashboard · index.html treemap fetch/layout fix · `viz_build_ifrs17_panels.py` rewrite (ASCII source, UTF-8 no BOM) · index C-1/C-2 (no transition toggle) · item28 basic-capital ratio post-transition · K-ICS.html 보조지표(29-35) + 경과조치 토글 · CSM Waterfall HTML proto · NB CSM Ratio HTML proto · IR visual aid 카탈로그 6사

### 2026-05-23 initial setup
- IFRS17 키지표·스크래핑 우선순위 (`docs/claude-agent-ifrs17.md`) · 생명장기손해보험위험액 보조지표 → kics_disclosure.json · IFRS17 도메인 부트스트랩

### 2026-04-25 ~ 04-28 pipeline foundation
- 코드 통폐합 + Docling 파이프라인 · 디렉토리 quarter-first 마이그레이션 · NONLIFE/LIFE 협회 다운로더 · PDF 검증/ACL 모듈 · FY2025_Q4 하네스 일괄 실행
