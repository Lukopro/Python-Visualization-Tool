from databridge import *

from pyvis.network import Network
import json

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

    def __init__(self, *, height: str = "900px", width: str = "100%",
                 directed: bool = True) -> None:
        self._inline_counter = 0
        self._anchor_specs: list[dict] = []
        self._char_width = 8.43
        self._line_height = 14

        self.net = Network(height=height, width=width, directed=directed,
                           bgcolor="#ffffff", font_color="#111827")

        self.net.set_options(
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
        )

    def visualize(self, snapshot: RuntimeSnapshot, renderFrames: bool=True) -> str:
        self._add_objects(snapshot.objects)
        if renderFrames:
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
                            """)

        html = html.replace("</body>",
                            f"""
                            <script>
                            (function () {{
                                const anchorSpecs = {json.dumps(self._anchor_specs)}
                                
                                function syncAnchors() {{
                                    if (typeof network === "undefined" || !network.body) return;
                                    
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
                                
                                // Start continuous synchronization immediately
                                requestAnimationFrame(syncAnchors);
                            }})();
                            </script>
                            </body>
                            """)

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
        items = list(enumerate(obj.value))

        lines, anchors = self._mapping_layout(items)

        label = f"{obj.type}"
        label += "\n\n" + "\n".join(lines) if lines else "\n(empty)"

        self.net.add_node(
            node_id,
            label=label,
            title=f"{self._escape(obj.type)}\nObjectID = {object_id}\nlength = {len(obj.value)}",
            shape="box",
            color=self.COLORS["sequence"],
            font={"color": "#FFFFFF"}
        )

        self._add_node_anchors(node_id, anchors)

    def _add_mapped_node(self, object_id: ObjectID, obj: MappedObject) -> None:
        node_id = self._object_node_id(object_id)
        items = list(obj.value.items())

        lines, anchors = self._mapping_layout(items)

        label = f"{obj.type}"
        label += "\n\n" + "\n".join(lines) if lines else "\n(empty)"

        self.net.add_node(
            node_id,
            label=label,
            title=f"{self._escape(obj.type)}\nObjectID = {object_id}\nsize = {len(obj.value)}",
            shape="box",
            color=self.COLORS["mapping"],
            font={"color": "#FFFFFF"}
        )

        self._add_node_anchors(node_id, anchors)

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
        return
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
        return
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
        items = list(frame.bindings.items())

        lines, anchors = self._mapping_layout(items)

        label = f"Global Frame"
        label += "\n\n" + "\n".join(lines) if lines else "\n(empty)"

        self.net.add_node(node_id, label=label, title="Global Frame",  shape="box",
                color=self.COLORS["global"], font={"color": "#FFFFFF", "size": 16}, margin=12)

        for name, value in frame.bindings.items():
            self._add_binding(source=node_id, name=name, value=value)

        self._add_node_anchors(node_id, anchors)

    def _add_function_frames(self, frames: list[FunctionFrame]) -> None:
        for index, frame in enumerate(frames):
            node_id = self._function_frame_node_id(index)
            items = list(frame.arguments.items()) + list(frame.bindings.items())

            lines, anchors = self._mapping_layout(items)

            label = f"{frame.name}"
            label += "\n\n" + "\n".join(lines) if lines else "\n(empty)"

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

            self._add_node_anchors(node_id, anchors)

    def _add_binding(self, *, source: str, name: str, value: Value, kind: str = "binding") -> None:
        self._add_value_edge(source=source, value=value, label=name)

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
            else len(self._format_inline_value(value))
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
            self.net.add_node(anchor_id, label="                                              ", shape="box",
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
            self.net.add_edge(anchor_id, target_id, title=f"{self._escape(spec['label'])} → Object #{spec['target']}")

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

    def _has_node(self, node_id: str) -> bool:
        return any(node["id"] == node_id for node in self.net.nodes)

    @staticmethod
    def _escape(value: str) -> str:
        return (value
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))