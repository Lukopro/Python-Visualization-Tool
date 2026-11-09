import types
from typing import Any
from internal.databridge import *
import inspect

def trace(steps_back: int, max_scopes: int | None = None) -> RuntimeSnapshot:
    snapshot = RuntimeSnapshot()
    objects = snapshot.objects

    # Get caller's frame
    frame = inspect.currentframe()

    for _ in range(steps_back):
        if frame is None or frame.f_back is None:
            raise RuntimeError("Could not retrieve caller's frame\n")

        frame = frame.f_back

    # Get all active frames in caller's source file and within max_scopes
    source_file = frame.f_code.co_filename

    frames = []
    while frame is not None and (max_scopes is None or len(frames) < max_scopes):
        if frame.f_code.co_filename != source_file:
            break
        frames.append(frame)
        frame = frame.f_back

    # Iterate the frames top-down
    frames.reverse()

    for frame in frames:

        # Global frame
        if frame.f_code.co_name == "<module>":
            snapshot.global_frame = GlobalFrame(
                bindings={
                    name: _capture_value(value, objects, set())
                    for name, value in frame.f_locals.items()
                    if not name.startswith("__")
                }
            )
            continue

        # Function frame
        arguments = _get_arguments(frame, objects, set())

        function_frame = FunctionFrame(
            name=frame.f_code.co_name,
            return_value=UNSET, # Force an unset return value until implemented
            arguments=arguments,
            bindings={
                name: _capture_value(value, objects, set())
                for name, value in frame.f_locals.items()
                if name not in arguments
            }
        )

        snapshot.function_frames.append(function_frame)

    return snapshot

# Take 'value' of any type and capture it to put in 'objects'
def _capture_value(value: Any, objects: dict[ObjectID, Object], capturing: set[ObjectID]) -> Value:
    # Inline primitives
    if isinstance(value, InlineValue):
        return value

    # Generate id
    object_id = ObjectID(id(value))

    # Skip capturing if we already captured it
    if object_id in objects:
        return object_id

    # Make sure we're not already capturing it, to prevent infinite recursion
    if object_id in capturing:
        return object_id

    capturing.add(object_id)

    # Capture it as an arbitrary, non-primitive object
    objects[object_id] = _capture_object(value, objects, capturing)

    capturing.remove(object_id)

    return object_id


def _capture_object(value: Any, objects: dict[ObjectID, Object], capturing: set[ObjectID]) -> Object:
    # Lists, tuples, sets
    if isinstance(value, (list, tuple, set)):
        return SequenceObject(
            type=type(value).__name__,
            values=[
                _capture_value(item, objects, capturing)
                for item in value
            ]
        )

    # Dicts
    if isinstance(value, dict):
        return MappedObject(
            type=type(value).__name__,
            values={
                _capture_value(key, objects, capturing):
                    _capture_value(item, objects, capturing)
                for key, item in value.items()
            }
        )

    # Classes
    if isinstance(value, type):
        return MappedObject(
            type=value.__name__,
            values={
                _capture_value(name, objects, capturing):
                    _capture_value(member, objects, capturing)
                for name, member in vars(value).items()
                if not name.startswith("__")
            }
        )

    # Functions
    if isinstance(value, types.FunctionType):
        return FunctionObject(
            name=value.__name__,
            parameters=list(value.__code__.co_varnames[:value.__code__.co_argcount]),
        )

    # Built-ins
    if isinstance(value, types.BuiltinFunctionType):
        return FunctionObject(
            name=value.__name__,
            parameters=[]
        )

    # Instances
    if (hasattr(value, "__dict__")
    and type(value).__module__ != "builtins"):
        return MappedObject(
            type=type(value).__name__,
            values={
                _capture_value(name, objects, capturing):
                    _capture_value(member, objects, capturing)
                for name, member in vars(value).items()
            }
        )

    # Otherwise, unsupported
    return UnsupportedObject(
        type(value).__name__,
    )

def _get_arguments(frame, objects: dict[ObjectID, Object], capturing: set[ObjectID]) -> dict[str, Value]:
    code = frame.f_code

    argument_names = (
        # Positional argument names
        list(code.co_varnames[:code.co_argcount])

        # Keyword-only argument names
        + list(code.co_varnames[
            code.co_argcount:
            code.co_argcount + code.co_kwonlyargcount
        ])

        # Skip *args and **kwargs for now
    )

    # Return captured name-value pairs for every argument that's in the frame
    return {
        name: _capture_value(frame.f_locals[name], objects, capturing)
        for name in argument_names
        if name in frame.f_locals
    }