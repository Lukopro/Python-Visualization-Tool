from pyvis.network import Network
from internal.databridge import *
from api.config import Config
import json

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

        self._char_width = 8.43
        self._line_height = 14
        self._anchor_specs: list[dict] = []

        # get the config reference from API
        self.config = Config()

        self.reset_network() # initializes network based on config parameters

    # Remove data, keep config
    def reset_network(self):
        self.network = Network(
            height=str(Config().get_opt('height')) + 'px',
            width=str(Config().get_opt('width')) + 'px',
            directed=True,
            bgcolor=self.config.get_opt("bg_color"),
            font_color=self.config.get_opt("font_color"),
        )

        self.network.set_options(self.get_network_options())

        self._anchor_specs: list[dict] = []

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

        html = html.replace("</body>",
                            f"""
                                    <script>
                                    (function () {{
                                        const anchorSpecs = {json.dumps(self._anchor_specs)}

                                        const anchorsByParent = new Map();

                                        for (const anchor of anchorSpecs) {{
                                            if (!anchorsByParent.has(anchor.parent)) {{
                                                anchorsByParent.set(anchor.parent, []);
                                            }}
                                            anchorsByParent.get(anchor.parent).push(anchor.id);
                                        }}

                                        function getAnchorIds(parentIds) {{
                                            return [...new Set(
                                                parentIds.flatMap(
                                                    parent => anchorsByParent.get(parent) || []
                                                )
                                            )];
                                        }}

                                        function syncAnchors() {{
                                            if (typeof network === "undefined" || !network.body) {{
                                                requestAnimationFrame(syncAnchors);
                                                return;
                                            }}

                                            const parentIds = [...new Set(anchorSpecs.map(a => a.parent))];

                                            const positions = network.getPositions(parentIds);
                                            const updates = [];

                                            for (const anchor of anchorSpecs) {{
                                                const parent = positions[anchor.parent]
                                                if (!parent) continue;

                                                updates.push({{
                                                    id: anchor.id,
                                                    x: parent.x + anchor.dx,
                                                    y: parent.y + anchor.dy
                                                }})
                                            }}

                                            if (updates.length > 0) {{
                                                network.body.data.nodes.update(updates);
                                            }}

                                            requestAnimationFrame(syncAnchors);
                                        }}

                                        let syncingSelection = false;

                                        const userSelected = new Set();
                                        const userSelectedEdges = new Set();

                                        const hoveredParents = new Set();

                                        let observedSelection = new Set(network.getSelectedNodes());

                                        function syncSelection() {{
                                            const requiredParents = new Set(hoveredParents);

                                            for (const id of userSelected) {{
                                                if (anchorsByParent.has(id)) {{
                                                    requiredParents.add(id);
                                                }}
                                            }}

                                            const desired = new Set(userSelected);

                                            for (const id of getAnchorIds([...requiredParents])) {{
                                                desired.add(id);
                                            }}

                                            syncingSelection = true;
                                            try {{
                                                network.setSelection({{
                                                    nodes: [...desired],
                                                    edges: [...userSelectedEdges]
                                                }});

                                                observedSelection = new Set(desired);
                                            }} finally {{
                                                syncingSelection = false;
                                            }}
                                        }}

                                        function handleUserSelectionChange(params) {{
                                            if (syncingSelection) return;

                                            const current = new Set(params.nodes);

                                            for (const id of current) {{
                                                if (!observedSelection.has(id)) {{
                                                    userSelected.add(id);
                                                }}
                                            }}

                                            for (const id of observedSelection) {{
                                                if (!current.has(id)) {{
                                                    userSelected.delete(id);
                                                }}
                                            }}

                                            observedSelection = current;
                                            syncSelection();
                                        }}

                                        network.on("selectNode", handleUserSelectionChange);
                                        network.on("deselectNode", handleUserSelectionChange);

                                        network.on("hoverNode", function(params) {{
                                            const parent = params.node;
                                            if (!anchorsByParent.has(parent)) return;

                                            hoveredParents.add(parent);
                                            syncSelection();
                                        }});

                                        network.on("blurNode", function(params) {{
                                            hoveredParents.delete(params.node);
                                            syncSelection();
                                        }});

                                        network.on("selectEdge", function(params) {{
                                            if (syncingSelection) return;

                                            userSelectedEdges.clear();

                                            for (const id of network.getSelectedEdges()) {{
                                                userSelectedEdges.add(id);
                                            }}
                                        }});

                                        network.on("deselectEdge", function(params) {{
                                            if (syncingSelection) return;

                                            userSelectedEdges.clear();

                                            for (const id of network.getSelectedEdges()) {{
                                                userSelectedEdges.add(id);
                                            }}
                                        }});

                                        // Start continuous synchronization immediately
                                        requestAnimationFrame(syncAnchors);
                                    }})();
                                    </script>
                                    </body>
                                    """)

        return html

    def get_network_options(self):
        # When we have more config options, this will have to replace some values
        '''
                        "layout": {
                            "hierarchical": {
                                "enabled": true,
                                "direction": "LR",
                                "sortMethod": "directed",
                                "shakeTowards": "roots",
                                "levelSeparation": 250,
                                "nodeSpacing": 150,
                                "treeSpacing": 200,
                                "blockShifting": true,
                                "edgeMinimization": true,
                                "parentCentralization": true
                            }
                        },
                        "physics": {
                            "enabled": false
                        },



                        "interaction": {
                            "hover": true,
                            "navigationButtons": false,
                            "keyboard": false,
                            "multiselect": false,
                            "selectConnectedEdges": true
                        },

                        "layout": {
                            "improvedLayout": true
                        },

                        "physics": {
                            "enabled": true,
                            "solver": "forceAtlas2Based",

                            "forceAtlas2Based": {
                                "gravitationalConstant": -40,
                                "centralGravity": 0.01,
                                "springLength": 60,
                                "springConstant": 0.01,
                                "damping": 0.4,
                                "avoidOverlap": 1
                            },

                            "stabilization": {
                                "enabled": true,
                                "fit": false,
                                "iterations": 500
                            }
                        },'''

        return """
                    {
                        "interaction": {
                            "hover": true,
                            "navigationButtons": false,
                            "keyboard": false,
                            "multiselect": false,
                            "selectConnectedEdges": true
                        },

                        "layout": {
                            "improvedLayout": true
                        },

                        "physics": {
                            "enabled": true,
                            "solver": "forceAtlas2Based",

                            "forceAtlas2Based": {
                                "gravitationalConstant": -40,
                                "centralGravity": 0.01,
                                "springLength": 60,
                                "springConstant": 0.01,
                                "damping": 0.4,
                                "avoidOverlap": 1
                            },

                            "stabilization": {
                                "enabled": true,
                                "fit": false,
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
                        },
                        
                        "groups": {
                            "anchor": {
                                "font": {
                                    "face": "monospace",
                                    "size": 1
                                },
                                "color": {
                                    "background": "#EF4444",
                                    "border": "#991B1B"
                                }
                            }
                        }
                    }
                    """

    def add_sequence_node(self, object_id: ObjectID, obj: SequenceObject) -> None:
        node_id = self._object_node_id(object_id)

        # Format label
        items = list(enumerate(obj.values))
        lines, anchors = self._mapping_layout(items)

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

        self._add_node_anchors(node_id, anchors)

    def add_mapped_node(self, object_id: ObjectID, obj: MappedObject) -> None:
        node_id = self._object_node_id(object_id)

        # Format label
        items = list(obj.values.items())
        lines, anchors = self._mapping_layout(items)

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

        self._add_node_anchors(node_id, anchors)

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
        items = list(frame.bindings.items())
        lines, anchors = self._mapping_layout(items)

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
        # for name, value in frame.bindings.items():
            # Inline values are included in labels, so we only check for references
        #     if isinstance(value, ObjectID):
        #         self._add_edge(source=node_id, value=value, label=name)

        self._add_node_anchors(node_id, anchors)

    def add_function_frames(self, frames: list[FunctionFrame]) -> None:
        for index, frame in enumerate(frames):
            node_id = f"frame:function:{index}"

            # Format label
            items = list(frame.arguments.items()) + list(frame.bindings.items())
            lines, anchors = self._mapping_layout(items)

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

            '''# Add arguments
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
                                    label="return", color="#DC2626")'''

            self._add_node_anchors(node_id, anchors)

    def _mapping_layout(self, items: list[tuple[Value, Value]]) -> tuple[list[str], list[dict]]:
        keys = [self._format_value(key) for key, _ in items]

        values = [
            "" if isinstance(value, ObjectID)
            else self._format_value(value)
            for _, value in items
        ]

        key_width = max((len(key) for key in keys), default=0)

        value_width = max((
            len("Object") if isinstance(value, ObjectID)
            else len(self._format_value(value))
            for _, value in items
        ), default=0)

        lines, anchors = [], []
        total_lines = len(items) + 2

        for row, ((key, value), key_text, value_text) in enumerate(
                zip(items, keys, values)
        ):
            line = (
                f"{key_text:>{key_width}}: "
                f"{value_text:<{value_width}}"
            )
            lines.append(line)

            line_index = row + 2

            def offset_for(center_column: float) -> tuple[float, float]:
                dx = (center_column - len(line) / 2) * self._char_width
                dy = (line_index - (total_lines - 2) / 2) * self._line_height - 7
                return dx, dy

            # Reference is in key cell
            if isinstance(key, ObjectID):
                key_start = key_width - len(key_text)
                dx, dy = offset_for(key_start + len(key_text) / 2)

                anchors.append({
                    "row": row,
                    "role": "key",
                    "target": key,
                    "dx": dx,
                    "dy": dy,
                    "label": f"key in entry {row}"
                })

            # Reference is in value cell
            if isinstance(value, ObjectID):
                dx, dy = offset_for(key_width + 2 + value_width / 2)

                anchors.append({
                    "row": row,
                    "role": "value",
                    "target": value,
                    "dx": dx,
                    "dy": dy,
                    "label": f"value in entry {row}"
                })

        return lines, anchors

    def _add_node_anchors(self, parent_id: str, anchors: list[dict]) -> None:
        for spec in anchors:
            anchor_id = f"anchor:{parent_id}:{spec['role']}:{spec['row']}"

            # Invisible, physics-free node; will be positioned in JavaScript
            self.network.add_node(anchor_id, label="                                              ", shape="box",
                              borderWidth=1, physics=False,
                              group='anchor',
                              x=0, y=0, title="", hidden=False, fixed=True)

            self._anchor_specs.append({
                "id": anchor_id,
                "parent": parent_id,
                "dx": spec["dx"],
                "dy": spec["dy"]
            })

            target_id = self._object_node_id(spec["target"])

            # Edge from the anchor to its reference
            self.network.add_edge(anchor_id, target_id, title=f"{self._escape(spec['label'])} → Object #{spec['target']}")

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