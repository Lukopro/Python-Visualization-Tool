from internal.databridge import *

from internal.graphics.graph import Graph

# this class bundles configuration options to be used by visualizer
class VisualizerConfig:
    configOpts = {}

    def __init__(self):
        self.configOpts['renderFrames'] = True
        self.configOpts['height'] = "900px"
        self.configOpts['width'] = "100%"
        self.configOpts['directed'] = True
        self.configOpts['bgcolor'] = "#ffffff"
        self.configOpts['font_color'] = "#111827"
        # more config options initialized here

    # used to update configuration settings
    # ex. configure(renderFrames=True) would set renderFrames to True
    def update(self, renderFrames: bool=None, height: str=None, width: str=None,
               directed: bool=None, bgcolor: str=None, font_color: str=None):

        if renderFrames is not None:
            self.configOpts['renderFrames'] = renderFrames
        if height is not None:
            self.configOpts['height'] = height
        if width is not None:
            self.configOpts['width'] = width
        if directed is not None:
            self.configOpts['directed'] = directed
        if bgcolor is not None:
            self.configOpts['bgcolor'] = bgcolor
        if font_color is not None:
            self.configOpts['font_color'] = font_color
        # this pattern can repeat for as many configurations we have

    # getter function for visualizer to read specific config options
    def get_opt(self, opt):
        return self.configOpts[opt]
    # returns formatted string of all configuration options
    def __str__(self):
        resultStr = ""
        for opt, val in self.configOpts.items():
            resultStr += f"{opt<20}: {val}\n"
        return resultStr


class RuntimeVisualizer:

    def __init__(self) -> None:

        # configuration object, use this object when referencing user-set options
        self.config = VisualizerConfig()

        # initialize the graph
        self.graph = Graph()

    # updates the visualizer's config object
    def update_config(self, renderFrames: bool=None, height: str=None, width: str=None,
                      directed: bool=None, bgcolor: str=None, font_color: str=None):
        self.config.update(renderFrames=renderFrames, height=height, width=width,
                           directed=directed, bgcolor=bgcolor, font_color=font_color)

        # Update graph's config too, for now
        self.graph.configure(height=height, width=width, directed=directed,
                             bgcolor=bgcolor, font_color=font_color)

    def visualize(self, snapshot: RuntimeSnapshot) -> str:
        # Clear graph, start fresh
        self.graph.reset_network()

        # First, add nodes
        for object_id, obj in snapshot.objects.items():
            # Filter object types and delegate
            match obj:
                case SequenceObject():
                    self.graph.add_sequence_node(object_id, obj)
                case MappedObject():
                    self.graph.add_mapped_node(object_id, obj)
                case FunctionObject():
                    self.graph.add_function_node(object_id, obj)
                case UnsupportedObject():
                    self.graph.add_unsupported_node(object_id, obj)
                case _:
                    raise TypeError(f"Unknown object type: {type(obj)!r}")

        # Then, add edges
        for object_id, obj in snapshot.objects.items():
            if isinstance(obj, SequenceObject):
                for index, value in enumerate(obj.values):
                    if isinstance(value, ObjectID):
                        label = f"[{index}]"
                        self.graph.add_value_edge(object_id, label, value)
            elif isinstance(obj, MappedObject):
                for key, value in obj.values.items():
                    if isinstance(value, ObjectID):
                        self.graph.add_mapping_entry(object_id, key, value)

            # FunctionObject and UnsupportedObject don't contain references

        # Then add frames and bind objects
        if self.config.get_opt('renderFrames'):
            if snapshot.global_frame is not None:
                self.graph.add_global_frame(snapshot.global_frame)
            self.graph.add_function_frames(snapshot.function_frames)

        return self.graph.html()