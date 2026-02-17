"""Construction geometry tools (planes, axes) for Fusion 360."""

from utils.geometry import mm_to_cm, deg_to_rad, get_plane, get_body_by_name


def register(registry):
    """Register all construction geometry tools."""

    registry.register(
        name="create_offset_plane",
        description="Create a construction plane offset from an existing plane or planar face.",
        input_schema={
            "type": "object",
            "properties": {
                "base_plane": {
                    "type": "string",
                    "description": "Base plane: 'XY', 'XZ', 'YZ', or 'face:{body_name}:{face_index}' for a planar face.",
                },
                "offset": {
                    "type": "number",
                    "description": "Offset distance in mm. Positive = along normal direction.",
                },
                "component_name": {
                    "type": "string",
                    "description": "Optional component name. Uses root component if not specified.",
                },
            },
            "required": ["base_plane", "offset"],
        },
        handler=create_offset_plane,
    )

    registry.register(
        name="create_angled_plane",
        description="Create a construction plane rotated around a line/axis from a base plane.",
        input_schema={
            "type": "object",
            "properties": {
                "base_plane": {
                    "type": "string",
                    "description": "Base plane: 'XY', 'XZ', or 'YZ'.",
                    "enum": ["XY", "XZ", "YZ"],
                },
                "axis": {
                    "type": "string",
                    "description": "Rotation axis: 'X', 'Y', 'Z', or 'edge:{body_name}:{edge_index}'.",
                },
                "angle": {
                    "type": "number",
                    "description": "Rotation angle in degrees.",
                },
                "component_name": {
                    "type": "string",
                    "description": "Optional component name. Uses root component if not specified.",
                },
            },
            "required": ["base_plane", "axis", "angle"],
        },
        handler=create_angled_plane,
    )

    registry.register(
        name="create_midplane",
        description="Create a construction plane midway between two parallel planes or faces.",
        input_schema={
            "type": "object",
            "properties": {
                "plane1": {
                    "type": "string",
                    "description": "First plane: 'XY', 'XZ', 'YZ', or 'face:{body_name}:{face_index}'.",
                },
                "plane2": {
                    "type": "string",
                    "description": "Second plane: 'XY', 'XZ', 'YZ', or 'face:{body_name}:{face_index}'.",
                },
                "component_name": {
                    "type": "string",
                    "description": "Optional component name. Uses root component if not specified.",
                },
            },
            "required": ["plane1", "plane2"],
        },
        handler=create_midplane,
    )

    registry.register(
        name="create_construction_axis",
        description="Create a construction axis from two points, an edge, or a face normal.",
        input_schema={
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": "Creation mode: 'two_points', 'edge', 'face_normal'.",
                    "enum": ["two_points", "edge", "face_normal"],
                },
                "point1": {
                    "type": "object",
                    "description": "First point {x, y, z} in mm (for 'two_points' mode).",
                    "properties": {
                        "x": {"type": "number", "default": 0},
                        "y": {"type": "number", "default": 0},
                        "z": {"type": "number", "default": 0},
                    },
                },
                "point2": {
                    "type": "object",
                    "description": "Second point {x, y, z} in mm (for 'two_points' mode).",
                    "properties": {
                        "x": {"type": "number", "default": 0},
                        "y": {"type": "number", "default": 0},
                        "z": {"type": "number", "default": 0},
                    },
                },
                "body_name": {
                    "type": "string",
                    "description": "Body name (for 'edge' or 'face_normal' mode).",
                },
                "edge_index": {
                    "type": "integer",
                    "description": "Edge index (for 'edge' mode).",
                },
                "face_index": {
                    "type": "integer",
                    "description": "Face index (for 'face_normal' mode).",
                },
                "component_name": {
                    "type": "string",
                    "description": "Optional component name. Uses root component if not specified.",
                },
            },
            "required": ["mode"],
        },
        handler=create_construction_axis,
    )


def _resolve_plane_or_face(app, ref_string):
    """Resolve a plane reference string to a ConstructionPlane or BRepFace.

    Accepts 'XY', 'XZ', 'YZ' or 'face:{body_name}:{face_index}'.
    """
    if ref_string.startswith("face:"):
        parts = ref_string.split(":")
        if len(parts) != 3:
            raise ValueError("Face reference must be 'face:body_name:face_index', got '{}'".format(ref_string))
        body_name = parts[1]
        face_index = int(parts[2])
        body = get_body_by_name(app, body_name)
        if not body:
            raise ValueError("Body '{}' not found.".format(body_name))
        if face_index < 0 or face_index >= body.faces.count:
            raise ValueError("Face index {} out of range (0-{})".format(
                face_index, body.faces.count - 1))
        return body.faces.item(face_index)
    else:
        return get_plane(app, ref_string)


def _get_target_component(app, component_name=None):
    """Get target component by name or return root."""
    design = app.activeProduct
    root = design.rootComponent
    if component_name:
        for occ in root.allOccurrences:
            if occ.component.name == component_name:
                return occ.component
    return root


def create_offset_plane(app, base_plane, offset, component_name=None, **kwargs):
    """Create a construction plane offset from a base plane or face."""
    import adsk.core
    import adsk.fusion

    comp = _get_target_component(app, component_name)
    base = _resolve_plane_or_face(app, base_plane)

    planes = comp.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByOffset(
        base,
        adsk.core.ValueInput.createByReal(mm_to_cm(offset)),
    )

    plane = planes.add(plane_input)
    idx = planes.count - 1
    return "Created offset plane '{}' at {}mm from {} (index: {})".format(
        plane.name, offset, base_plane, idx)


def create_angled_plane(app, base_plane, axis, angle, component_name=None, **kwargs):
    """Create a construction plane rotated from a base plane around an axis."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent
    comp = _get_target_component(app, component_name)

    base = get_plane(app, base_plane)

    if axis.startswith("edge:"):
        parts = axis.split(":")
        if len(parts) != 3:
            raise ValueError("Edge reference must be 'edge:body_name:edge_index', got '{}'".format(axis))
        body = get_body_by_name(app, parts[1])
        if not body:
            raise ValueError("Body '{}' not found.".format(parts[1]))
        edge_idx = int(parts[2])
        if edge_idx < 0 or edge_idx >= body.edges.count:
            raise ValueError("Edge index {} out of range (0-{})".format(
                edge_idx, body.edges.count - 1))
        axis_obj = body.edges.item(edge_idx)
    else:
        axis_map = {
            "X": root.xConstructionAxis,
            "Y": root.yConstructionAxis,
            "Z": root.zConstructionAxis,
        }
        axis_obj = axis_map.get(axis.upper())
        if axis_obj is None:
            raise ValueError("Unknown axis: {}. Use X, Y, Z, or 'edge:body:index'.".format(axis))

    planes = comp.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByAngle(
        axis_obj,
        adsk.core.ValueInput.createByReal(deg_to_rad(angle)),
        base,
    )

    plane = planes.add(plane_input)
    idx = planes.count - 1
    return "Created angled plane '{}' at {}deg from {} around {} (index: {})".format(
        plane.name, angle, base_plane, axis, idx)


def create_midplane(app, plane1, plane2, component_name=None, **kwargs):
    """Create a construction plane between two planes or faces."""
    import adsk.core
    import adsk.fusion

    comp = _get_target_component(app, component_name)
    p1 = _resolve_plane_or_face(app, plane1)
    p2 = _resolve_plane_or_face(app, plane2)

    planes = comp.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByTwoPlanes(p1, p2)

    plane = planes.add(plane_input)
    idx = planes.count - 1
    return "Created midplane '{}' between {} and {} (index: {})".format(
        plane.name, plane1, plane2, idx)


def create_construction_axis(app, mode, point1=None, point2=None,
                              body_name=None, edge_index=None, face_index=None,
                              component_name=None, **kwargs):
    """Create a construction axis."""
    import adsk.core
    import adsk.fusion
    from utils.geometry import point3d

    design = app.activeProduct
    comp = _get_target_component(app, component_name)
    axes = comp.constructionAxes

    axis_input = axes.createInput()

    if mode == "two_points":
        if not point1 or not point2:
            raise ValueError("'two_points' mode requires point1 and point2.")
        p1 = point3d(point1.get("x", 0), point1.get("y", 0), point1.get("z", 0))
        p2 = point3d(point2.get("x", 0), point2.get("y", 0), point2.get("z", 0))
        axis_input.setByTwoPoints(p1, p2)

    elif mode == "edge":
        if not body_name or edge_index is None:
            raise ValueError("'edge' mode requires body_name and edge_index.")
        body = get_body_by_name(app, body_name)
        if not body:
            raise ValueError("Body '{}' not found.".format(body_name))
        if edge_index < 0 or edge_index >= body.edges.count:
            raise ValueError("Edge index {} out of range (0-{})".format(
                edge_index, body.edges.count - 1))
        edge = body.edges.item(edge_index)
        axis_input.setByLine(edge)

    elif mode == "face_normal":
        if not body_name or face_index is None:
            raise ValueError("'face_normal' mode requires body_name and face_index.")
        body = get_body_by_name(app, body_name)
        if not body:
            raise ValueError("Body '{}' not found.".format(body_name))
        if face_index < 0 or face_index >= body.faces.count:
            raise ValueError("Face index {} out of range (0-{})".format(
                face_index, body.faces.count - 1))
        face = body.faces.item(face_index)
        axis_input.setByNormalToFaceAtPoint(face, face.pointOnFace)

    else:
        raise ValueError("Unknown mode: {}. Use 'two_points', 'edge', or 'face_normal'.".format(mode))

    axis = axes.add(axis_input)
    idx = axes.count - 1
    return "Created construction axis '{}' via {} (index: {})".format(axis.name, mode, idx)
