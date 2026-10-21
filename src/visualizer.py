from databridge import *

from pyvis.network import Network


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

    COLORS = {
        "global": "#7973E6",
        "frame": "#9D7CD6",

        "sequence": "#0EA5E9",
        "mapping": "#14B8A6",
        "function": "#F59E0B",
        "unsupported": "#64748B",

        "inline": "#D9D9D9",
    }

    def __init__(self) -> None:

        # configuration object, use this object when referencing user-set options
        self.config = VisualizerConfig()

        self._inline_counter = 0

        # initialize the network
        self.net = self.net_init()

    # updates the visualizer's config object
    def update_config(self, renderFrames: bool=None, height: str=None, width: str=None,
                      directed: bool=None, bgcolor: str=None, font_color: str=None):
        self.config.update(renderFrames=renderFrames, height=height, width=width,
                           directed=directed, bgcolor=bgcolor, font_color=font_color)

    # initialize network
    # call before redrawing as well to get clean slate
    def net_init(self):

        net = Network(height=self.config.get_opt('height'),
                      width=self.config.get_opt('width'),
                      directed=self.config.get_opt('directed'),
                      bgcolor=self.config.get_opt('bgcolor'),
                      font_color=self.config.get_opt('font_color'))

        net.set_options(
            """
            {
                "interaction": {
                    "hover": true,
                    "navigationButtons": false,
                    "keyboard": false,
                    "multiselect": false,
                    "selectConnectedEdges": true
                },

                "physics": {
                    "enabled": true,
                    "solver": "forceAtlas2Based",

                    "forceAtlas2Based": {
                        "gravitationalConstant": -50,
                        "centralGravity": 0.01,
                        "springLength": 60,
                        "springConstant": 0.01,
                        "damping": 0.4,
                        "avoidOverlap": 1
                    },

                    "stabilization": {
                        "enabled": true,
                        "iterations": 500
                    }
                },

                "edges": {
                    "arrows": {
                        "to": {
                            "enabled": true,
                            "scaleFactor": 0.8
                        }
                    },

                    "smooth": {
                        "enabled": true,
                        "type": "dynamic"
                    },

                    "font": {
                       "size": 14,
                       "background": "white",
                       "strokeWidth": 1
                    }
                },

                "nodes": {
                    "font": {
                        "face": "monospace",
                        "size": 14
                    },

                    "borderWidth": 2
                }
            }
            """
        )

        return net

    def visualize(self, snapshot: RuntimeSnapshot) -> str:

        self.net = self.net_init() # reset network

        self._add_objects(snapshot.objects)
        if self.config.get_opt('renderFrames'):
            self._add_global_frame(snapshot.global_frame)
            self._add_function_frames(snapshot.function_frames)

        html = self.net.generate_html()

        html = html.replace("</body>",
                            """
                                <button
                                    onclick="
                                        const newEnabled = !network.physics.options.enabled;
                                        network.setOptions({ 
                                            physics: { enabled: newEnabled },
                                            edges: {
                                                smooth: {
                                                    enabled: true,
                                                    type: newEnabled ? 'dynamic' : 'continuous'
                                                }
                                            }
                                        });
                                        this.textContent = newEnabled ? 'Physics: ON' : 'Physics: OFF';
                                    "
                                    style="
                                        position: fixed;
                                        top: 16px;
                                        left: 10px;
                                        z-index: 9999;
                                        padding: 8px 14px;
                                        border: none;
                                        border-radius: 5px;
                                        background: #485775;
                                        color: white;
                                        font-size: 14px;
                                        cursor: pointer;
                                    "
                                >
                                    Physics: ON
                                </button>
                                </body>
                            """
                            )

        return html

    def _add_objects(self, objects: dict[ObjectID, Object]) -> None:
        # First, nodes
        for object_id, obj in objects.items():
            self._add_object_node(object_id, obj)

        # Then, edges
        for object_id, obj in objects.items():
            self._add_object_edges(object_id, obj)

    def _add_object_node(self, object_id: ObjectID, obj: Object) -> None:
        if isinstance(obj, SequenceObject):
            self._add_sequence_node(object_id, obj)
        elif isinstance(obj, MappedObject):
            self._add_mapped_node(object_id, obj)
        elif isinstance(obj, FunctionObject):
            self._add_function_node(object_id, obj)
        elif isinstance(obj, UnsupportedObject):
            self._add_unsupported_node(object_id, obj)
        else:
            raise TypeError(f"Unknown object type: {type(obj)!r}")

    def _add_sequence_node(self, object_id: ObjectID, obj: SequenceObject) -> None:
        node_id = self._object_node_id(object_id)

        lines = self._format_mapping_lines(list(enumerate(obj.value)))

        label = f"{obj.type}"
        if lines:
            label +="\n\n" + "\n".join(lines)
        else:
            label += "\n(empty)"

        self.net.add_node(
            node_id,
            label=label,
            title=f"{self._escape(obj.type)}\nObjectID = {object_id}\nlength = {len(obj.value)}",
            shape="box",
            color=self.COLORS["sequence"],
            font={"color": "#FFFFFF"}
        )

    def _add_mapped_node(self, object_id: ObjectID, obj: MappedObject) -> None:
        node_id = self._object_node_id(object_id)

        lines = self._format_mapping_lines(list(obj.value.items()))

        label = f"{obj.type}"
        if lines:
            label += "\n\n" + "\n".join(lines)
        else:
            label += "\n(empty)"

        self.net.add_node(
            node_id,
            label=label,
            title=f"{self._escape(obj.type)}\nObjectID = {object_id}\nsize = {len(obj.value)}",
            shape="box",
            color=self.COLORS["mapping"],
            font={"color": "#FFFFFF"}
        )

    def _add_function_node(self, object_id: ObjectID, obj: FunctionObject) -> None:
        node_id = self._object_node_id(object_id)

        parameters = ", ".join(obj.parameters)

        self.net.add_node(
            node_id,
            label=f"function: {obj.name}",
            title=(
                f"Function #{object_id}\n"
                f"name = {self._escape(obj.name)}\n"
                f"parameters = {self._escape(parameters)}\n"
                f"ObjectID = {object_id}"
            ),
            shape="ellipse",
            color=self.COLORS["function"],
            font={"color": "#111827"}
        )

    def _add_unsupported_node(self, object_id: ObjectID, obj: UnsupportedObject) -> None:
        node_id = self._object_node_id(object_id)

        self.net.add_node(
            node_id,
            label=f"{obj.type}",
            title=f"Unsupported Object\ntype = {self._escape(obj.type)}\nObjectID = {object_id}",
            shape="ellipse",
            color=self.COLORS["unsupported"],
            font={"color": "#FFFFFF"}
        )

    def _add_object_edges(self, object_id: ObjectID, obj: Object) -> None:
        node_id = self._object_node_id(object_id)

        if isinstance(obj, SequenceObject):
            for index, value in enumerate(obj.value):
                self._add_value_edge(source=node_id, value=value, label=f"[{index}]")
        elif isinstance(obj, MappedObject):
            for key, value in obj.value.items():
                self._add_mapping_entry(source=node_id, key=key, value=value)

        # FunctionObject and UnsupportedObject don't contain references

    def _add_value_edge(self, *, source: str, value: Value, label: str,
                        color: str | None = None) -> None:

        if not isinstance(value, ObjectID):
            return

        target = self._object_node_id(value)

        self.net.add_edge(source, target, label=label, color=color,
                          title=f"{self._escape(label)} → Object #{value}")

    def _add_mapping_entry(self, *, source: str, key: Value, value: Value) -> None:
        key_text = self._format_value(key)

        self._add_value_edge(source=source, value=value, label=f"[{key_text}]")

    def _add_global_frame(self, frame: GlobalFrame) -> None:
        node_id = "frame:global"

        lines = self._format_mapping_lines(list(frame.bindings.items()))

        label = f"Global Frame"
        if lines:
            label += "\n\n" + "\n".join(lines)
        else:
            label += "\n(empty)"

        self.net.add_node(node_id, label=label, title="Global Frame",  shape="box",
                color=self.COLORS["global"], font={"color": "#FFFFFF", "size": 16}, margin=12)

        for name, value in frame.bindings.items():
            self._add_binding(source=node_id, name=name, value=value)

    def _add_function_frames(self, frames: list[FunctionFrame]) -> None:
        for index, frame in enumerate(frames):
            node_id = self._function_frame_node_id(index)

            lines = self._format_mapping_lines(list(
                frame.arguments.items()) + list(frame.bindings.items()))

            label = f"{frame.name}"
            if lines:
                label += "\n\n" + "\n".join(lines)
            else:
                label += "\n(empty)"

            self.net.add_node(
                node_id,
                label=label,
                title=f"Function Frame\nname = {self._escape(frame.name)}",
                shape="box",
                color=self.COLORS["frame"],
                font={"color": "#FFFFFF", "size": 16},
                margin=12
            )

            for name, value in frame.arguments.items():
                self._add_binding(source=node_id, name=name, value=value, kind="argument")

            for name, value in frame.bindings.items():
                self._add_binding(source=node_id, name=name, value=value)

            if not isinstance(frame.return_value, Unset):
                self._add_value_edge(source=node_id, value=frame.return_value,
                                    label="return", color="#DC2626")


    def _add_binding(self, *, source: str, name: str, value: Value, kind: str = "binding") -> None:
        self._add_value_edge(source=source, value=value, label=name)

    @staticmethod
    def _object_node_id(object_id: ObjectID) -> str:
        return f"object:{object_id}"

    @staticmethod
    def _function_frame_node_id(index: int) -> str:
        return f"frame:function:{index}"

    def _inline_node_id(self) -> str:
        node_id = f"inline:{self._inline_counter}"
        self._inline_counter += 1
        return node_id

    @staticmethod
    def _format_value(value: Value, object_label: str="Object") -> str:
        if isinstance(value, ObjectID):
            return object_label # f"Object #{value}"

        return RuntimeVisualizer._format_inline_value(value)

    @staticmethod
    def _format_inline_value(value: InlineValue) -> str:
        if value is None:
            return "None"

        if isinstance(value, str):
            return repr(value)

        if isinstance(value, bool):
            return "True" if value else "False"

        return str(value)

    @staticmethod
    def _format_mapping_lines(items: list[tuple[Value, Value]]) -> list[str]:
        keys = [RuntimeVisualizer._format_value(key) for key, _ in items]
        max_key_width = max((len(key) for key in keys), default=0)\

        values = [RuntimeVisualizer._format_value(value, "") for _, value in items]
        max_value_width = max((len(value) for value in values), default=0)

        return [
            f"{key:>{max_key_width}}: {value:<{max_value_width}}"
            for key, value in zip(keys, values)
        ]

    def _has_node(self, node_id: str) -> bool:
        return any(node["id"] == node_id for node in self.net.nodes)

    @staticmethod
    def _escape(value: str) -> str:
        return (value
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))