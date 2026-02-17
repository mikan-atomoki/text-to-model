"""Transform tools (move, scale, copy) for Fusion 360."""

from utils.geometry import mm_to_cm, deg_to_rad, get_body_by_name, vector3d, point3d


def register(registry):
    """Register all transform tools."""

    registry.register(
        name="move_body",
        description="Move or rotate one or more bodies. Translate by XYZ offset or rotate around an axis.",
        input_schema={
            "type": "object",
            "properties": {
                "body_names": {
                    "type": "array",
                    "description": "Array of body names to move.",
                    "items": {"type": "string"},
                },
                "mode": {
                    "type": "string",
                    "description": "Transform mode: 'translate' or 'rotate'.",
                    "enum": ["translate", "rotate"],
                },
                "x": {
                    "type": "number",
                    "description": "Translation X in mm (translate mode).",
                    "default": 0,
                },
                "y": {
                    "type": "number",
                    "description": "Translation Y in mm (translate mode).",
                    "default": 0,
                },
                "z": {
                    "type": "number",
                    "description": "Translation Z in mm (translate mode).",
                    "default": 0,
                },
                "axis": {
                    "type": "string",
                    "description": "Rotation axis: 'X', 'Y', or 'Z' (rotate mode).",
                    "enum": ["X", "Y", "Z"],
                },
                "angle": {
                    "type": "number",
                    "description": "Rotation angle in degrees (rotate mode).",
                },
                "create_copy": {
                    "type": "boolean",
                    "description": "If true, create a moved copy instead of moving the original.",
                    "default": False,
                },
            },
            "required": ["body_names", "mode"],
        },
        handler=move_body,
    )

    registry.register(
        name="scale_body",
        description="Scale one or more bodies uniformly or non-uniformly.",
        input_schema={
            "type": "object",
            "properties": {
                "body_names": {
                    "type": "array",
                    "description": "Array of body names to scale.",
                    "items": {"type": "string"},
                },
                "scale_factor": {
                    "type": "number",
                    "description": "Uniform scale factor (e.g. 2.0 = double size). Overridden by scale_x/y/z if provided.",
                },
                "scale_x": {
                    "type": "number",
                    "description": "X scale factor (non-uniform scaling).",
                },
                "scale_y": {
                    "type": "number",
                    "description": "Y scale factor (non-uniform scaling).",
                },
                "scale_z": {
                    "type": "number",
                    "description": "Z scale factor (non-uniform scaling).",
                },
                "base_point": {
                    "type": "object",
                    "description": "Base point {x, y, z} in mm for scaling origin. Default is body centroid.",
                    "properties": {
                        "x": {"type": "number", "default": 0},
                        "y": {"type": "number", "default": 0},
                        "z": {"type": "number", "default": 0},
                    },
                },
            },
            "required": ["body_names"],
        },
        handler=scale_body,
    )

    registry.register(
        name="copy_body",
        description="Create a copy of a body, optionally into a different component.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {
                    "type": "string",
                    "description": "Name of the body to copy.",
                },
                "target_component": {
                    "type": "string",
                    "description": "Optional target component name. Copies within the same component if not specified.",
                },
            },
            "required": ["body_name"],
        },
        handler=copy_body,
    )


def move_body(app, body_names, mode, x=0, y=0, z=0, axis=None, angle=None,
              create_copy=False, **kwargs):
    """Move or rotate bodies."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body_collection = adsk.core.ObjectCollection.create()
    for name in body_names:
        body = get_body_by_name(app, name)
        if not body:
            raise ValueError("Body '{}' not found.".format(name))
        body_collection.add(body)

    moves = root.features.moveFeatures
    move_input = moves.createInput2(body_collection)

    if mode == "translate":
        transform = adsk.core.Matrix3D.create()
        transform.translation = adsk.core.Vector3D.create(
            mm_to_cm(x), mm_to_cm(y), mm_to_cm(z))
        move_input.defineAsFreeMove(transform)
    elif mode == "rotate":
        if not axis or angle is None:
            raise ValueError("Rotate mode requires 'axis' and 'angle'.")
        axis_map = {
            "X": adsk.core.Vector3D.create(1, 0, 0),
            "Y": adsk.core.Vector3D.create(0, 1, 0),
            "Z": adsk.core.Vector3D.create(0, 0, 1),
        }
        axis_vec = axis_map.get(axis.upper())
        if not axis_vec:
            raise ValueError("Unknown axis: {}. Use X, Y, or Z.".format(axis))
        origin = adsk.core.Point3D.create(0, 0, 0)
        transform = adsk.core.Matrix3D.create()
        transform.setToRotation(deg_to_rad(angle), axis_vec, origin)
        move_input.defineAsFreeMove(transform)
    else:
        raise ValueError("Unknown mode: {}. Use 'translate' or 'rotate'.".format(mode))

    if create_copy:
        move_input.isCopy = True

    feature = moves.add(move_input)

    if mode == "translate":
        return "Moved {} bodies by ({}, {}, {})mm{} -> '{}'".format(
            len(body_names), x, y, z,
            " (copy)" if create_copy else "", feature.name)
    else:
        return "Rotated {} bodies {}deg around {}{} -> '{}'".format(
            len(body_names), angle, axis,
            " (copy)" if create_copy else "", feature.name)


def scale_body(app, body_names, scale_factor=None, scale_x=None, scale_y=None,
               scale_z=None, base_point=None, **kwargs):
    """Scale bodies uniformly or non-uniformly."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body_collection = adsk.core.ObjectCollection.create()
    for name in body_names:
        body = get_body_by_name(app, name)
        if not body:
            raise ValueError("Body '{}' not found.".format(name))
        body_collection.add(body)

    scales = root.features.scaleFeatures

    if base_point:
        bp = point3d(base_point.get("x", 0), base_point.get("y", 0), base_point.get("z", 0))
    else:
        bp = adsk.core.Point3D.create(0, 0, 0)

    base_pt_input = adsk.fusion.UniformScaleDefinition if scale_factor else None

    if scale_x is not None or scale_y is not None or scale_z is not None:
        sx = scale_x if scale_x is not None else (scale_factor if scale_factor else 1.0)
        sy = scale_y if scale_y is not None else (scale_factor if scale_factor else 1.0)
        sz = scale_z if scale_z is not None else (scale_factor if scale_factor else 1.0)

        scale_input = scales.createInput(body_collection, bp, False)
        scale_input.setToNonUniform(
            adsk.core.ValueInput.createByReal(sx),
            adsk.core.ValueInput.createByReal(sy),
            adsk.core.ValueInput.createByReal(sz),
        )
        desc = "non-uniform ({}, {}, {})".format(sx, sy, sz)
    else:
        if scale_factor is None:
            scale_factor = 1.0
        scale_input = scales.createInput(body_collection, bp, True)
        scale_input.scaleFactor = adsk.core.ValueInput.createByReal(scale_factor)
        desc = "uniform {}x".format(scale_factor)

    feature = scales.add(scale_input)
    return "Scaled {} bodies {} -> '{}'".format(len(body_names), desc, feature.name)


def copy_body(app, body_name, target_component=None, **kwargs):
    """Copy a body, optionally to another component."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body = get_body_by_name(app, body_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    if target_component:
        target_comp = None
        for occ in root.allOccurrences:
            if occ.component.name == target_component:
                target_comp = occ.component
                break
        if not target_comp:
            raise ValueError("Component '{}' not found.".format(target_component))
        new_body = body.copyToComponent(target_comp)
    else:
        body_collection = adsk.core.ObjectCollection.create()
        body_collection.add(body)

        copies = root.features.copyPasteBodies
        copy_input = copies.createInput(body_collection)
        feature = copies.add(copy_input)
        new_body = feature.bodies.item(0)

    return "Copied '{}' -> '{}'{}".format(
        body_name, new_body.name,
        " into '{}'".format(target_component) if target_component else "")
