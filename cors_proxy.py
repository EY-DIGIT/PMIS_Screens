"""Local CORS proxy for the PMIS UIDAI screens.

The VM services at http://10.1.131.199/contracts and /projects don't allow
file:// origins (CORS_ORIGINS=http://localhost:3000 only). This proxy runs
on your laptop, forwards requests to the VM, and adds Access-Control-* so
the browser stops complaining.

Run:
    python cors_proxy.py

Then keep the default API base URLs in the screens:
    Contract API     -> http://localhost:9000/contracts
    Project Mgmt API -> http://localhost:9000/projects

No dependencies — pure stdlib.
"""
from __future__ import annotations

import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.error
import urllib.request

UPSTREAM = "http://10.1.131.199"
PORT = 9000
HOP_BY_HOP = {"transfer-encoding", "content-encoding", "connection",
              "keep-alive", "proxy-authenticate", "proxy-authorization",
              "te", "trailers", "upgrade"}


class CorsProxy(BaseHTTPRequestHandler):
    def _forward(self, method: str) -> None:
        url = UPSTREAM + self.path
        body = None
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length:
            body = self.rfile.read(length)

        req = urllib.request.Request(url, data=body, method=method)
        for h, v in self.headers.items():
            if h.lower() in ("host", "origin", "referer", "content-length"):
                continue
            req.add_header(h, v)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                for h, v in resp.headers.items():
                    if h.lower() in HOP_BY_HOP:
                        continue
                    self.send_header(h, v)
                self._cors()
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            payload = e.read()
            self.send_response(e.code)
            ct = e.headers.get("Content-Type", "text/plain")
            self.send_header("Content-Type", ct)
            self._cors()
            self.end_headers()
            self.wfile.write(payload)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self._cors()
            self.end_headers()
            self.wfile.write(f"Proxy error: {e}".encode("utf-8"))

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods",
                         "GET, POST, PATCH, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, Authorization, Accept, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):    self._forward("GET")
    def do_POST(self):   self._forward("POST")
    def do_PATCH(self):  self._forward("PATCH")
    def do_PUT(self):    self._forward("PUT")
    def do_DELETE(self): self._forward("DELETE")

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[cors-proxy] {fmt % args}\n")


def main() -> None:
    print(f"CORS proxy listening on http://localhost:{PORT}")
    print(f"  /contracts/* -> {UPSTREAM}/contracts/*")
    print(f"  /projects/*  -> {UPSTREAM}/projects/*")
    print("Press Ctrl+C to stop.\n")
    try:
        ThreadingHTTPServer(("localhost", PORT), CorsProxy).serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
