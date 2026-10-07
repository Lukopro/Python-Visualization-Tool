from __future__ import annotations

from pathlib import Path
import webbrowser

from databridge import *

from pyvis.network import Network

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
                        "gravitationalConstant": -40,
                        "centralGravity": 0.01,
                        "springLength": 50,
                        "springConstant": 0.04,
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

    def visualize(self, snapshot: RuntimeSnapshot) -> None:
        self._add_objects(snapshot.objects)
        self._add_global_frame(snapshot.global_frame)
        self._add_function_frames(snapshot.function_frames)

        self.net.write_html("runtime.html", notebook=False, open_browser=False)

        html = Path("runtime.html").read_text()

        html = html.replace("</body>",
                                """
                                    <button
                                        onclick="
                                            const enabled = network.physics.options.enabled;
                                            network.setOptions({ physics: { enabled: !enabled } });
                                            this.textContent = !enabled ? 'Physics: ON' : 'Physics: OFF';
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

        Path("runtime.html").write_text(html)

        webbrowser.open("runtime.html")

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

        self.net.add_node(
            node_id,
            label=f"{obj.type}\n#{object_id}",
            title=f"{self._escape(obj.type)}\nObjectID = {object_id}\nlength = {len(obj.value)}",
            shape="ellipse",
            color=self.COLORS["sequence"],
            font={"color": "#FFFFFF"}
        )

    def _add_mapped_node(self, object_id: ObjectID, obj: MappedObject) -> None:
        node_id = self._object_node_id(object_id)

        self.net.add_node(
            node_id,
            label=f"{obj.type}\n#{object_id}",
            title=f"{self._escape(obj.type)}\nObjectID = {object_id}\nsize = {len(obj.value)}",
            shape="database",
            color=self.COLORS["mapping"],
            font={"color": "#FFFFFF"}
        )

    def _add_function_node(self, object_id: ObjectID, obj: FunctionObject) -> None:
        node_id = self._object_node_id(object_id)

        parameters = ", ".join(obj.parameters)

        self.net.add_node(
            node_id,
            label=f"function {obj.name}\n#{object_id}",
            title=(
                "Function\n"
                f"name = {self._escape(obj.name)}\n"
                f"parameters = {self._escape(parameters)}\n"
                f"ObjectID = {object_id}"
            ),
            shape="box",
            color=self.COLORS["function"],
            font={"color": "#111827"}
        )

    def _add_unsupported_node(self, object_id: ObjectID, obj: UnsupportedObject) -> None:
        node_id = self._object_node_id(object_id)

        self.net.add_node(
            node_id,
            label=f"{obj.type}\n#{object_id}",
            title=f"Unsupported Object\ntype = {self._escape(obj.type)}\nObjectID = {object_id}",
            shape="box",
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
                        kind: str = "value", color: str | None = None) -> None:
        if isinstance(value, ObjectID):
            target = self._object_node_id(value)

            self.net.add_edge(source, target, label=label, color=color,
                              title=f"{self._escape(label)} → Object #{value}")

            return

        # Inline value
        target = self._inline_node_id()

        if not self._has_node(target):
            self.net.add_node(
                target,
                label=self._format_inline_value(value),
                title=f"Inline value\n{self._format_inline_value(value)}",
                shape="box",
                color=self.COLORS["inline"],
                font={"color": "#FFFFFF"}
            )

        self.net.add_edge(source, target, label=label, color=color,
                title=f"{kind}: {self._format_inline_value(value)}", dashes=True, length=40)

    def _add_mapping_entry(self, *, source: str, key: Value, value: Value) -> None:
        key_text = self._format_value(key)

        self._add_value_edge(source=source, value=value, label=f"[{key_text}]", kind="mapping")

    def _add_global_frame(self, frame: GlobalFrame) -> None:
        node_id = "frame:global"

        self.net.add_node(node_id, label="Global Frame", title="Global Frame",  shape="box",
                color=self.COLORS["global"], font={"color": "#FFFFFF", "size": 16}, margin=12)

        for name, value in frame.bindings.items():
            self._add_binding(source=node_id, name=name, value=value)

    def _add_function_frames(self, frames: list[FunctionFrame]) -> None:
        for index, frame in enumerate(frames):
            node_id = self._function_frame_node_id(index)

            self.net.add_node(
                node_id,
                label=f"Frame; {frame.name}",
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
                                    label="return", kind="return", color="#DC2626")


    def _add_binding(self, *, source: str, name: str, value: Value, kind: str = "binding") -> None:
        self._add_value_edge(source=source, value=value, label=name, kind=kind)

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
    def _format_value(value: Value) -> str:
        if isinstance(value, ObjectID):
            return f"Object #{value}"

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