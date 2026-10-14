# changelog_downloader.md 보관 — 미분류(옛 압축 보관 절)

> `docs/changelog_downloader.md` 에서 무수정으로 옮긴 항목(최신이 위). 현행 항목은 원 파일에 있다. 관리: `scripts/doc_rotate.py changelog`.

## Archive (pre-2026-06) — 2026-05-25 → 2026-05-31 (FY2026.1Q 수집 + Reorg)

> 1줄 요약. 전문은 git log/blame. 회사별 URL/XPath 정본은 source-catalog.yaml.

- 2026-05-31 (O~S) -- 데이터 수집 완결: 전수 audit + disclosure 28셀 backfill
- 2026-05-30 (N) -- DART batch script canonical-path refactor
- 2026-05-30 (M) -- File-integrity 검사기 + 현대해상 IR 재다운로드
- 2026-05-30 (L) -- Collection-Status Report step + 양식 추가
- 2026-05-30 (j) -- Reorg #2: DART/KIDI/assoc 마저 정리 (canonical 일관 적용)
- 2026-05-30 (i) -- Downloader workflow 정리 완료 (5 source audit + canonical reorg + master prompt)
- 2026-05-30 (h) -- DART raw 100% audit + gap fill (KPI "전부 다 성실하게" 달성)
- 2026-05-30 (g) -- DART 별첨 fetch 진단 철회 (본문에 다 있음, 회사별 라벨 변형 처리 필요)
- 2026-05-30 (f) -- FY2026.1Q 생보 22사 경영공시 일괄 다운로드 완료 (세션 file ingest A-Z 마무리)
- 2026-05-30 (e) -- FY2026.1Q IR 자료 13 source 다운로드 완료 + 한화손보 IR mis-classified 정리
- 2026-05-30 (d) -- FY2026.1Q 손보 17사 경영공시 PDF 다운로드 완료
- 2026-05-30 (c) -- F2 v3 KIDI ML01/MN07 crawler DONE — NB CSM 분모 6→328 entries, computed multiple 6→27/28
- 2026-05-25 -- IFRS17 historical 13Q ingest + CSM 시계열 panel (push #2)
- 2026-05-25 -- Bond tier `(신종)` fix + FSC bond normalize refresh

---

## Compressed historical archive (pre-2026-05-25)

The compressed one-liner archive in root `docs/claude-changelog.md` ("## Historical archive (compressed)") contains a few downloader-relevant lines, kept inline there for compactness:

- FSC bond ingest client `src/bonds/` + `scripts/ingest_fsc_bonds.py` (MISC-BOND-INGEST)
- FSC schedule API per-insurer full pull: 1720 rows / 19 insurers
- Bond calendar v3: 5y Call rule for ALL bonds, 3-status outstanding/called/matured
- FSC schedule API 15059611 [승인] confirmed

These remain in the root changelog rather than being re-extracted, since they're already condensed.
