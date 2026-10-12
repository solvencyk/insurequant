import re
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
def rd(p): return open(R + p, encoding="utf-8").read()
def wr(p, s): open(R + p, "w", encoding="utf-8", newline="\n").write(s)

status = """- **2026-10-13 (28차) K-ICS 「최신 공시 직전 컬럼」 적용 65칸 독립 검수 + 골든 정리 (티켓 `20261013T0010Z`, 커밋 `74a415bf` 대상)** — 원본 PDF 직접 재판독: primary 33칸 33/33 일치(10쪽은 240dpi 렌더링 육안), 미러 22칸·파생 10칸 재계산 일치, 마스터 diff = 정확히 65칸(레코드 30,011 불변). 보류 10블록 전부 사유 타당.
  게이트: K-ICS exit 0 RED 56→54(풀린 KR0003 2025.1Q·KR0032 2024.3Q 다리 RED 2건, 새 RED 0, 이동 31 finding 전부 적용 16블록 안) · 데이터계약 RED 0 · master_tables `--no-build` 직전 판과 동일 · xlsx 드리프트 0 · 매니페스트 102 통과.
  갱신: `kics_rules_golden`(YELLOW 1,936→1,934 · GREEN 13,705→13,709 · RED 56→54) · 입력지문 4종(+3바이트) · 시험 2파일(등재부 census 10→39, tier2 면제 22→20). 남은 것: PL·17BS 골든 미실행(parser-ifrs17 동시 작업, 빌더가 kics_disclosure 는 이름·티커만 읽음) · 관찰 3건은 changelog 28차.
"""
t = rd("TODO_validation.md")
m = re.search(r"^- \*\*2026-10-12 \(25차\).*?(?=\n\n## 열린 일)", t, re.S | re.M)
old25 = m.group(0)
t = t.replace(old25, "").replace("\n\n\n## 열린 일", "\n\n## 열린 일")
t = t.replace("## Status (최신 3개)\n\n", "## Status (최신 3개)\n\n" + status, 1)
t = re.sub(r"> 갱신 2026-10-12 \(27차 소진율·전망 복원 독립 감사\)", "> 갱신 2026-10-13 (28차 K-ICS 최신 공시 직전 컬럼 적용 독립 검수)", t, 1)
wr("TODO_validation.md", t)
a = rd("docs/todo_archive_validation.md")
head = "# TODO archive — `TODO_validation.md` (Status 이력, 읽기 지연)\n\n"
assert a.startswith(head)
a = head + "## 2026-10-13 Status 밀림 (28차 독립 검수 항목 추가로 밀려난 항목, 무수정)\n\n" + old25 + "\n\n" + a[len(head):]
wr("docs/todo_archive_validation.md", a)

c = rd("docs/changelog_validation.md")
entry = """## 2026-10-13 (28차) -- K-ICS 「최신 공시 직전 컬럼」 적용 65칸 독립 검수 + 골든 정리 (티켓 `20261013T0010Z`)

- **대상·방법**: parser-kics `74a415bf`(owner 2026-10-12 승인) = 16블록 65칸(primary 33 · 적용후 미러 22 · 파생 27·28 10), 보류 10블록. 감사 산출물 `data/_derived/kics_latest_prior_apply_audit_20261013/`(parser 증거 파일은 열지 않고 `applied_blocks.csv` 는 칸 목록으로만 썼다). 원본 PDF 를 자체 판독기(`lib_kics.py`: PyMuPDF word 좌표 -> 행·열 군집, 열 머리 분기 라벨로 컬럼 확정)로 읽었고, 자동 판독이 못 닫은 칸과 스캔 쪽은 행 덤프·240dpi 렌더링 육안으로 읽었다.
- **① primary 33칸**: 새 값 = 최신 공시(F+2, 2026.1Q 둘은 F+1)의 직전/전전 컬럼 인쇄값 **33/33**. F+1·F+2 두 공시가 같은 값이다. 자기 공시 인쇄값 대조: 28칸은 자기 공시 = 옛 마스터(진짜 재작성), **5칸은 마스터 오류**(KR0049 2025.1Q 항목 3 자기 2,331 · KR0049 2026.1Q 항목 4 자기 3,820 · KR0071 2024.4Q 항목 4 자기 33,924 · KR0080 2026.1Q 항목 3 자기 4,280 = 스캔/그림 쪽을 렌더링으로 읽음, KR0003 2023.4Q 항목 4 = 자기 공시 활자 오류 `2,481`, 구성합 24,808, 후속 둘 24,807). KR0072 2025.2Q 항목 12 는 자기 `-`(0) 이고 후속 둘이 328. 육안 렌더링 10쪽 = 위 스캔 4 + KR0003 p41 + KR0009·KR0004·KR0032·KR0072·KR0003 의 F+2. 원장 신규 29칸(`h1_ledger_check.txt`) = primary 33 중 자기 공시값이 새 값과 다른 29칸과 1:1(as_filed · restated · 마스터 현재값 일치). 표 `e1_final_table.csv`(65행, 쪽 번호·인쇄값).
- **② 미러 22칸 · 파생 10칸**: 미러는 새 primary 값의 복사이며 전제(그 줄은 경과조치가 안 바꾼다)를 후속 공시 본문에서 읽었다(KR0009 비적용 · KR0049 TIR 만 적용 -> 보완자본 불변 · KR0050 · KR0069 · KR0080 · KR0095 비적용 · KR0099 TFI 만 적용 -> 구성항목 불변). 파생 10칸은 항목 1·2·14 에서 재계산해 |차| ≤ 1e-5(적용전·적용후), 16블록 전 칸 27·28 재검산 불일치 0. **마스터 diff = 정확히 65칸**(레코드 30,011 · 추가/삭제 0 · 필드 `값`·`값_적용후` 만).
- **③ 보류 10블록 전부**: KR0070 2024.3Q 항목 22 = 자기·F+1·F+2 모두 1, 마스터 0, `recalc_kics_derived.py`(항목14=항목15 · 항목23=0 이면 항목 22 를 0 으로) 가 1 을 다시 0 으로 되돌림을 메모리에서 재현(f2_kr0070). 나머지 9블록은 F+1 과 F+2 가 서로 다르다(8블록: 자기=F+1=마스터, F+2 만 ±1 · KR0051 2023.3Q: 자기 -321 · F+1 -332 · F+2 -333 · KR0100 2025.2Q: F+2 만 항목 5 4,941 · 항목 11 275, 둘이 서로 상쇄해 산수로 판별 불가). 보류 타당, 10블록 마스터 불변.
- **④ 게이트**(한 번에 하나, `gates/`): `validate_kics_disclosure` exit 0 · RED 56->54(풀린 KR0003 2025.1Q·KR0032 2024.3Q 의 `2_tier1_bridge` 2건, **새 RED 0**) · 이동한 (회사,분기,룰,상태) 31건은 전부 적용 16블록 안(블록 밖 0) · 반올림 GREEN->YELLOW(잔차 ±1~2, tol 2) 포함. `validate_data_contract` exit 0 RED 0 YELLOW 165(재작성 박제 14버킷 재검산 통과) · `validate_master_tables --no-build` SUMMARY 가 parser 최종 판과 한 줄도 다르지 않다(exit 2 는 기지 29건 pl_bridge 때문, 골든이 고정) · `check_master_xlsx_drift` 드리프트 0 · `test_rule_coverage_manifest` 102 통과 · identity 계열 통과.
- **⑤ 골든·시험 정리**: `kics_rules_golden` — 기준선(`74a415bf^` 마스터)을 같은 엔진으로 돌리면 골든 sha 와 일치(골든 = 적용 직전 상태)하고 현재와의 차이는 위 31건뿐이라 의도된 변화로 판정해 `--update`(YELLOW 1,936->1,934 · GREEN 13,705->13,709 · RED 56->54). `builder_input_fingerprints` 4종(ifrs17_bs·pl_breakdown·dividend·post_transition)은 입력 `kics_disclosure.json` +3바이트뿐 — 앞 셋은 이 파일에서 회사명·티커·생손보만 읽으므로(코드 확인) 산출 불변, post_transition·dividend 골든은 실행해 통과. 시험 고침: `test_rule_coverage_manifest.KICS_RESTATEMENT_CENSUS` 10->39(원장 +29, 검사는 느슨하게 하지 않고 숫자만) · `test_tier2_issuer_inconsistent_exemption` 3건 = 등재 22->20, 결측 시험 대상 KR0003 2025.1Q -> KR0004 2025.1Q, 갈래 박제 시험은 `branch=` 박제 버킷이 0 이 돼 KR0029 2025.3Q 의 flag 를 시험 안에서만 `branch=CAPPED` 로 monkeypatch(대조군 추가, 지우지 않음).
- **⑥ 하지 않은 것 · 관찰**: ① PL·17BS 골든 미실행(빌더가 마스터를 인플레이스로 덮고 parser-ifrs17 이 같은 시간에 작업 중 — 동시 쓰기 위험; 입력지문 갱신 근거는 위 코드 확인) ② `tests/test_data_contract_selftest.py` 는 단독 실행 시 실패한다(`validate_master_tables.py:31` 의 무가드 `sys.stdout.reconfigure` 가 StringIO 리다이렉트 중 import 에 걸림). 훅의 묶음 실행에서는 앞선 시험이 먼저 import 해 통과하며(42 통과로 확인), 직접 `--selftest` 는 102/102 — 적용과 무관한 순서 의존 결함, 미수정. ③ KR0009 2023.1Q 의 적용후 항목 2·3·28(미러)은 자기 공시 `해당사항 없음`·후속 공시는 적용후 지급여력금액 합계만 인쇄해 독립 확증이 없다(같은 회사 2023.2Q 는 TFI 로 적용후 기본자본이 +5,000 이동) — 적용 전에도 전=후였던 기존 가정이고 이번 적용이 만든 문제는 아니다. ④ `scripts/validate_kics_disclosure.py`·마스터·원장은 손대지 않았다.
- **커밋 범위**: 시험 2 · 골든 fixture 2 · 감사 폴더 · TODO/changelog/archive. 티켓 파일은 고치지 않았다(오케스트레이터가 종결).

"""
marker = "## 2026-10-12 (27차)"
assert marker in c
c = c.replace(marker, entry + marker, 1)
c = c.replace("> Last updated: 2026-10-12 (27차 소진율·전망 복원 독립 감사)", "> Last updated: 2026-10-13 (28차 K-ICS 최신 공시 직전 컬럼 적용 독립 검수)", 1)
wr("docs/changelog_validation.md", c)
print("ok")
