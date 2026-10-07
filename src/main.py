import tracer
from visualizer import RuntimeVisualizer

def update():
    snapshot = tracer.trace()
    # print(snapshot)
    RuntimeVisualizer().visualize(snapshot)