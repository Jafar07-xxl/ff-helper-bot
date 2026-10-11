"""Mini web server so Render Web Service stays awake."""
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"FF Helper bot is alive")

    def log_message(self, format, *args):
        pass


def run():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


def start():
    threading.Thread(target=run, daemon=True).start()
