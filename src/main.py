import tracer
import viewer
from visualizer import RuntimeVisualizer

started = False

def update(renderFrames: bool=True):
    global started

    if not started:
        viewer.start()
        started = True

    snapshot = tracer.trace()
    viewer.draw(RuntimeVisualizer().visualize(snapshot, renderFrames=renderFrames))