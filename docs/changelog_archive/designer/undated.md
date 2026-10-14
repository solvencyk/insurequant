# changelog_designer.md 보관 — 미분류(옛 압축 보관 절)

> `docs/changelog_designer.md` 에서 무수정으로 옮긴 항목(최신이 위). 현행 항목은 원 파일에 있다. 관리: `scripts/doc_rotate.py changelog`.

## Archive (pre-2026-06)

- 2026-05-31 — Designer stage created (split from publishing): new prompt `claude-agent-designer.md`; TODO/changelog seeded from root TODO items (MOB-KICS / MOB-IFRS17 / VIS-DONUT / VIS-CHARTLEGEND / M3 / Panel 7 / INDEX-BUBBLE-V2 / F17 Tier2); done archive imported (M1·M2·treemap cleanup·panel pruning·F6·F17 P3·single-source·dead CDN·console·INDEX-C12·KICS-HTML-SUB·F1).
- 2026-05-30 — Panel 3 clean 4-bar swap (data from publishing F17-T1): raw 12-row bar dump → 4-bar 당기순이익 분해 (보험손익·투자손익·영업외 → 당기순이익) + 보종별 caption. Source `net_income_breakdown.json` (Tier1 10/10 손보). 생보 graceful stub, 콘솔 0.
- 2026-05-28 — IFRS17 패널 정리 + F6 yearly amort Panel 2: F6 desktop 10y / mobile 5y (`matchMedia`); coarse → 4-bucket. Panel 5 KPI 카드 + Panel 6 BS 스냅샷 제거(`docs/archived_metrics.md` archive), 패널 1–6 재번호. Generators kept. → follow-up Panel 7.
- 2026-05-28 — index treemap text cleanup + mobile list sort: "기준 XXX" meta line 제거(`.meta` CSS/JS), size-aware labels(name ≥46×60px, ratio ≥26×44px). 모바일 리스트 정렬 ratio desc → 지급여력기준금액 desc (삼성생명 top, 라이나 9th). Preview 검증, 콘솔 0.
- 2026-05-28 — M2 mobile responsive (treemap → vertical list): index.html ≤640px swaps treemap for `#map-list` + `renderList(sector)` mirroring `render()` (same data/color/toggle/click-through). 생명/손해 그룹, ratio desc. Preview 375px 검증, 콘솔 0.
- 2026-05-28 — M1 mobile responsive foundation (4 pages): added `@media (max-width:640px)` to all 4 (zero queries existed before). Header/tabs scroll, panel/chart heights ↓, table overflow-x, map 76vh→58vh. ≤640px scoped → desktop unaffected. Preview 375/1280 검증.
- 2026-05-28 — HTML single-source refactor (P1 + P4): root `K-ICS.html` vs `templates/K-ICS.html` drift(line 171 forward blob) → root sole copy, `git rm templates/{index,K-ICS,IFRS17,공시보고서}.html`. P4: index.html dropped unused `xlsx.full.min.js` CDN (~900KB, 817→816 lines). Preview now `python -m http.server 8000` from root. Deferred: data-JSON dup (P2), shared CSS/nav (P3), K-ICS inline data → external (P5).

Pre-2026-05-28 HTML/viz design entries are in the compressed historical archive of root `docs/claude-changelog.md` ("## Historical archive (compressed)"): IFRS17.html 6-panel dashboard (initial) / K-ICS.html Phase 4 (자본성증권 도넛 + Forward Outlook dual-axis) / index.html treemap (initial Phase 3) / K-ICS sub-items + transition toggle.
