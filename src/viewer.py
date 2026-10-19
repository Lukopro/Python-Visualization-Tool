from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import subprocess
import sys
import threading

_process = None
_lock = threading.Lock()

def start() -> None:
    global _process

    with _lock:
        if _process is not None and _process.poll() is None:
            return

        _process = subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "--html-viewer-worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )

def draw(html: str) -> None:
    with _lock:
        if _process is None or _process.poll() is not None:
            raise RuntimeError("Viewer is not running. Call start() first.")

        if _process.stdin is None:
            raise RuntimeError("Viewer input is unavailable.")

        try:
            _process.stdin.write(json.dumps(html) + "\n")
            _process.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise RuntimeError("Viewer has closed.") from e

def _run_worker():
    import webview

    state = {"html": "<h2>Waiting for HTML...</h2>"}
    state_lock = threading.Lock()
    stop = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/state":
                with state_lock:
                    payload = json.dumps(state["html"]).encode("utf-8")

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return

            if self.path == "/":
                page = b"""<!doctype html>
                <html>
                    <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        html, body, iframe {
                            width: 100%;
                            height: 100%;
                            margin: 0;
                            border: 0;
                            overflow: hidden;
                        }
                    </style>
                    </head>
                    
                    <body>
                    <iframe id="view" title="Graphics viewer"></iframe>
                        <script>
                        let previous = null;
                        
                        async function refresh() {
                            try {
                                const response = await fetch('/state', {cache: 'no-store'});
                                if (!response.ok) return;
                                
                                const html = await response.json();
                                if (html !== previous) {
                                    document.getElementById('view').srcdoc = html;
                                    previous = html;
                                }
                            } catch (e) {
                                console.error('HTML viewer update failed:', e);
                            }
                        }
                        
                        refresh();
                        setInterval(refresh, 150);
                        </script>
                    </body>
                </html>
                """

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)
                return

            self.send_error(404)

        def log_message(self, format, *args):
            pass

    def read_updates():
        for line in sys.stdin:
            if stop.is_set():
                break
            try:
                html = json.loads(line)
                if isinstance(html, str):
                    with state_lock:
                        state["html"] = html
            except json.JSONDecodeError:
                continue

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True

    threading.Thread(target=server.serve_forever, daemon=True).start()

    threading.Thread(target=read_updates, daemon=True).start()

    window = webview.create_window(
        "Graphics viewer",
        f"http://127.0.0.1:{server.server_port}/",
        width = 960, height = 960, min_size = (360, 360)
    )

    window.events.closed += lambda *_: stop.set()

    try:
        webview.start()
    finally:
        stop.set()
        server.shutdown()
        server.server_close()

if __name__ == "__main__" and sys.argv[1:] == [
    "--html-viewer-worker"
]:
    _run_worker()