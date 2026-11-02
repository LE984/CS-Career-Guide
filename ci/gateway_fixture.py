"""Runner-only HTTP/SSE upstream; never imported by the production application."""

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/ai/llm/chat/'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(b'event: token\ndata: first\n\n')
            self.wfile.flush()
            time.sleep(3)
            self.wfile.write(b'event: done\ndata: last\n\n')
            self.wfile.flush()
            self.close_connection = True
            return
        body = json.dumps({'label': sys.argv[2], 'path': self.path,
                           'authorization': self.headers.get('Authorization'),
                           'cookie': self.headers.get('Cookie'),
                           'host': self.headers.get('Host')}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', int(sys.argv[1])), Handler).serve_forever()
