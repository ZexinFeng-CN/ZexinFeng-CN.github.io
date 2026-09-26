#!/usr/bin/env python3
"""Local preview server for this project page.

Fixes the one thing `python3 -m http.server` gets wrong for video: that server
ignores HTTP Range requests, so Chrome sees `video.seekable === [0, 0]` and the
progress bar cannot be clicked or dragged. Real static hosts (GitHub Pages,
Netlify, S3, nginx) all support ranges, so this only affects local preview.

Usage:
    python3 serve.py [port] [root]
"""

import functools
import http.server
import os
import re
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
ROOT = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))


class RangeHandler(http.server.SimpleHTTPRequestHandler):
    _range = None

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")
        if not os.path.isfile(path):
            self.send_error(404, "File not found")
            return None

        size = os.path.getsize(path)
        ctype = self.guess_type(path)
        handle = open(path, "rb")

        match = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if match and (match.group(1) or match.group(2)):
            start = int(match.group(1)) if match.group(1) else 0
            end = int(match.group(2)) if match.group(2) else size - 1
            end = min(end, size - 1)
            if start > end:
                self.send_error(416, "Requested range not satisfiable")
                handle.close()
                return None
            self._range = (start, end)
            self.send_response(206)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(end - start + 1))
        else:
            self._range = None
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(size))
        self.end_headers()
        return handle

    def copyfile(self, source, outputfile):
        if self._range is None:
            return super().copyfile(source, outputfile)
        start, end = self._range
        remaining = end - start + 1
        while remaining > 0:
            chunk = source.read(min(65536, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    handler = functools.partial(RangeHandler, directory=ROOT)
    with Server(("127.0.0.1", PORT), handler) as httpd:
        print(f"Serving {ROOT} at http://localhost:{PORT}  (Range requests enabled)")
        httpd.serve_forever()
