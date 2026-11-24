# main API class, exposes methods for user call

import sys
import inspect

import internal.tracer as tracer
import internal.graphics.viewer as viewer
from internal.graphics.visualizer import RuntimeVisualizer

from api.config import Config

# tracks start status of graphics viewer
# viewer must be started to receive HTML from visualizer
started = False

# tracks if an update call is in progress
# prevents internal recursion from trace_callback()
updating = False
visualizer = RuntimeVisualizer()

file_to_update = None

# updates the visualization with the current state
def update():
    _internal_update()

# internal tracing function, used by auto draw
def _trace_callback(frame, event, arg):
    global file_to_update

    if event != "line" or frame.f_code.co_filename != file_to_update:
        return _trace_callback

    _internal_update()

    return _trace_callback

# starts automatic updates to visualization
# updates occur every line
# see _trace_callback and sys.settrace() for specifics
def start_auto():
    global file_to_update

    caller = inspect.currentframe().f_back

    file_to_update = caller.f_code.co_filename

    caller.f_trace = _trace_callback

    sys.settrace(_trace_callback)

# stops automatic updates to visualization
def stop_auto():
    global file_to_update

    caller = inspect.currentframe().f_back

    file_to_update = None

    caller.f_trace = None

    sys.settrace(None)

# method for configuring how visualization is done
"""
debug: bool, toggles debug mode
render_frames: bool, enables drawing of frames (function and global)
max_scopes: int, how many scopes to draw (1 for only the current scope)
height: int, height of the viewer window
width: int, width of the viewer window
bg_color: str, color of the background expressed in hex rgb string (ex. #FF0000)
font_color: str, color of the font expressed in hex rgb string (ex. #FF0000)

For default values, see config.py
"""
def configure(debug: bool=None, render_frames: bool=None, max_scopes: int=None,
              height: int=None, width: int=None, bg_color: str=None, font_color: str=None):
    # get the singleton config object and call update on it
    Config().update(sel_debug=debug, render_frames=render_frames, max_scopes=max_scopes,
                    height=height, width=width, bg_color=bg_color, font_color=font_color)

def _internal_update():
    global started, updating

    if updating:
        return

    if not started:
        viewer.start()
        started = True

    updating = True

    steps = Config().get_opt('steps_back')
    scopes = Config().get_opt('max_scopes')
    snapshot = tracer.trace(steps, scopes)

    viewer.draw(visualizer.visualize(snapshot))

    updating = False