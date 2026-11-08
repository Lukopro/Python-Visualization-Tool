from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import subprocess
import sys
import threading

_process = None
_lock = threading.Lock()

_POLL_INTERVAL = 150

def start() -> None:
    global _process

    with _lock:
        if _process is not None and _process.poll() is None:
            return

        _process = subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "--html-viewer-worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, # Discard errors
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )

        try:
            # Make sure server starts before draw() is called
            assert _process.stdout is not None
            ready = _process.stdout.readline().strip()

            if not ready.startswith("READY "):
                raise RuntimeError(f"Viewer failed to start. Worker exit code: {_process.poll()}")

            _process.stdout.close()

        except BaseException:
            _terminate()
            raise

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

def close() -> None:
    with _lock:
        _terminate()

def _terminate() -> None:
    global _process

    if _process is None:
        return

    if _process.poll() is None:

        if _process.stdin is not None:
            _process.stdin.write(json.dumps(None) + "\n")
            _process.stdin.flush()
            _process.stdin.close()

        _process.terminate()
        try:
            _process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            _process.kill()
            _process.wait()
    _process = None

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
                page = f"""<!doctype html>
                <html>
                    <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                        <style>
                        html, body, iframe {{
                            width: 100%;
                            height: 100%;
                            margin: 0;
                            border: 0;
                            overflow: hidden;
                        }}
                        </style>
                    </head>
                    
                    <body>
                    <iframe id="view" title="Graphics viewer"></iframe>
                        <script>
                        let previous = null;
                        let updating = false;
                        
                        async function refresh() {{
                            if (updating) return;
                            updating = true;
                            
                            try {{
                                const response = await fetch('/state', {{cache: 'no-store'}});
                                if (!response.ok) {{
                                    throw new Error('Snapshot request failed: ' + response.status);
                                }}
                                
                                const html = await response.json();
                                if (html !== previous) {{
                                    document.getElementById('view').srcdoc = html;
                                    previous = html;
                                }}
                            }} catch (e) {{
                                console.error('HTML viewer update failed:', e);
                            }} finally {{
                                updating = false;
                                setTimeout(refresh, {_POLL_INTERVAL});
                            }}
                        }}
                        
                        refresh();
                        </script>
                    </body>
                </html>
                """.encode("utf-8")

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)
                return

            self.send_error(404)

    def read_updates():
        try:
            for line in sys.stdin:
                try:
                    html = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if html is None:
                    stop.set()
                    break

                if isinstance(html, str):
                    with state_lock:
                        state["html"] = html
        finally:
            stop.set()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True

    threading.Thread(target=server.serve_forever, name="html-viewer-http", daemon=True).start()

    print(f"READY {server.server_port}", flush=True)

    threading.Thread(target=read_updates, name="html-viewer-input", daemon=True).start()

    try:
        window = webview.create_window(
            "Graphics viewer",
            f"http://127.0.0.1:{server.server_port}/",
            width=960, height=960, min_size=(360, 360)
        )

        window.events.closed += lambda *_: stop.set()
        webview.start()
    finally:
        stop.set()
        server.shutdown()
        server.server_close()

if __name__ == "__main__" and sys.argv[1:] == [
    "--html-viewer-worker"
]:
    _run_worker()