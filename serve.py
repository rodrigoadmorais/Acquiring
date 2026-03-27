import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

port = int(os.environ.get("PORT", 3000))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        print(format % args, flush=True)

print(f"Server running at http://localhost:{port}/", flush=True)
HTTPServer(("localhost", port), Handler).serve_forever()
