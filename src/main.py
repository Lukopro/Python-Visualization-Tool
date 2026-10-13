import tracer
from visualizer import RuntimeVisualizer

def update(renderFrames: bool=True):
    snapshot = tracer.trace()
    # print(snapshot)
    RuntimeVisualizer().visualize(snapshot, renderFrames=renderFrames)