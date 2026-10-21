import tracer
import viewer
from visualizer import RuntimeVisualizer

started = False
visualizer = RuntimeVisualizer()

def update():
    global started

    if not started:
        viewer.start()
        started = True

    snapshot = tracer.trace()
    viewer.draw(visualizer.visualize(snapshot))


# wrapper for modifying runtime visualizer configuration object
def configure(renderFrames: bool=None, height: str=None, width: str=None,
               directed: bool=None, bgcolor: str=None, font_color: str=None):
    visualizer.update_config(renderFrames=renderFrames, height=height, width=width,
               directed=directed, bgcolor=bgcolor, font_color=font_color)

