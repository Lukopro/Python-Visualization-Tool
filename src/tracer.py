import sys
import types
from databridge import (GlobalFrame, FunctionFrame, RuntimeSnapshot,
                        SequenceObject, MappedObject, FunctionObject,
                        Object, ObjectID, Value, UNSET, UnsupportedObject)


def trace() -> RuntimeSnapshot:
    snapshot = RuntimeSnapshot()
    objects = snapshot.objects

    frame = sys._getframe(2)

    frames = []
    while frame is not None:
        frames.append(frame)
        frame = frame.f_back

    frames.reverse()

    for frame in frames:

        # Global
        if frame.f_code.co_name == "<module>":
            snapshot.global_frame = GlobalFrame(
                bindings={
                    name: capture_value(value, objects, set())
                    for name, value in frame.f_locals.items()
                    if not name.startswith("__")
                }
            )
            continue

        # Function
        arguments = get_arguments(frame, objects, set())

        function_frame = FunctionFrame(
            name=frame.f_code.co_name,
            return_value=UNSET,
            arguments=arguments,
            bindings={
                name: capture_value(value, objects, set())
                for name, value in frame.f_locals.items()
                if name not in arguments
            }
        )

        snapshot.function_frames.append(function_frame)

    return snapshot

def capture_value(value, objects, capturing) -> Value:
    if isinstance(value, (int, str, bool, float)) or value is None:
        return value

    object_id = ObjectID(id(value))

    if object_id in objects:
        return object_id

    if object_id in capturing:
        return object_id

    capturing.add(object_id)

    objects[object_id] = capture_object(value, objects, capturing)

    capturing.remove(object_id)

    return object_id


def capture_object(value, objects, capturing) -> Object:
    # Lists, tuples, sets
    if isinstance(value, (list, tuple, set)):
        return SequenceObject(
            type=type(value).__name__,
            value=[
                capture_value(item, objects, capturing)
                for item in value
            ]
        )

    # Dicts
    if isinstance(value, dict):
        return MappedObject(
            type=type(value).__name__,
            value={
                capture_value(key, objects, capturing):
                capture_value(item, objects, capturing)
                for key, item in value.items()
            }
        )

    # Classes
    if isinstance(value, type):
        return MappedObject(
            type=value.__name__,
            value={
                capture_value(name, objects, capturing):
                capture_value(member, objects, capturing)
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
            value={
                capture_value(name, objects, capturing):
                capture_value(member, objects, capturing)
                for name, member in vars(value).items()
            }
        )

    return UnsupportedObject(
        type(value).__name__,
    )

def get_arguments(frame, objects, capturing):
    code = frame.f_code

    argument_names = (
        list(code.co_varnames[:code.co_argcount])

        + list(code.co_varnames[
            code.co_argcount:
            code.co_argcount + code.co_kwonlyargcount
        ])
    )

    return {
        name: capture_value(frame.f_locals[name], objects, capturing)
        for name in argument_names
        if name in frame.f_locals
    }