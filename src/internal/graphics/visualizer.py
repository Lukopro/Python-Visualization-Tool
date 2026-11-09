from internal.databridge import *
from internal.graphics.graph import Graph
from api.config import Config

class RuntimeVisualizer:

    # get the reference for the config
    config = Config()

    def __init__(self) -> None:

        # initialize the graph
        self.graph = Graph()

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
        if self.config.get_opt('render_frames'):
            if snapshot.global_frame is not None:
                self.graph.add_global_frame(snapshot.global_frame)
            self.graph.add_function_frames(snapshot.function_frames)

        return self.graph.html()