from dataclasses import dataclass, field

@dataclass(frozen=True)
class ObjectID:
    value: int

    def __str__(self) -> str:
        return str(self.value)

InlineValue = int | str | bool | float | None # | bytes | complex
Value = InlineValue | ObjectID

# primitive, list, tuple, set
@dataclass
class SequenceObject:
    type: str
    value: list[Value]

# dict, class, instance
@dataclass
class MappedObject:
    type: str
    value: dict[Value, Value]

# functions
@dataclass
class FunctionObject:
    name: str
    parameters: list[str]

@dataclass
class UnsupportedObject:
    type: str

Object = SequenceObject | MappedObject | FunctionObject | UnsupportedObject

@dataclass
class GlobalFrame:
    bindings: dict[str, Value] = field(default_factory=dict)

class Unset:
    pass
UNSET = Unset() # Sentinel for unset return value

@dataclass
class FunctionFrame:
    name: str

    return_value: Value | Unset = UNSET
    arguments: dict[str, Value] = field(default_factory=dict)
    bindings: dict[str, Value] = field(default_factory=dict)


@dataclass
class RuntimeSnapshot:
    objects: dict[ObjectID, Object] = field(default_factory=dict)
    global_frame: GlobalFrame = field(default_factory=GlobalFrame)
    function_frames: list[FunctionFrame] = field(default_factory=list)

    def __str__(self) -> str:
        lines = ["RuntimeSnapshot"]

        lines.append("  Global:")
        for name, value in self.global_frame.bindings.items():
            lines.append(f"    {name} = {value}")

        if self.function_frames:
            lines.append("  Functions:")
            for frame in self.function_frames:
                lines.append(f"    {frame.name}")

                if frame.arguments:
                    lines.append(f"    {frame.arguments}")

                if frame.bindings:
                    lines.append(f"    {frame.bindings}")

                if frame.return_value:
                    lines.append(f"    {frame.return_value}")

        lines.append("  Objects:")
        for object_id, obj in self.objects.items():
            lines.append(f"    {object_id}: {obj}")

        return "\n".join(lines)
