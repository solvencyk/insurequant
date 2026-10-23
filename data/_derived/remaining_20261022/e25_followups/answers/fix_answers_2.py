# -*- coding: utf-8 -*-
p = "kr0104_nhlife.md"
s = open(p, encoding="utf-8").read()
a = "18 = 17 − 19 가 마스터에 따로 저장돼 있어 17 만 옮기면 `17 = 18 + 19` 가 2.909 어긋난다(허용오차 0.1% × 2,519 = 2.5 보다 크다)."
b = "18 = 17 − 19 가 마스터에 따로 저장돼 있어 17 만 옮기면 `17 = 18 + 19` 가 2.909 백만원 어긋난다(게이트 허용오차 200백만원 안이라 게이트는 못 잡지만 마스터 항등식이 깨진다)."
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
