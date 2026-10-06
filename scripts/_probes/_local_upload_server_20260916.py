# -*- coding: utf-8 -*-
"""임시 로컬 업로드 서버 -- 브라우저 페인이 fetch() 로 받은 바이너리를 로컬 디스크로
직접 옮기기 위한 1회용 다리. LLM 컨텍스트로 바이트를 왕복시키지 않는다.
사용 후 이 프로세스는 종료하고 파일도 지운다."""
import http.server
import sys
from pathlib import Path

OUT = Path(sys.argv[1]).resolve()
OUT.parent.mkdir(parents=True, exist_ok=True)


class Handler(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        OUT.write_bytes(body)
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"saved {len(body)} bytes to {OUT}".encode())
        print(f"saved {len(body)} bytes to {OUT}", flush=True)

    def log_message(self, fmt, *args):
        pass


port = int(sys.argv[2]) if len(sys.argv) > 2 else 8917
srv = http.server.HTTPServer(("127.0.0.1", port), Handler)
print(f"listening on 127.0.0.1:{port} -> {OUT}", flush=True)
srv.handle_request()  # 요청 1건만 처리하고 종료
