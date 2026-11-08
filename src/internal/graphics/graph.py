from pyvis.network import Network
from internal.databridge import *

class GraphConfig:
    DEFAULTS = {
        'height': '900px',
        'width': '100%',
        'directed': True,
        'bgcolor': '#FFFFFF',
        'font_color': "#111827"
    }

    def __init__(self):
        self.height = self.DEFAULTS['height']
        self.width = self.DEFAULTS['width']
        self.directed = self.DEFAULTS['directed']
        self.bgcolor = self.DEFAULTS['bgcolor']
        self.font_color = self.DEFAULTS['font_color']

    def get_network_options(self):
        # When we have more config options, this will have to replace some values
        return """
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


class Graph:
    COLORS = {
        "global": "#7973E6",
        "frame": "#9D7CD6",

        "sequence": "#0EA5E9",
        "mapping": "#14B8A6",
        "function": "#F59E0B",
        "unsupported": "#64748B",

        "inline": "#D9D9D9",
    }

    def __init__(self):
        self.network = None
        self.config = GraphConfig()
        self.reset_network()


    def configure(self, height: str | None = None, width: str | None = None,
                  directed: bool | None = None, bgcolor: str | None = None, font_color: str | None = None):
        if height is not None:
            self.network.height = height
        if width is not None:
            self.network.width = width
        if directed is not None:
            self.network.directed = directed
        if bgcolor is not None:
            self.network.bgcolor = bgcolor
        if font_color is not None:
            self.network.font_color = font_color

    # Remove data, keep config
    def reset_network(self):
        self.network = Network(
            height=self.config.height,
            width=self.config.width,
            directed=self.config.directed,
            bgcolor=self.config.bgcolor,
            font_color=self.config.font_color
        )

        self.network.set_options(self.config.get_network_options())

    def html(self):
        html = self.network.generate_html()

        # Append to html to add physics button
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

    def add_sequence_node(self, object_id: ObjectID, obj: SequenceObject) -> None:
        node_id = self._object_node_id(object_id)

        # Format label
        lines = self._format_mapping_lines(list(enumerate(obj.values)))

        label = f"{obj.type}"
        if lines:
            label +="\n\n" + "\n".join(lines)
        else:
            label += "\n(empty)"

        # Format hover description
        hover_description = (f"{self._escape(obj.type)}\n"
                             f"ObjectID = {object_id}\n"
                             f"length = {len(obj.values)}")

        # Add node
        self.network.add_node(
            node_id,
            label=label,
            title=hover_description,
            shape="box",
            color=self.COLORS["sequence"],
            font={"color": "#FFFFFF"}
        )

    def add_mapped_node(self, object_id: ObjectID, obj: MappedObject) -> None:
        node_id = self._object_node_id(object_id)

        # Format label
        lines = self._format_mapping_lines(list(obj.values.items()))

        label = f"{obj.type}"
        if lines:
            label += "\n\n" + "\n".join(lines)
        else:
            label += "\n(empty)"

        # Format hover description
        hover_description = (f"{self._escape(obj.type)}\n"
                             f"ObjectID = {object_id}\n"
                             f"size = {len(obj.values)}")

        # Add node
        self.network.add_node(
            node_id,
            label=label,
            title=hover_description,
            shape="box",
            color=self.COLORS["mapping"],
            font={"color": "#FFFFFF"}
        )

    def add_function_node(self, object_id: ObjectID, obj: FunctionObject) -> None:
        node_id = self._object_node_id(object_id)

        # Format label
        label = f"function: {obj.name}"

        # Parameters as a readable string
        parameters = ", ".join(obj.parameters)

        # Format hover description
        hover_description = (f"Function #{object_id}\n"
                             f"name = {self._escape(obj.name)}\n"
                             f"parameters = {self._escape(parameters)}\n"
                             f"ObjectID = {object_id}")

        # Add node
        self.network.add_node(
            node_id,
            label=label,
            title=hover_description,
            shape="ellipse",
            color=self.COLORS["function"],
            font={"color": "#111827"}
        )

    def add_unsupported_node(self, object_id: ObjectID, obj: UnsupportedObject) -> None:
        node_id = self._object_node_id(object_id)

        # Format hover description
        hover_description = (f"Unsupported Object\n"
                             f"type = {self._escape(obj.type)}\n"
                             f"ObjectID = {object_id}")

        # Add node
        self.network.add_node(
            node_id,
            label=f"{obj.type}",
            title=hover_description,
            shape="ellipse",
            color=self.COLORS["unsupported"],
            font={"color": "#FFFFFF"}
        )

    # Link a source object to a value object if the source uses a map to reference the value
    def add_mapping_entry(self, source: ObjectID, key: Value, value: ObjectID) -> None:
        label = f"[{self._format_value(key)}]"

        self.add_value_edge(source=source, value=value, label=label)

    # Link a source object to a value object
    def add_value_edge(self, source: ObjectID, label: str, value: ObjectID,
                       *, color: str | None = None) -> None:

        node_id = self._object_node_id(source)

        self._add_edge(node_id, value, label, color)

    # Most direct edge insertion method here, for internal references that have node ids already
    def _add_edge(self, source: str, value: ObjectID, label: str, color: str | None = None) -> None:
        target = self._object_node_id(value)

        hover_description = f"{self._escape(label)} → Object #{value}"

        self.network.add_edge(source, target, label=label, color=color, title=hover_description)

    def add_global_frame(self, frame: GlobalFrame) -> None:
        node_id = "frame:global"

        # Format label
        lines = self._format_mapping_lines(list(frame.bindings.items()))

        label = f"Global Frame"
        if lines:
            label += "\n\n" + "\n".join(lines)
        else:
            label += "\n(empty)"

        # Add node
        self.network.add_node(
            node_id,
            label=label,
            title="Global Frame",
            shape="box",
            color=self.COLORS["global"],
            font={"color": "#FFFFFF", "size": 16},
            margin=12
        )

        # Add bindings
        for name, value in frame.bindings.items():
            # Inline values are included in labels, so we only check for references
            if isinstance(value, ObjectID):
                self._add_edge(source=node_id, value=value, label=name)

    def add_function_frames(self, frames: list[FunctionFrame]) -> None:
        for index, frame in enumerate(frames):
            node_id = self._function_frame_node_id(index)

            lines = self._format_mapping_lines(list(
                frame.arguments.items()) + list(frame.bindings.items()))

            label = f"{frame.name}"
            if lines:
                label += "\n\n" + "\n".join(lines)
            else:
                label += "\n(empty)"

            self.network.add_node(
                node_id,
                label=label,
                title=f"Function Frame\nname = {self._escape(frame.name)}",
                shape="box",
                color=self.COLORS["frame"],
                font={"color": "#FFFFFF", "size": 16},
                margin=12
            )

            # Add arguments
            for name, value in frame.arguments.items():
                # Inline values are included in labels, so we only check for references
                if isinstance(value, ObjectID):
                    self._add_edge(source=node_id, value=value, label=name)

            # Add bindings
            for name, value in frame.bindings.items():
                # Inline values are included in labels, so we only check for references
                if isinstance(value, ObjectID):
                    self._add_edge(source=node_id, value=value, label=name)

            # Add return value
            if not isinstance(frame.return_value, Unset):
                # Not implemented yet
                self._add_edge(source=node_id, value=frame.return_value,
                                    label="return", color="#DC2626")

    @staticmethod
    def _object_node_id(object_id: ObjectID) -> str:
        return f"object:{object_id}"

    @staticmethod
    def _function_frame_node_id(index: int) -> str:
        return f"frame:function:{index}"

    @staticmethod
    def _format_value(value: Value, object_label: str="Object") -> str:
        if isinstance(value, ObjectID):
            return object_label # f"Object #{value}"

        return Graph._format_inline_value(value)

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
        keys = [Graph._format_value(key) for key, _ in items]
        max_key_width = max((len(key) for key in keys), default=0)

        values = [Graph._format_value(value, "") for _, value in items]
        max_value_width = max((len(value) for value in values), default=0)

        return [
            f"{key:>{max_key_width}}: {value:<{max_value_width}}"
            for key, value in zip(keys, values)
        ]

    def _has_node(self, node_id: str) -> bool:
        return any(node["id"] == node_id for node in self.network.nodes)

    @staticmethod
    def _escape(value: str) -> str:
        return (value
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))