from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 5173
DIST_DIR = Path(__file__).resolve().parent / "frontend" / "dist"


class SpaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def do_GET(self):
        target = DIST_DIR / self.path.lstrip("/")
        if self.path in ("/", ""):
            self.path = "/index.html"
        elif not target.exists() and not self.path.startswith("/assets/"):
            self.path = "/index.html"
        return super().do_GET()


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), SpaHandler).serve_forever()
