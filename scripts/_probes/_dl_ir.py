# -*- coding: utf-8 -*-
"""Quick IR file downloader with SSL-relaxed context. Usage: python _dl_ir.py <url> <dest>"""
import sys, ssl, urllib.request, os

def download(url, dest):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Referer": "https://www.samsunglife.com/",
        "Accept": "*/*",
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
            data = r.read()
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        head = data[:4]
        kind = "PDF" if head == b"%PDF" else ("ZIP/XLSX" if head[:2] == b"PK" else "OTHER")
        print(f"OK {len(data)} bytes [{kind}] -> {dest}")
        return True
    except Exception as e:
        print(f"FAIL {url} :: {e}")
        return False

if __name__ == "__main__":
    download(sys.argv[1], sys.argv[2])
