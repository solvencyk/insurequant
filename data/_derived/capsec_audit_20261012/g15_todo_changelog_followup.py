# -*- coding: utf-8 -*-
"""g15: bookkeeping for the follow-up of the 29th round (publishing 7e6e55d0 + 20a700a9 verified): update the 29th-round Status entry and the '29차 재측정 후속' open item in
TODO_validation.md, and insert a follow-up section above the 29th-round entry of docs/changelog_validation.md.  Newline style preserved; asserts on every anchor."""
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
tp, cp = ROOT + "TODO_validation.md", ROOT + "docs/changelog_validation.md"

# ------------------------------------------------------------------ TODO
raw = open(tp, "rb").read()
nl = b"\r\n" if b"\r\n" in raw[:4000] else b"\n"
lines = raw.decode("utf-8").split(nl.decode())
i = [n for n, l in enumerate(lines) if l.startswith("- **2026-10-13 (29차) 소진율·전망 재측정")]
assert len(i) == 1, i
i = i[0]
assert lines[i + 1].startswith("  불일치 1건:") and lines[i + 2].startswith("  남은 것: publishing 답변 후 재측정")
lines[i] = lines[i].replace("대상 HEAD `6fd00720`,", "대상 HEAD `6fd00720` -> 후속 확인 `20a700a9`,", 1)
lines[i + 1] = ("  불일치 1건(원장 `past_call_outstanding` 플래그가 행 `as_of` 기준이라 콜 경과 3건이 차감에 남음)은 **해소**: publishing `7e6e55d0`·`20a700a9`(첫 콜일 <= 분자 기준일)를 독립 재측정으로 확인 - "
                "47/47 일치, 메리츠 30.8→37.5 · 아이엠라이프 56.9→70.4 · KB라이프 0.0→0.8, 그 밖 변동 0(44사 불변), 기본자본·전망·타임라인·원장·`K-ICS.html` 바이트 동일, 화면 47사 x 1280/375 불일치 0, "
                "티켓 `20261013T0205Z` resolved(`_resolved/`). 재현물 `data/_derived/capsec_audit_20261012/`(`h1h_delta_vs_previous_20a700a9.txt`·`e11_public_sheet_delta_20a700a9.txt`).")
lines[i + 2] = "  남은 것: 공유 감사 티켓 `20261012T2040Z` 종결(오케스트레이터 몫) · owner 결정 잔여 5건(아래 열린 일)."
j = [n for n, l in enumerate(lines) if l.startswith("- [ ] **29차 재측정 후속**")]
assert len(j) == 1, j
j = j[0]
old = lines[j]
assert "publishing `20261013T0205Z`(콜 경과 3건을 분자 기준일로 판정) 답변을 받으면 같은 순서로 재측정:" in old
lines[j] = old.replace("① publishing `20261013T0205Z`(콜 경과 3건을 분자 기준일로 판정) 답변을 받으면 같은 순서로 재측정:",
                       "① 다음 변경 때 같은 순서로 재측정(콜일 규칙 확인 끝남; `h1_tier2_recompute_47.py` 기본 규칙 = 첫 콜일 <= 분자 기준일, 이전 핀은 `H1_PRIMARY=flag`; `h1h`·`e11` 은 이전 핀 대비 변동 목록):", 1)
for n, l in enumerate(lines):
    if l.startswith("> 갱신 2026-10-13 (29차 소진율·전망 재측정 +"):
        lines[n] = l.replace("(29차 소진율·전망 재측정 +", "(29차 소진율·전망 재측정 + 콜일 규칙 정정 확인 +", 1)
        break
else:
    raise SystemExit("header not found")
open(tp, "wb").write(nl.join(l.encode("utf-8") for l in lines))

# ------------------------------------------------------------------ changelog
raw = open(cp, "rb").read()
nl = "\r\n" if b"\r\n" in raw[:4000] else "\n"
t = raw.decode("utf-8")
marker = "## 2026-10-13 (29차) -- 소진율·전망 재측정 (티켓 `20261012T2040Z` 재실행, 읽기 전용)"
assert t.count(marker) == 1
entry = """## 2026-10-13 (29차 후속) -- 콜일 규칙 정정 독립 확인, 티켓 `20261013T0205Z` 종결 (HEAD `20a700a9`)

- **대상**: publishing `7e6e55d0`(데이터·코드: 기발행 차감 제외 = 첫 콜일 <= 분자 기준일, 원장 플래그는 보조) + `20a700a9`(공개본). 직전 판 `6fd00720` 대비 바뀐 감사 대상 파일은 `kics_tier2_utilization.json` 과 공개 시트 `보완자본소진율` 뿐이고, 기본자본 JSON · 전망 JSON · 타임라인 JSON · 원장 · 등재부 · 마스터 · `K-ICS.html` · `theme.js` 는 **바이트 동일**이다(`h1h_delta_vs_previous_20a700a9.txt`).
- **독립 재계산(`h1_tier2_recompute_47.py`, 규칙을 첫 콜일 <= 2026-06-30 으로 바꿔 구현 코드 없이 다시 계산)**: 47/47 일치(0.1%p), 원장 차감액 · 인쇄값 보존 · 적용 전 열 · 한도 47사 일치. 메리츠 **37.5** · 아이엠라이프 **70.4** · KB라이프 **0.8**, 발행 JSON 의 이전 판 대비 변동도 이 3사뿐(44사 불변)이고 내 재계산의 변동과 회사·값이 같다. 콜일이 기준일 당일인 채권을 제외하지 않는 경계 변형은 변동 0(그런 채권 없음), 잔존만기 체감 변형도 변동 0(체감이 움직이던 콜 경과 채권이 빠졌다).
- **기본자본 · 전망 · 타임라인**: 기본자본 47/47(결속 갈래 없는 33사 한도 10%, 하나생명 238.2 · 교보 70.1 · DB손보 151.6), 전망 7사 손계산 35점 차이 0 · 전망 JSON 행 변경 0, 타임라인 JSON 대 원장 126건 차이 0.
- **공개 시트(`e11_public_sheet_delta_20a700a9.txt`, `e7`)**: 기본자본소진율 · 자본비율전망 · 자본성증권발행현황 변경 0. 보완자본소진율은 658행 · 열 · 항목명 구조가 같고, 값 변경 = 3사의 분자(메리츠 9,724.88→11,824.88, 아이엠라이프 2,109.54→2,609.54, KB라이프 0.0→108.51) · 소진율 · 레거시 후순위(5,960→3,860, 500→0, 1,999.51→699.8), 나머지 변경은 47사 3개 행의 비고 문구(「첫 콜일이 분기말 이전인 채권 제외」)뿐이다. 시트 대 JSON 불일치 0, 시트 대 내 재계산 329칸 불일치 0.
- **화면**: 같은 필드를 읽는다. 47사 x 1280/375 DOM · 도넛 · 숫자 줄 · 툴팁 불일치 0(`h5`·`h6`), 툴팁 잘림 0(`h7`). 메리츠 37.5%(「보완자본 한도 적용 전 11,825억원 / 한도 31,554억원 경과조치 기발행 후순위 3,860억원」) · 아이엠라이프 70.4%(「2,610억원 / 3,707억원」, 차감 후순위 0 이라 그 줄 없음) · KB라이프 0.8%(「109억원 / 13,586억원 경과조치 기발행 후순위 700억원」)를 두 폭에서 확인하고 375px 은 캡처로도 읽었다.
- **판정**: 티켓 `20261013T0205Z` resolved(`_resolved/` 로 이동, 종결 노트에 측정값과 재현 명령). 공유 감사 티켓 `20261012T2040Z` 의 지적 전부(원 감사 S-1~S-7, 재측정 1건)가 닫혔고 최종 판정 PASS 다 - 공유 티켓은 오케스트레이터가 종결한다. 하네스: 한 번에 47사 툴팁을 돌리면 45초 제한에 걸려 24사씩 나눴다.
- **모델**: Sonnet 5.5, 이번 구간 토큰 약 0.2M.

"""
t = t.replace(marker, entry.replace("\n", nl) + marker, 1)
t = t.replace("> Last updated: 2026-10-13 (29차 소진율·전망 재측정 +", "> Last updated: 2026-10-13 (29차 소진율·전망 재측정 + 콜일 규칙 정정 확인 +", 1)
open(cp, "wb").write(t.encode("utf-8"))
print("ok")
