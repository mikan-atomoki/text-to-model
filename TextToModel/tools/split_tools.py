"""Split tools (body split, face split) for Fusion 360."""

from utils.geometry import get_body_by_name, get_plane, parse_entity_ref


def register(registry):
    """Register all split tools."""

    registry.register(
        name="split_body",
        description=(
            "Split a body using a construction plane, surface body, or face as the splitting tool. "
            "Results in two or more bodies."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {
                    "type": "string",
                    "description": "Name of the body to split.",
                },
                "splitting_tool": {
                    "type": "string",
                    "description": (
                        "Splitting tool reference: 'plane:XY', 'plane:XZ', 'plane:YZ', "
                        "'face:{body_name}:{face_index}', or a surface body name."
                    ),
                },
            },
            "required": ["body_name", "splitting_tool"],
        },
        handler=split_body,
    )

    registry.register(
        name="split_face",
        description="Split a face on a body using a construction plane or another face.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {
                    "type": "string",
                    "description": "Name of the body containing the face.",
                },
                "face_index": {
                    "type": "integer",
                    "description": "Index of the face to split.",
                },
                "splitting_tool": {
                    "type": "string",
                    "description": (
                        "Splitting tool reference: 'plane:XY', 'plane:XZ', 'plane:YZ', "
                        "or 'face:{body_name}:{face_index}'."
                    ),
                },
            },
            "required": ["body_name", "face_index", "splitting_tool"],
        },
        handler=split_face,
    )


def _resolve_splitting_tool(app, ref_string):
    """Resolve a splitting tool reference to a Fusion object.

    Accepts 'plane:XY', 'face:body:idx', or a body name (for surface body).
    """
    if ":" in ref_string:
        return parse_entity_ref(app, ref_string)
    else:
        body = get_body_by_name(app, ref_string)
        if not body:
            raise ValueError("Splitting tool body '{}' not found.".format(ref_string))
        return body


def split_body(app, body_name, splitting_tool, **kwargs):
    """Split a body with a plane, face, or surface body."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body = get_body_by_name(app, body_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    tool_entity = _resolve_splitting_tool(app, splitting_tool)

    splits = root.features.splitBodyFeatures
    split_input = splits.createInput(body, tool_entity, True)

    feature = splits.add(split_input)
    result_count = feature.bodies.count
    return "Split '{}' with {} -> {} resulting bodies, feature '{}'".format(
        body_name, splitting_tool, result_count, feature.name)


def split_face(app, body_name, face_index, splitting_tool, **kwargs):
    """Split a face on a body."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body = get_body_by_name(app, body_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    if face_index < 0 or face_index >= body.faces.count:
        raise ValueError("Face index {} out of range (0-{})".format(
            face_index, body.faces.count - 1))
    face = body.faces.item(face_index)

    tool_entity = _resolve_splitting_tool(app, splitting_tool)

    face_collection = adsk.core.ObjectCollection.create()
    face_collection.add(face)

    splits = root.features.splitFaceFeatures
    split_input = splits.createInput(face_collection, tool_entity, True)

    feature = splits.add(split_input)
    return "Split face {} on '{}' with {} -> '{}'".format(
        face_index, body_name, splitting_tool, feature.name)
