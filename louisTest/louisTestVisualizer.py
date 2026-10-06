"""Display changing program variables in a PyVis browser window."""

from collections.abc import Mapping
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import subprocess
import sys
import threading
from time import sleep
from typing import Any


# The caller owns the process handle; the child process owns the browser server.
_viewer_process: subprocess.Popen[str] | None = None
_viewer_closed = False


def _format_value(value: Any) -> str:
    """Return a compact, single-line representation suitable for a node label."""
    text = repr(value).replace("\r", "\\r").replace("\n", "\\n")
    if len(text) > 240:
        return text[:237] + "..."
    return text


def _run_worker() -> None:
    """Serve the PyVis visualization inside its own desktop window."""
    from pyvis.network import Network
    import webview

    latest_snapshot: list[dict[str, str]] = []
    snapshot_lock = threading.Lock()
    close_event = threading.Event()

    class ViewerHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/shutdown":
                close_event.set()
                self.send_response(204)
                self.end_headers()
                return

            if self.path == "/state":
                with snapshot_lock:
                    payload = json.dumps(latest_snapshot).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return

            if self.path != "/":
                self.send_error(404)
                return
            payload = self.page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, _format: str, *_args: Any) -> None:
            # Avoid writing routine browser polling requests to the console.
            return

    # PyVis supplies the vis-network graph and its browser interaction model.
    # Inline resources make this generated page work without a CDN connection.
    graph = Network(
        height="100vh",
        width="100%",
        bgcolor="#f2f4f5",
        font_color="#172a36",
        directed=False,
        cdn_resources="in_line",
    )
    graph.set_options(
        """
        {
          "nodes": {
            "shape": "box",
            "margin": 12,
            "widthConstraint": {"maximum": 280},
            "font": {"face": "Consolas", "size": 16, "color": "#172a36"},
            "color": {"background": "#ffffff", "border": "#9aabb2", "highlight": {"background": "#e3f2f3", "border": "#167d83"}}
          },
          "edges": {"color": {"color": "#bac6ca"}},
          "physics": {"enabled": false},
          "interaction": {"dragNodes": true, "dragView": true, "zoomView": true, "hover": true, "multiselect": true}
        }
        """
    )
    page = graph.generate_html().replace(
        "</body>",
        """
        <script>
          // Poll the worker for complete snapshots. Updating existing node IDs
          // retains the positions users have chosen by dragging the boxes.
          const knownVariableIds = new Set();
          async function refreshVariables() {
            try {
              const response = await fetch('/state', { cache: 'no-store' });
              if (!response.ok) throw new Error('Snapshot request failed');
              const variables = await response.json();
              const receivedIds = new Set(variables.map(item => item.name));
              const removedIds = [...knownVariableIds].filter(id => !receivedIds.has(id));
              if (removedIds.length) nodes.remove(removedIds);
              for (const id of removedIds) knownVariableIds.delete(id);
              nodes.update(variables.map(item => ({
                id: item.name,
                label: `${item.name}\\n${item.type}\\n${item.value}`,
                title: `${item.name} (${item.type})`
              })));
              for (const id of receivedIds) knownVariableIds.add(id);
            } catch (error) {
              console.error('Unable to refresh variable snapshot:', error);
            }
          }
          refreshVariables();
          setInterval(refreshVariables, 150);
          // The caller may finish before the user closes this window. Keep the
          // worker alive for the final view, then stop it when the page exits.
          window.addEventListener('pagehide', () => navigator.sendBeacon('/shutdown'));
        </script>
        </body>""",
    )

    # Bind only to loopback and let the OS select a free port, avoiding an
    # external service dependency and conflicts with other local applications.
    server = ThreadingHTTPServer(("127.0.0.1", 0), ViewerHandler)
    server.daemon_threads = True
    ViewerHandler.page = page
    server_thread = threading.Thread(target=server.serve_forever, name="pyvis-http", daemon=True)
    server_thread.start()

    url = f"http://127.0.0.1:{server.server_port}/"
    window = webview.create_window(
        "Program Variable Watch",
        url,
        width=1100,
        height=760,
        min_size=(640, 420),
    )
    window.events.closed += lambda *_args: close_event.set()

    # Read snapshots independently so stdin EOF (the caller ending) does not
    # close the browser view. A lock keeps each HTTP response internally stable.
    def read_snapshots() -> None:
        nonlocal latest_snapshot
        for line in sys.stdin:
            try:
                snapshot = json.loads(line)
            except json.JSONDecodeError:
                continue
            with snapshot_lock:
                latest_snapshot = snapshot

    threading.Thread(target=read_snapshots, name="snapshot-input", daemon=True).start()
    # pywebview selects the native platform backend. On Windows this is
    # normally WebView2, displaying the PyVis page in a standalone app window.
    webview.start()
    close_event.set()
    server.shutdown()
    server.server_close()


def _start_viewer() -> subprocess.Popen[str]:
    # Keep the viewer independent of the debugger so a breakpoint cannot freeze
    # the browser page's state server along with the inspected program.
    environment = os.environ.copy()
    for key in tuple(environment):
        if key.upper().startswith(("DEBUGPY_", "PYDEVD_", "VSCODE_DEBUGPY_")):
            environment.pop(key, None)
    # The absolute file path works regardless of cwd; stdin carries snapshots
    # into the worker. Do not use -I here: PyVis may be installed in user-site
    # packages, which isolated mode deliberately hides.
    return subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "--visualizer-worker"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        bufsize=1,
        env=environment,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def draw(variables: Mapping[str, Any], delay_ms: int = 200) -> None:
    """Send a variable snapshot to the independent PyVis browser view.

    Call with locals() at each point where a new state should be displayed.
    Values are converted to display strings before transmission, so the worker
    never needs access to the caller's live objects.
    """
    global _viewer_process, _viewer_closed

    if _viewer_closed:
        return
    # Start lazily so importing this module has no GUI/process side effects.
    if _viewer_process is None:
        try:
            _viewer_process = _start_viewer()
        except OSError:
            _viewer_closed = True
            return
    if _viewer_process.poll() is not None or _viewer_process.stdin is None:
        _viewer_closed = True
        return

    # Debuggers may inject bookkeeping locals. Exclude those without hiding
    # ordinary variables, and sort for stable presentation between snapshots.
    snapshot = [
        {"name": name, "type": type(value).__name__, "value": _format_value(value)}
        for name, value in sorted(variables.items())
        if not name.startswith("__pydevd_")
    ]
    try:
        # Newline-delimited JSON makes each snapshot a complete message. Flush
        # so the worker can serve the update without waiting for a full buffer.
        _viewer_process.stdin.write(json.dumps(snapshot) + "\n")
        _viewer_process.stdin.flush()
    except (BrokenPipeError, OSError):
        _viewer_closed = True
        return

    # Throttle fast loops so snapshots can be observed. The browser stays
    # responsive independently because its server runs in another process.
    if delay_ms > 0:
        sleep(delay_ms / 1000)


# This file is also the worker entry point. The private flag selects the PyVis
# server mode; importing the module has no browser or server side effects.
if __name__ == "__main__" and sys.argv[1:] == ["--visualizer-worker"]:
    _run_worker()

