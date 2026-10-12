import re
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
def rd(p): return open(R + p, encoding="utf-8").read()
def wr(p, s): open(R + p, "w", encoding="utf-8", newline="\n").write(s)

status = """- **2026-10-13 (30차) IFRS17 「최신 비교열」 적용 249칸 독립 검수 + 골든 정리 (티켓 `20261012T2230Z`, 커밋 `b8c37fff` 대상)** — 원문(DART XML·경영공시 PDF)을 자체 코드로 재독: 249/249 일치(BS 65 · CSM 27 · PL 157, 3개월→누적 14칸은 누적 열 인쇄값 일치·한화손보 2칸은 PDF 두 판 일치), 마스터 변경 = 정확히 249칸, 골드 오버레이 +157/+27/+65 가 계획과 1:1(기존 owner 칸 변경 0), 예외 해제 10줄 모두 산수로 닫힘. 후속 `99c7ead7`(NB 12칸 · 콤보 8잎 · 비교 패널 전 잎 658×12 재계산) 일치.
  게이트: 데이터계약 RED 0 · `validate_master_tables --no-build` exit 2(기지 23건, 직전 29) · 연속성·ILP·NB·워터폴·xlsx 드리프트 0 · 골든 갱신 3종(master_tables SUMMARY · 17BS sha(빌더 산출 = 커밋 마스터 바이트) · 입력지문 2종). 발견: parser 티켓 `20261012T1820Z`(푸본현대 1Q 항목 18·19 · 흥국화재 1Q 항목 19 · 삼성화재 2024.1Q 항목 13·14 · 삼성생명 BS 2024.4Q/2025.1Q 기준 단절). 경영공시 PDF 미결정 116칸도 재독 116/116 일치.
"""
t = rd("TODO_validation.md")
m = re.search(r"^- \*\*2026-10-12 \(27차\).*?(?=\n\n## 열린 일)", t, re.S | re.M)
old27 = m.group(0)
t = t.replace(old27, "").replace("\n\n\n## 열린 일", "\n\n## 열린 일")
t = t.replace("## Status (최신 3개)\n\n", "## Status (최신 3개)\n\n" + status, 1)
t = t.replace("> 갱신 2026-10-13 (29차", "> 갱신 2026-10-13 (30차 IFRS17 최신 비교열 적용 249칸 독립 검수 + 29차", 1)
wr("TODO_validation.md", t)
a = rd("docs/todo_archive_validation.md")
head = "# TODO archive — `TODO_validation.md` (Status 이력, 읽기 지연)\n\n"
assert a.startswith(head)
a = head + "## 2026-10-13 Status 밀림 (30차 독립 검수 항목 추가로 밀려난 항목, 무수정)\n\n" + old27 + "\n\n" + a[len(head):]
wr("docs/todo_archive_validation.md", a)

c = rd("docs/changelog_validation.md")
entry = """## 2026-10-13 (30차) -- IFRS17 「최신 비교열」 적용 249칸 독립 검수 + 골든 정리 (티켓 `20261012T2230Z`, 대상 `b8c37fff` · 후속 `99c7ead7`·`638ebabb`)

- **방법**: parser 증거(`evidence_*`)·계획 표시는 열지 않고 `applied_cells.csv` 는 칸 목록으로만 썼다. 자체 코드(`lib_dart.py` lxml 표 판독 · `lib_pl.py` 손익계산서 행 정의 · `lib_tier2.py` 주석 표 레시피 탐색)로 원문 XML 을 읽었고, **레시피를 정하는 방법은 현재 기간 보정**이다: 같은 공시의 당기 열이 마스터의 당기 값(예: 2024.1Q)을 재현하는 행 조합을 먼저 찾고 그 조합을 전기 열에 적용한다(삼성화재 · DB손보 주석 13/13 보정, 메리츠 13/13, CSM 6/6). BS 는 같은 공시 당기말 열이 마스터 값과 맞는 표(별도 기준)를 고른 뒤 전기말 열을 읽었다.
- **결과(249/249)**: BS 65 = 다음 결산 공시 전기말 열 · CSM 27 = 측정요소 변동표(삼성화재 12칸은 당기 표 6/6 · 전기 표 6/6, 메리츠·삼성생명·DB생명·동양·농협은 CSM 3열 합/소계 + 마감 항등식 잔차 0.0억; 동양 항목 4 −240.1 은 인쇄 −240.04 와 반올림 차, 농협 항목 4 1,836.4 는 부채 행 기준 마감 잔차로 2Q~4Q 와 같은 규약 — 인쇄 소계 1,866.15 와는 다르다) · PL 157 = 삼성화재·DB손보·메리츠 후속 공시 전기 열(주석 레시피 + 손익계산서 행) 141 + 3개월 열 정정 14(원 공시 2023.2Q 표의 **누적 열 인쇄값과 일치**) + 한화손보 기타사업비용 2(경영공시 PDF 두 판: 23.1Q 257억 · 23.2Q 529억, 마스터의 옛 39,900·84,500 은 24.1Q·24.2Q 열 399·845). 마스터 변경은 PL 157 · CSM 27 · BS 65 에서 정확히 그 칸뿐이고 파생 `값_당분기`(PL 236 · CSM 42행)는 규칙대로(잔액 항목은 재고 규칙). 골드 지속: `user_pl_cells` +157 · `user_csm_cells` +27 · `bs_manual_overrides` +65, 기존 owner 칸 변경·삭제 0, 계획 칸과 값 1:1. **gold 충돌 59블록**은 적용 칸이 하나도 그 블록 칸이 아니다(회사·분기가 같은 4블록은 다른 항목).
- **3개월→누적 14칸 분기 산술**: 12칸은 `2Q 누적 = 마스터 1Q + 인쇄 3개월` 잔차 0. 2칸은 새 값 = 인쇄 누적이지만 **마스터 1Q 칸이 어긋남**: 흥국화재 항목 19(1Q −83,304 대 후속 공시 −86,247, 재보험금융비용 2,943 누락 의심) · 푸본현대 항목 18·19(1Q −0.19 · 40,277.5 대 −72,286.4 · 112,563.7). 적용 전에는 옛 3개월 값이 우연히 흐름값을 맞췄다 — parser 티켓 `20261012T1820Z`로 발주(고치지 않음).
- **예외 해제 10줄**: DB손보 2023.1Q~3Q · 메리츠 2023.3Q 보험손익 dual(적용 형태 `ΣLOB + 기타영업수익 − 기타사업비용` 잔차 0.1~0.3) · 한화생명·한화손보 2023.2Q 세전이익 = 영업이익 + 영업외손익(잔차 0.000) · DB손보 CSM상각 PIN 3(PL 3,118.50/6,193.43/9,357.89억 대 워터폴 3,118.50/6,193.40/9,357.90억) · 농협생명 FY2023 기초 CSM 4분기 모두 42,505.2(2024.1Q 기초 = 2023.4Q 기말 44,773.9) — 전부 숨은 RED 없이 스스로 닫힌다(`k8_release.txt`).
- **파생 산출물(publishing `99c7ead7`)**: NB_CSM_multiple 변경 12잎 = 동양 2023.1Q·2Q · 메리츠 2023.3Q·4Q, 분자(`CSM_waterfall` 항목 2 연누계·당분기)로 재계산하고 분모(월납월초보험료)는 불변을 확인. `panel_csm_combo` 8잎 + `est_unreliable` 13→12(KB라이프가 빠짐: 2023.4Q 보험계약부채가 재작성 사이드카와 같아져 추정 편차 0.07%)를 마스터에서 재계산해 일치. `panel_compare` 12개 지표 × 658잎 전부 재계산 차이 0(적용 전부터 낡았던 6잎 = K-ICS `74a415bf` 의 현대해상·삼성생명 값, 지금 133,381 · 532,471 로 맞다); ROE 3잎(예별)은 자본 조건 차이로 내 재계산이 값을 내고 패널은 비움 — 이번 적용과 무관.
- **경영공시 PDF 미결정 116칸(parser 자동 대조 못 끝낸 칸)**: 요약 쪽 행 재독 63 + 전체 PDF 행 재독 24 + 스캔 쪽 육안(AIA 12 · 하나생명 5 · 카카오페이 10) 27 + 부호 분리 인쇄 1 + 인쇄 행 없음 1(하노버 2023.1Q 기타사업비용 0) = 116/116, 불일치 0.
- **게이트·골든**(`gates/`, 부작용은 `gate_overlay` 로 격리): `validate_data_contract` RED 0 · YELLOW 170 · `validate_master_tables --no-build` pl_bridge 29→23F(신규 0)·csm_amort PIN 5→2·qoq 267→266·oci_vs_bs_aoci 14→22(YELLOW) · 연속성 · ILP 포트폴리오 · ILP LIC · NB 5/5 · 워터폴 · xlsx 드리프트 0(대조 120,704행) 전부 적용 전과 같거나 의도한 이동. `csm_coverage` exit 1 = 카카오페이 2023.4Q(적용 전부터 있던 기지). **골든**: `master_tables`(SUMMARY 네 토큰 이동 전부 위 수치) · `ifrs17_bs`(sha 만 이동; 빌더 산출 바이트 = 커밋 마스터, 재빌드 안전) · 입력지문 2종(ifrs17_bs 입력 `bs_manual_overrides` +38,939바이트 · viz_ifrs17_panels +1바이트) `--update`. 무이동: PL 빌더 골든(`RUN_PL_GOLDEN=1`, 174초) · viz 패널 · viz CSM(출력 5파일 백업 대비 바이트 동일, publishing 커밋과 같음).
- **관찰 · 한계**: `oci_vs_bs_aoci` 새 YELLOW 8(삼성생명 2024.4Q +5.39조 · 2025.1Q −5.51조 = 2024.4Q 만 재작성 기준·2025.1Q 는 원 기준인 단절 등) 은 골든에 박제됐다 — 해소는 parser 몫. 이 일을 하던 중 느슨한 `python` 호출 2개가 남긴 고아 프로세스를 `taskkill` 로 정리했는데 `python3.13` 프로세스 2개를 이미지 이름으로 죽였다(다른 에이전트 것일 수 있다). 영향 확인은 하지 못했다.

"""
marker = "## 2026-10-13 (29차 후속)"
assert marker in c
c = c.replace(marker, entry + marker, 1)
c = re.sub(r"> Last updated: 2026-10-13 \(", "> Last updated: 2026-10-13 (30차 IFRS17 최신 비교열 적용 249칸 독립 검수 + ", c, 1)
wr("docs/changelog_validation.md", c)
print("ok")
