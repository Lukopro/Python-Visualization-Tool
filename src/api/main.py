import sys
import inspect

import internal.tracer as tracer
import internal.graphics.viewer as viewer
from internal.graphics.visualizer import RuntimeVisualizer

started = False
updating = False
visualizer = RuntimeVisualizer()

file_to_update = None

def update():
    _internal_update()

def trace_callback(frame, event, arg):
    global file_to_update

    if event != "line" or frame.f_code.co_filename != file_to_update:
        return trace_callback

    print(frame)
    print("Event" + event)

    _internal_update()

    return trace_callback

def start_auto():
    global file_to_update

    caller = inspect.currentframe().f_back

    file_to_update = caller.f_code.co_filename

    caller.f_trace = trace_callback

    sys.settrace(trace_callback)

def stop_auto():
    global file_to_update

    caller = inspect.currentframe().f_back

    file_to_update = None

    caller.f_trace = None

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