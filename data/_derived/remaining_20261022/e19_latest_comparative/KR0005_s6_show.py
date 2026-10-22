from KR0005_common import *
import sys
fy = sys.argv[1]
out = io.open(EVD/f"KR0005_s6_show_{fy}.txt","w",encoding="utf-8")
src = io.open(EVD/f"KR0005_s5_stmt_{fy}.txt",encoding="utf-8").read().split("\n")
on = False
for ln in src:
    if "포괄손익계산서 ::" in ln and not on:
        on = True
    if on:
        out.write(ln+"\n")
    if on and ("총포괄" in ln):
        break
out.close()
