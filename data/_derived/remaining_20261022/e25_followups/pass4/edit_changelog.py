# -*- coding: utf-8 -*-
"""docs/changelog_parser_ifrs17.md: insert the 25차 entry above the 24차 entry (byte-preserving for everything else; one blank line separator)."""
from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/docs/changelog_parser_ifrs17.md")
raw = p.read_bytes()
crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")
anchor = "## 2026-10-24 (24차: 이웃 옛 판 칸 점검 3차, 마지막 묶음"
assert s.count(anchor) == 1
entry = """## 2026-10-24 (25차: 동양 재보험 블록 9·10(+11 빈칸) · NH농협손보 2023 손익계산서 블록 마무리 — PL 값 15칸 · 단일분기 25칸, 박제·핀·잔차·예외 0 — 티켓 20261024T1000Z)

커밋 안 함, push 안 함. 서브에이전트·docling 안 씀. `build_root_masters.main()`·`build_ifrs17_bs`·xlsx 동기화·panel·public_exports·NB·원장(박제)·핸들러·CSM 파일 미접촉. 증거 `data/_derived/remaining_20261022/e25_followups/pass4/`(`INDEX.txt` · 답변 원문 `answer_ticket.md` · 게이트/테스트 `gates/`).

- **범위(24차 독립 재독이 같은 필링에서 읽히는데 비어 있다고 남긴 칸)**: ① NH농협손보 KR0032 2023.2Q 항목 1·16·17·18·19·20·21 + 2023.1Q 항목 19 ② 동양 KR0087 2024.1Q·3Q 재보험 항목 9·10·11·12 ③ 동양 2024.2Q 항목 9·12 부호 확인(값 불변).
- **방법**: 24차와 같은 흐름(읽기 스크립트 → `p01_build_plan.py` → `p4_apply.py` 가 실제 `build_pl()` 을 임시 사본에 돌려 달라지는 칸만 셀 단위로 씀). 적용기는 `p3_apply.py` 에서 파생해 gold 값 null(빈칸)을 허용하고 기존 gold 의 note 만 덧붙이는 `gold_note_append` 를 더했다. 독립 재독은 정규식 표 파서(`vlib.py`)로 78/78 일치, 변이 시험(5칸 주입 → BAD 9줄). 적재 전 `b01_backup_preload.py` 로 29개 파일 백업(sha256 사본 == 원본), 적재 뒤 `x02_diff_files_p4.py` ALL PASS.
- **결과**: gold set 1523 → 1538(신규 15: NH 9 · 동양 6[빈칸 2]), null_dangi 124 → 125(+동양 2024.4Q 항목 9·10 −NH 2023.2Q 항목 16), 값 15칸 · 단일분기 25칸(NH 17 · 동양 8), 출처표 4블록 교체(방출기 재현 56/56). 모두 빌더 소스와 달라 마스크 칸이 아니다(센서스 (1523, 22) → (1538, 22), 박제 0, 원장 바이트 동일).
- **판정 메모**: NH 는 FY2024 1분기·반기·3분기 별도 손익계산서 전기 누적 열(FS-API `frmtrm_add` 로 독립 확인)로 원 단위 연쇄 1+17−20 · 20+21−22 · 22−23−24 · 투자영업수익−투자영업비용−17 이 모두 0 이고, 2Q·3Q 단일분기가 인쇄 3개월과 소수 6자리 일치한다. 19 = (보험·재보험 금융수익) − (금융비용), 18 = 17 − 19 정의는 마스터 2023.3Q 와 e20 gold 를 원 단위로 재현한다. 2023.1Q 는 항목 19 만 다르고(−56,596 → −56,595.452489) 나머지는 이미 최신이었다. 2Q 항목 16 은 41,900(경영공시 0.01억 반올림) → 40,748.545805 로 바꿔 e20 (c) 단일분기 빈칸을 풀었다. **첫 적용에서 새 FAIL 1건**: 항목 1 이 생기자 PL_BRIDGE `보험손익(leg-coverage)` 가 2023.2Q 를 처음 검산하는데 adj 후보(2 + 15 − 16)는 15·16 이 둘 다 있을 때만 만들어져 15 공란이면 기타사업비용만큼(40,747) 어긋나 보인다(삼성화재 2023.1Q 에서 이미 겪은 함정, `build_pl_breakdown.py` L719-724). NH 손익계산서에 기타영업수익 행이 없고 저장소 관례가 0.0 이라 2023.2Q 항목 15 = 0.0 을 티켓 밖 한 칸으로 더했다(잔차 −1.268 로 닫힘, 15 가 ±1.3 밖이면 깨지므로 끼움이 아니다). 동양 티켓의 L22097·L22108 은 연결 쪽 표라 별도 표(FY2025_Q1 L36357-36718 · FY2025_Q3 L55014-55411)를 다시 읽었고 합계 열은 같은 값이다. 부호는 생산 정의 −|값|이며 마스터 2025.3Q −1,401/−841 을 같은 서식의 당분기 표로 재현한다; 반기보고서 전반기 별도 롤포워드(CSM (70)+2,599 = 2,529 · RA (33)+(791) = (824))가 2024.2Q 마스터 −2,528/−824 와 일치하고, 1분기·3분기 전분기 표의 기초 잔액이 같아 3분기 전분기 표는 9개월 누계다. 예상/실제 재보험금 구성 행은 반기보고서만 인쇄해 1분기·3분기의 항목 11 은 확정할 수 없고, 옛 값 3,805 · −479 는 재보험계약 서비스결과 합계(= 항목 8, 3개월 열)라 gold null 로 비웠다(2025.3Q 항목 11 과 같은 방식); 12 는 공란 유지. 4Q 항목 11 의 단일분기 6,237 은 3Q 누계가 비면서 공란이 됐다.
- **새로 확인한 것(부호)**: owner 손입력 gold 는 순자산(부채) 관점 인쇄 부호를 뒤집은 값이다(2024.4Q 인쇄 +1,711 · (1,559) → −1,711 / +1,559, FY2024 사업보고서 별도 L54016·L54027; 2025.1Q 인쇄 (461) · (295) → +461 / +295). 인쇄 부호는 RA 가 전 분기 음수, CSM 이 2024 에 +, 2025 에 − 라 −|값| 은 RA 전부와 2025 CSM 에서 인쇄와 같고 2024 CSM 만 반대이다; owner 규약(−인쇄)과는 RA 전부와 2025 CSM 에서 반대이다 → owner 결정. 4Q 항목 9·10 은 연간 원본(1,711 / 1,559)이 FY2025 분기 전기 열 3Q 누계(3,079 / 1,180)와 공시 판·부호가 달라 단일분기만 null_dangi.
- **싣지 않은 것**: 동양 2024.1Q·3Q 항목 12 와 11 의 새 값(구성 행 미인쇄) · 동양 2024.4Q 9·10·12 · 2025.1Q 9~12(owner gold) · 동양 2024.4Q 항목 11(owner gold 12 가 5,758 을 끼고 닫힘) · NH 2023.2Q LOB 노트 항목 6·7·11·12.
- **게이트·테스트(적재 전 → 후)**: master_tables pl_bridge 3803P → 3807P/18F/0NEW 한 필드뿐, 18 FAIL 목록과 나머지 SUMMARY 필드 동일(NH 2023.2Q `NOLHS` → `LEGOK diff=-1.3`) · data_contract RED 2 → 2(MASTER_XLSX_DRIFT `손익분해PL` 349 → 389 = 바뀐 40필드와 정확히 일치 + `CSM워터폴` 3), YELLOW 168 동일 · 연속성 flagged 1/RED 0 · 워터폴 41 pass · nb_csm 5/5 · live_artifacts RED 2/YELLOW 25 불변 · 골든 `--update` 1줄(master_tables SUMMARY) · rule_coverage 104 passed + 2 failed(허용된 xlsx 드리프트 · public_exports 드리프트[적재 전에도 실패]) · PL 골든(172초) · viz 골든 2종 · gold_overlay 10 · identity 24 · deploy_assets 12 · push_gate_wiring 66 · 지문 23 통과. `p4_apply.py --verify` 새 드리프트 0.
- **프로세스 기록**: 수정 라운드 1회 — 첫 적용(항목 15 없이 14칸)이 새 FAIL 1건을 내서 감사된 되돌림 경로 `--revert --apply` 로 HEAD 와 바이트 동일하게 되돌리고(`sha256_head_state.txt` 대조) 항목 15 를 넣어 다시 적용했다. 둘째 적용 전에 `--out-dir` 시뮬레이션 + `gate_overlay.py` 로 master_tables 새 FAIL 0 을 먼저 확인했다. `git push`/`git add -A` 없음.
- **남은 것**: 결정 = 동양 부호 규약 · 동양 4Q owner gold 9·10·11·12 · 흥국화재 항목 16 박제 2건 · KB라이프 연쇄 면제 / publishing = xlsx `손익분해PL` 389 · `CSM워터폴` 3 동기화, panel/public_exports.

"""
s = s.replace(anchor, entry + anchor)
p.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
print("changelog entry inserted; crlf =", crlf)
