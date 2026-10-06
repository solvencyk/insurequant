# -*- coding: utf-8 -*-
"""브라우저 javascript_tool 결과가 너무 커서 자동 저장된 JSON([{type,text}]) 에서
base64 텍스트를 꺼내 PDF 로 디코드. 이 스크립트는 큰 문자열을 LLM 컨텍스트에
올리지 않고 디스크에서 디스크로 바로 처리한다."""
import base64
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])

blob = SRC.read_text(encoding="utf-8")
# 저장 포맷의 JSON 중첩/이스케이프가 신뢰할 수 없어 정규식으로 최장 base64 alphabet
# 런을 뽑는다 -- 페이로드가 118만자라 주변 JSON/트레일러 텍스트보다 압도적으로 길다.
candidates = re.findall(r"[A-Za-z0-9+/]{1000,}={0,2}", blob)
text = max(candidates, key=len)
print("candidates found:", len(candidates), "chosen len:", len(text))
pad = (-len(text)) % 4
text += "=" * pad
raw = base64.b64decode(text)
DST.parent.mkdir(parents=True, exist_ok=True)
DST.write_bytes(raw)
print("magic:", raw[:8])
print("bytes:", len(raw))
print("saved:", DST)
