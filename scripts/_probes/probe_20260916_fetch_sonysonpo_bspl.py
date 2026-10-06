# -*- coding: utf-8 -*-
"""owner 승인(2026-09-16)으로 ソニー損保 データ編 PDF 를 J-ESR/jesr_http.get 으로 받는다.
J-ESR/raw/ 는 gitignore(126MB급 원본은 커밋 안 함) -- 다음 단계는 jp-collector 가 법정
貸借対照表/損益計算書 추출."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "J-ESR"))
import jesr_http  # noqa: E402

URL = "https://www.sonysonpo.co.jp/company/pdf/ar_data_2026_web.pdf"
OUT = Path(__file__).resolve().parents[2] / "J-ESR" / "raw" / "nonlife_bspl" / "sonysonpo_ar_data_2026.pdf"

resp = jesr_http.get(URL, referer="https://www.sonysonpo.co.jp/company/fr05020.html")
print("status", resp.status_code, "bytes", len(resp.content), "content-type", resp.headers.get("content-type"))
if resp.status_code == 200 and resp.content[:4] == b"%PDF":
    OUT.write_bytes(resp.content)
    print("saved to", OUT)
else:
    print("NOT SAVED -- unexpected response")
    print(resp.text[:500])
