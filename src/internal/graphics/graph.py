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
        # Purple → Blue → Cyan
        "global":      "#C99DDD",
        "frame":       "#BCA2DE",
        "class":       "#A2B5E2",
        "instance":    "#9CD7E0", # Use a color generator later?

        # Red → Orange → Yellow → Yellow-green
        "list":        "#E8A09C",
        "tuple":       "#E9B28D",
        "set":         "#E7CB80",
        "dict":        "#D9D985",

        # Other
        "function":    "#C58EAC",
        "unsupported": "#B8B8B8",

        "inline":      "#D9D9D9", # Not currently used
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

        # Get appropriate color
        match obj.type:
            case "list":
                color = self.COLORS["list"]
            case "tuple":
                color = self.COLORS["tuple"]
            case _:
                color = self.COLORS["set"]

        # Add node
        self.network.add_node(
            node_id,
            label=label,
            title=hover_description,
            shape="box",
            color=color,
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

        # Get appropriate color
        match obj.type:
            case "dict":
                color = self.COLORS["dict"]
            case _ if obj.type.startswith("class:"):
                color = self.COLORS["class"]
            case _:
                print(obj.type)
                color = self.COLORS["instance"]

        # Add node
        self.network.add_node(
            node_id,
            label=label,
            title=hover_description,
            shape="box",
            color=color,
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
            node_id = f"frame:function:{index}"

            # Format label
            lines = self._format_mapping_lines(list(
                frame.arguments.items()) + list(frame.bindings.items()))

            label = f"{frame.name}"
            if lines:
                label += "\n\n" + "\n".join(lines)
            else:
                label += "\n(empty)"

            # Add node
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
        # formatted string for object ids
        return f"object:{object_id}"

    @staticmethod
    def _format_value(value: Value) -> str:
        if isinstance(value, ObjectID):
            # Objects are shown by edges, so format them as empty text
            return ""

        # puts single quotes around string
        if isinstance(value, str):
            return repr(value)

        # value is an inline value, format using str() cast
        return str(value)

    @staticmethod
    def _format_mapping_lines(items: list[tuple[Value, Value]]) -> list[str]:

        # get formatted list of keys and values
        keys = []
        values = []
        for key, value in items:
            keys.append(Graph._format_value(key))
            values.append(Graph._format_value(value))

        # get length of longest key
        max_key_width = max((len(key) for key in keys), default=0)

        # get the length of longest value
        max_value_width = max((len(value) for value in values), default=0)

        # return list of formatted strings, where each string is in form "<key_name>: <value>"
        return [
            f"{key:>{max_key_width}}: {value:<{max_value_width}}"
            for key, value in zip(keys, values)
        ]

    def _has_node(self, node_id: str) -> bool:
        # network.get_nodes() returns a list of node ids that are in the graph
        # return whether a node with the specified id exists in the network
        return any(node == node_id for node in self.network.get_nodes())

    @staticmethod
    def _escape(value: str) -> str:
        # escape characters for html
        return (value
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))