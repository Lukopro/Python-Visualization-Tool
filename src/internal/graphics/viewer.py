from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
import subprocess
import sys
import threading

from api.config import Config

_LOGGER = logging.getLogger(__name__)
_process = None
_lock = threading.Lock()

_POLL_INTERVAL = 150
_WORKER_ARGUMENT = "--html-viewer-worker"
_CONSOLE_ARGUMENT = "--console-logging"


def start(*, console_logging: bool = False) -> None:
    """Start the viewer. Set console_logging to show viewer logs in the console."""
    global _process

    if console_logging:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s:%(name)s:%(message)s",
        )

    with _lock:
        if _process is not None and _process.poll() is None:
            return

        arguments = [sys.executable, os.path.abspath(__file__), _WORKER_ARGUMENT]
        if console_logging:
            arguments.append(_CONSOLE_ARGUMENT)

        _process = subprocess.Popen(
            arguments,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None if console_logging else subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        try:
            if _process.stdout is None:
                raise RuntimeError("Viewer output is unavailable.")

            ready = _process.stdout.readline().strip()
            if not ready.startswith("READY "):
                raise RuntimeError(f"Viewer failed to start. Worker exit code: {_process.poll()}")

            _process.stdout.close()
            _LOGGER.info("Viewer started.")
        except Exception:
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
            _LOGGER.debug("Updated viewer content.")
        except (BrokenPipeError, OSError) as e:
            _LOGGER.error("Could not send content to the viewer.")
            raise RuntimeError("Viewer has closed.") from e


def close() -> None:
    with _lock:
        _terminate()


def _terminate() -> None:
    global _process

    process = _process
    if process is None:
        return

    _process = None
    if process.poll() is None:
        try:
            if process.stdin is not None:
                process.stdin.write(json.dumps(None) + "\n")
                process.stdin.flush()
                process.stdin.close()
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        except (BrokenPipeError, OSError):
            process.terminate()
            process.wait()
    _LOGGER.info("Viewer stopped.")


def _run_worker(*, console_logging: bool = False) -> None:
    import webview

    if console_logging:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s:%(name)s:%(message)s",
        )

    state = {"html": "<h2>Waiting for HTML...</h2>"}
    state_lock = threading.Lock()
    stop = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def _send_content(self, content: bytes, content_type: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, format: str, *args: object) -> None:
            _LOGGER.debug("%s - %s", self.address_string(), format % args)

        def do_GET(self) -> None:
            if self.path == "/state":
                with state_lock:
                    payload = json.dumps(state["html"]).encode("utf-8")

                self._send_content(payload, "application/json; charset=utf-8")
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
                        
                        #viewer-container {{
                            position: relative;
                            width: 100%;
                            height: 100%;
                        }}
                        
                        #viewer-container iframe {{
                            position: absolute;
                            inset: 0;
                            width: 100%;
                            height: 100%;
                            border: 0;
                        }}
                        </style>
                    </head>
                    
                    <body>
                    <div id="viewer-container">
                        <iframe id="view" title="Graphics viewer"></iframe>
                    </div>
                        <script>
                            let previous = null;
                            let updating = false;
                            
                            function captureCamera(view) {{
                                try {{
                                    const network = view.contentWindow.network;
                                    
                                    if (!network) return null;
                                    
                                    return {{
                                        position: network.getViewPosition(),
                                        scale: network.getScale()
                                    }};
                                }} catch (e) {{
                                    console.warn("Could not capture camera: ", e);
                                    return null;
                                }}
                            }}
                            
                            function restoreCamera(view, cameraState) {{
                                return new Promise((resolve, reject) => {{
                                    let attempts = 0;
                                    
                                    const restore = () => {{
                                        try {{
                                            const network = view.contentWindow.network;
                                            
                                            if (!network) {{
                                                if (++attempts < 100) {{
                                                    setTimeout(restore, 50);
                                                }} else {{
                                                    reject(new Error("Network initialization timed out."));
                                                }}
                                                return;
                                            }}
                                            
                                            if (cameraState) {{
                                                network.moveTo({{
                                                    position: cameraState.position,
                                                    scale: cameraState.scale,
                                                    animation: false
                                                }});
                                            }}
                                            
                                            resolve();
                                        }} catch (e) {{
                                            reject(e);
                                        }}
                                    }};
                                    
                                    restore();
                                }});
                            }}
                            
                            async function replaceView(html) {{
                                const container = document.getElementById("viewer-container");
                                
                                const oldView = document.getElementById("view");
                                const cameraState = captureCamera(oldView);
                                
                                const newView = document.createElement("iframe");
                                
                                newView.style.visibility = "hidden";
                                newView.style.zIndex = '2';
                                
                                container.appendChild(newView);
                                
                                try {{
                                    await new Promise((resolve, reject) => {{
                                        newView.onload = resolve;
                                        newView.onerror = reject;
                                        newView.srcdoc = html;
                                    }});
                                    
                                    await restoreCamera(newView, cameraState);
                                    
                                    newView.id = "view";
                                    newView.style.visibility = "visible";
                                    
                                    oldView.remove();
                                    return true;
                                }} catch (e) {{
                                    console.error("Could not replace viewer: ", e);
                                    newView.remove();
                                    return false;
                                }}
                            }}
                            
                            async function refresh() {{
                                if (updating) return;
                                updating = true;
                                
                                try {{
                                    const response = await fetch("/state", {{ cache: "no-store" }});
                                    if (!response.ok) {{
                                        throw new Error("Snapshot request failed: " + response.status);
                                    }}
                                    
                                    const html = await response.json();
                                    
                                    if (html !== previous) {{
                                        const success = await replaceView(html);
                                        if (success) previous = html;
                                    }}
                                }} catch (e) {{
                                    console.error("Viewer refresh failed: ", e);
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

                self._send_content(page, "text/html; charset=utf-8")
                return

            self.send_error(404)

    def read_updates() -> None:
        try:
            for line in sys.stdin:
                try:
                    html = json.loads(line)
                except json.JSONDecodeError:
                    _LOGGER.warning("Ignoring invalid viewer update.")
                    continue

                if html is None:
                    stop.set()
                    break

                if isinstance(html, str):
                    with state_lock:
                        state["html"] = html
                else:
                    _LOGGER.warning("Ignoring viewer update with an unsupported value.")
        finally:
            stop.set()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True

    threading.Thread(target=server.serve_forever, name="html-viewer-http", daemon=True).start()

    print(f"READY {server.server_port}", flush=True)
    _LOGGER.info("Viewer server listening on port %s.", server.server_port)

    threading.Thread(target=read_updates, name="html-viewer-input", daemon=True).start()

    try:
        window = webview.create_window(
            "Graphics viewer",
            f"http://127.0.0.1:{server.server_port}/",
            width=Config().get_opt('width'),
            height=Config().get_opt('height'),
            min_size=(400, 400),
        )

        window.events.closed += lambda *_: stop.set()

        # Pass debug=True to open DevTools
        webview.start()
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        _LOGGER.info("Viewer server stopped.")


if __name__ == "__main__" and sys.argv[1:] in (
    [_WORKER_ARGUMENT],
    [_WORKER_ARGUMENT, _CONSOLE_ARGUMENT],
):
    _run_worker(console_logging=_CONSOLE_ARGUMENT in sys.argv[1:])