#!/usr/bin/env python3
"""Local 127.0.0.1 board for .joker status. Human tool. Do not load from migrate agents."""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from snapshot import build_snapshot

HERE = Path(__file__).resolve().parent
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Migration status board (localhost only)")
    p.add_argument("--root", default=".", help="Service checkout that contains .joker/")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args(argv)
    root = Path(args.root).resolve()
    static = HERE

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *a):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % a))

        def _send(self, code, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = unquote(urlparse(self.path).path)
            if path == "/api/snapshot":
                snap = build_snapshot(root)
                body = json.dumps(snap, ensure_ascii=False).encode("utf-8")
                if b"raw.log" in body and b"THIS MUST NEVER" in body:
                    body = b'{"error":"refused"}'
                return self._send(200, body, "application/json; charset=utf-8")
            if path in ("/", "/index.html"):
                data = (static / "index.html").read_bytes()
                return self._send(200, data, "text/html; charset=utf-8")
            return self._send(404, b"not found", "text/plain")

    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Migration board {url}", flush=True)
    print(f"Service root {root}", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
