import sys

import tracer
import viewer
from visualizer import RuntimeVisualizer

started = False
updating = False
visualizer = RuntimeVisualizer()

def update():
    _internal_update()

def trace_callback(frame, event, arg):
    if event != "line":
        return trace_callback

    _internal_update()

    return trace_callback

def start_auto():
    sys.settrace(trace_callback)

def stop_auto():
    sys.settrace(None)

# wrapper for modifying runtime visualizer configuration object
def configure(renderFrames: bool=None, height: str=None, width: str=None,
               directed: bool=None, bgcolor: str=None, font_color: str=None):
    visualizer.update_config(renderFrames=renderFrames, height=height, width=width,
               directed=directed, bgcolor=bgcolor, font_color=font_color)

def _internal_update():
    global started, updating

    if updating:
        return

    if not started:
        viewer.start()
        started = True

    updating = True

    snapshot = tracer.trace(3)
    viewer.draw(visualizer.visualize(snapshot))

    updating = False