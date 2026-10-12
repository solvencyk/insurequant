# -*- coding: utf-8 -*-
from pathlib import Path

def edit(path, pairs):
    p = Path(path)
    t = p.read_bytes().decode("utf-8")
    crlf = "\r\n" in t
    t = t.replace("\r\n", "\n")
    for old, new in pairs:
        assert t.count(old) == 1, (path, t.count(old), old[:70])
        t = t.replace(old, new)
    if crlf:
        t = t.replace("\n", "\r\n")
    p.write_bytes(t.encode("utf-8"))
    print("edited", path, "crlf" if crlf else "lf")

edit("scripts/export_public_sheets.py", [
 ('''# 되돌리기: PRIVATE_SHEETS 에서 시트를 빼고 PRIVATE_PATHS(.sh) 에서 경로를 빼고 download-survey.js 주석을 풀고
# exporter 를 다시 돌린다.
PRIVATE_SHEETS = ("기본자본소진율", "보완자본소진율", "자본비율전망")''',
  '''# 되돌리기: PRIVATE_SHEETS 에서 시트를 빼고 PRIVATE_PATHS(.sh) 에서 경로를 빼고 download-survey.js 주석을 풀고
# exporter 를 다시 돌린다.
# 2026-10-12 재공개 (owner 「분류 근거가 확정돼 소진율 도넛과 Forward Outlook 을 다시 살린다」, 티켓 20261012T2030Z):
# 세 시트와 루트 JSON 3개를 아래 튜플에서 뺐다(= 위 되돌리기 절차를 실행). 비공개 메커니즘(이 튜플들 · 게이트의
# PUBLIC_EXPORT_PRIVATE_SHEET_PRESENT · 배포 스크립트 PRIVATE_PATHS · tests/test_private_deploy.py)은 그대로 둔다 -
# 다시 내리려면 이전 값 `("기본자본소진율", "보완자본소진율", "자본비율전망")` 과
# `("kics_tier1_utilization.json", "kics_tier2_utilization.json", "kics_forward_capital.json")` 을 되살리고
# 배포 스크립트 PRIVATE_PATHS 에 같은 6개 경로를 넣는다. download-survey.js·report-widget.js·K-ICS.html 은 designer 몫.
PRIVATE_SHEETS = ()'''),
 ('''PRIVATE_ROOT_JSONS = ("kics_tier1_utilization.json", "kics_tier2_utilization.json", "kics_forward_capital.json")''',
  '''PRIVATE_ROOT_JSONS = ()'''),
])
edit("scripts/android_push_and_deploy.sh", [
 ('''PRIVATE_PATHS="public_exports/기본자본소진율.json public_exports/보완자본소진율.json public_exports/자본비율전망.json kics_tier1_utilization.json kics_tier2_utilization.json kics_forward_capital.json"''',
  '''# 2026-10-12 재공개(티켓 20261012T2030Z): 아래 6개 경로를 목록에서 뺐다(비공개 메커니즘은 남김). 되돌리려면 6개를 다시 넣는다:
#   public_exports/기본자본소진율.json public_exports/보완자본소진율.json public_exports/자본비율전망.json
#   kics_tier1_utilization.json kics_tier2_utilization.json kics_forward_capital.json
# main 은 비공개 배포로 이 6개를 이미 지웠으므로 NEW_FILES 에 넣어 다시 올린다.
PRIVATE_PATHS=""'''),
 ('''public_exports/보험금예실차비율.json kics_capital_securities_timeline.json"''',
  '''public_exports/보험금예실차비율.json kics_capital_securities_timeline.json kics_tier1_utilization.json kics_tier2_utilization.json kics_forward_capital.json public_exports/기본자본소진율.json public_exports/보완자본소진율.json public_exports/자본비율전망.json"'''),
])
