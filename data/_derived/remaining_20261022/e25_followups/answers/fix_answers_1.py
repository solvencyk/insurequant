# -*- coding: utf-8 -*-
import io
p = "kr0070_abl.md"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
rep("티켓·앞 답변이 말한 3,323(원 공시 발행 표)·3,524 는 다른 판/다른 행이라 쓰지 않았다.", "티켓이 말한 3,323 은 원 공시 판의 원수 값(옛 판)이다. 앞 적재 답변의 「최신 3,524」는 이 표의 위험조정변동(3,593)이 아니라 같은 표 기타사업비용 전분기 열(L41734 3,524)과 같은 숫자라 맞지 않는다.")
rep("**방식·수치**: gold set 신규 17 + 제자리 교체 1(2023.1Q 항목 7), 박제·핀·잔차 끼움·게이트 예외 0. 전부 빌더 소스 값과 달라 마스크 칸 아님(PL 마스크 22 불변). 마스터 값 변경 20칸 + 파생 단일분기 변경 포함 20칸(`x02_diff_applied.txt`). 제거한 박제 없음.",
    "**방식·수치**: gold set 신규 18 + 제자리 교체 1(2023.1Q 항목 7), 박제·핀·잔차 끼움·게이트 예외 0. 전부 빌더 소스 값과 달라 마스크 칸 아님(PL 마스크 22 불변). 마스터 값 변경 19칸, 단일분기 변경 20칸(값 변경 19 + 2023.4Q 항목 9 단일분기 -3 → -2,434; `x02_diff_applied.txt`). 제거한 박제 없음.")
rep("publishing = xlsx `손익분해PL` 동기화(ABL 몫: 값 20 + 단일분기 파생 변경 20 중 겹침 제외), panel/public_exports.", "publishing = xlsx `손익분해PL` 동기화(ABL 몫 39칸 = 값 19 + 단일분기 20), panel/public_exports.")
open(p, "w", encoding="utf-8", newline="\n").write(s)
p = "kr0099_kblife.md"
s = open(p, encoding="utf-8").read()
rep("publishing = xlsx `손익분해PL` 동기화(이 티켓분 6칸: 값 3 + 단일분기 2023.2Q 3), panel/public_exports.", "publishing = xlsx `손익분해PL` 동기화(KB라이프 몫 9칸 = 값 3 + 단일분기 6: 2023.1Q 3 + 2023.2Q 3), panel/public_exports.")
rep("이 티켓분 파일 변경은 아래 공통 절의 파일 목록에 있다.", "이 티켓분 파일 변경은 4건 공통 1회 적재의 파일 목록(INDEX.txt 1절)에 있다.")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
