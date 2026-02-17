"""Modification tools (fillet, chamfer, shell, mirror, variable_fillet, draft) for Fusion 360."""

from utils.geometry import mm_to_cm, deg_to_rad, get_body_by_name


def register(registry):
    """Register all modify tools."""

    registry.register(
        name="fillet",
        description="Apply a fillet (rounded edge) to one or more edges of a body.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {"type": "string", "description": "Name of the body."},
                "edge_indices": {
                    "type": "array",
                    "description": "Array of edge indices to fillet.",
                    "items": {"type": "integer"},
                },
                "radius": {"type": "number", "description": "Fillet radius in mm."},
            },
            "required": ["body_name", "edge_indices", "radius"],
        },
        handler=fillet,
    )

    registry.register(
        name="chamfer",
        description="Apply a chamfer to one or more edges of a body.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {"type": "string", "description": "Name of the body."},
                "edge_indices": {
                    "type": "array",
                    "description": "Array of edge indices to chamfer.",
                    "items": {"type": "integer"},
                },
                "distance": {"type": "number", "description": "Chamfer distance in mm."},
            },
            "required": ["body_name", "edge_indices", "distance"],
        },
        handler=chamfer,
    )

    registry.register(
        name="shell",
        description="Shell a body to make it hollow, removing selected faces. Supports inside/outside thickness.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {"type": "string", "description": "Name of the body."},
                "face_indices": {
                    "type": "array",
                    "description": "Array of face indices to remove (open faces).",
                    "items": {"type": "integer"},
                },
                "thickness": {"type": "number", "description": "Wall thickness in mm (inside direction)."},
                "outside_thickness": {
                    "type": "number",
                    "description": "Outside wall thickness in mm. If specified, shell grows outward by this amount.",
                },
                "direction": {
                    "type": "string",
                    "description": "Shell direction: 'inside' or 'outside'.",
                    "enum": ["inside", "outside"],
                    "default": "inside",
                },
            },
            "required": ["body_name", "face_indices", "thickness"],
        },
        handler=shell,
    )

    registry.register(
        name="mirror",
        description="Mirror bodies or features across a construction plane.",
        input_schema={
            "type": "object",
            "properties": {
                "body_names": {
                    "type": "array",
                    "description": "Array of body names to mirror.",
                    "items": {"type": "string"},
                },
                "plane": {
                    "type": "string",
                    "description": "Mirror plane: 'XY', 'XZ', or 'YZ'.",
                    "enum": ["XY", "XZ", "YZ"],
                },
                "operation": {
                    "type": "string",
                    "description": "Boolean operation: 'new_body' or 'join'.",
                    "enum": ["new_body", "join"],
                    "default": "new_body",
                },
            },
            "required": ["body_names", "plane"],
        },
        handler=mirror,
    )

    registry.register(
        name="variable_fillet",
        description="Apply a variable-radius fillet to an edge, with different radii at start and end.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {"type": "string", "description": "Name of the body."},
                "edge_index": {"type": "integer", "description": "Index of the edge to fillet."},
                "start_radius": {"type": "number", "description": "Fillet radius at start vertex in mm."},
                "end_radius": {"type": "number", "description": "Fillet radius at end vertex in mm."},
                "mid_points": {
                    "type": "array",
                    "description": "Optional array of {position, radius} for intermediate control points. Position is 0.0-1.0 along edge.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "position": {"type": "number", "description": "Parameter position (0.0-1.0) along edge."},
                            "radius": {"type": "number", "description": "Radius at this position in mm."},
                        },
                        "required": ["position", "radius"],
                    },
                },
            },
            "required": ["body_name", "edge_index", "start_radius", "end_radius"],
        },
        handler=variable_fillet,
    )

    registry.register(
        name="draft",
        description="Apply a draft (taper) angle to faces of a body, typically for injection molding.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {"type": "string", "description": "Name of the body."},
                "face_indices": {
                    "type": "array",
                    "description": "Array of face indices to apply draft to.",
                    "items": {"type": "integer"},
                },
                "plane": {
                    "type": "string",
                    "description": "Pull direction plane: 'XY', 'XZ', or 'YZ'.",
                    "enum": ["XY", "XZ", "YZ"],
                },
                "angle": {
                    "type": "number",
                    "description": "Draft angle in degrees.",
                },
            },
            "required": ["body_name", "face_indices", "plane", "angle"],
        },
        handler=draft,
    )


def fillet(app, body_name, edge_indices, radius, **kwargs):
    """Apply fillet to edges."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body = get_body_by_name(app, body_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    fillets = root.features.filletFeatures
    edge_collection = adsk.core.ObjectCollection.create()

    for idx in edge_indices:
        if idx < 0 or idx >= body.edges.count:
            raise ValueError("Edge index {} out of range (0-{})".format(idx, body.edges.count - 1))
        edge_collection.add(body.edges.item(idx))

    fillet_input = fillets.createInput()
    fillet_input.addConstantRadiusEdgeSet(
        edge_collection,
        adsk.core.ValueInput.createByReal(mm_to_cm(radius)),
        True,
    )

    feature = fillets.add(fillet_input)
    return "Filleted {} edges on '{}' with radius {}mm -> '{}'".format(
        len(edge_indices), body_name, radius, feature.name)


def chamfer(app, body_name, edge_indices, distance, **kwargs):
    """Apply chamfer to edges."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body = get_body_by_name(app, body_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    chamfers = root.features.chamferFeatures
    edge_collection = adsk.core.ObjectCollection.create()

    for idx in edge_indices:
        if idx < 0 or idx >= body.edges.count:
            raise ValueError("Edge index {} out of range (0-{})".format(idx, body.edges.count - 1))
        edge_collection.add(body.edges.item(idx))

    chamfer_input = chamfers.createInput(
        edge_collection,
        True,
    )
    chamfer_input.setToEqualDistance(
        adsk.core.ValueInput.createByReal(mm_to_cm(distance))
    )

    feature = chamfers.add(chamfer_input)
    return "Chamfered {} edges on '{}' by {}mm -> '{}'".format(
        len(edge_indices), body_name, distance, feature.name)


def shell(app, body_name, face_indices, thickness, outside_thickness=None,
          direction="inside", **kwargs):
    """Shell a body to make it hollow. Supports inside and outside thickness."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body = get_body_by_name(app, body_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    shells = root.features.shellFeatures
    face_collection = adsk.core.ObjectCollection.create()

    for idx in face_indices:
        if idx < 0 or idx >= body.faces.count:
            raise ValueError("Face index {} out of range (0-{})".format(idx, body.faces.count - 1))
        face_collection.add(body.faces.item(idx))

    shell_input = shells.createInput(face_collection, direction == "inside")
    shell_input.insideThickness = adsk.core.ValueInput.createByReal(mm_to_cm(thickness))

    if outside_thickness is not None:
        shell_input.outsideThickness = adsk.core.ValueInput.createByReal(mm_to_cm(outside_thickness))

    feature = shells.add(shell_input)
    desc = "{}mm inside".format(thickness)
    if outside_thickness is not None:
        desc += ", {}mm outside".format(outside_thickness)
    return "Shelled '{}' ({}) -> '{}'".format(body_name, desc, feature.name)


def mirror(app, body_names, plane, operation="new_body", **kwargs):
    """Mirror bodies across a plane."""
    import adsk.core
    import adsk.fusion
    from utils.geometry import get_plane

    design = app.activeProduct
    root = design.rootComponent

    body_collection = adsk.core.ObjectCollection.create()
    for name in body_names:
        body = get_body_by_name(app, name)
        if not body:
            raise ValueError("Body '{}' not found.".format(name))
        body_collection.add(body)

    plane_obj = get_plane(app, plane)

    mirrors = root.features.mirrorFeatures
    mirror_input = mirrors.createInput(body_collection, plane_obj)

    if operation == "join":
        mirror_input.patternComputeOption = adsk.fusion.PatternComputeOptions.IdenticalCompute
    else:
        mirror_input.patternComputeOption = adsk.fusion.PatternComputeOptions.IdenticalCompute

    feature = mirrors.add(mirror_input)
    return "Mirrored {} bodies across {} -> '{}'".format(
        len(body_names), plane, feature.name)


def variable_fillet(app, body_name, edge_index, start_radius, end_radius,
                     mid_points=None, **kwargs):
    """Apply a variable-radius fillet to an edge."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body = get_body_by_name(app, body_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    if edge_index < 0 or edge_index >= body.edges.count:
        raise ValueError("Edge index {} out of range (0-{})".format(
            edge_index, body.edges.count - 1))
    edge = body.edges.item(edge_index)

    fillets = root.features.filletFeatures
    fillet_input = fillets.createInput()

    edge_collection = adsk.core.ObjectCollection.create()
    edge_collection.add(edge)

    start_val = adsk.core.ValueInput.createByReal(mm_to_cm(start_radius))
    end_val = adsk.core.ValueInput.createByReal(mm_to_cm(end_radius))

    var_set = fillet_input.addVariableRadiusEdgeSet(
        edge_collection, start_val, end_val, True)

    if mid_points:
        for mp in mid_points:
            pos = mp["position"]
            rad = adsk.core.ValueInput.createByReal(mm_to_cm(mp["radius"]))
            var_set.addRadiusAtParameter(pos, rad)

    feature = fillets.add(fillet_input)
    mid_desc = ""
    if mid_points:
        mid_desc = " with {} mid-points".format(len(mid_points))
    return "Variable fillet on '{}' edge {} ({}mm -> {}mm{}) -> '{}'".format(
        body_name, edge_index, start_radius, end_radius, mid_desc, feature.name)


def draft(app, body_name, face_indices, plane, angle, **kwargs):
    """Apply draft angle to faces."""
    import adsk.core
    import adsk.fusion
    from utils.geometry import get_plane

    design = app.activeProduct
    root = design.rootComponent

    body = get_body_by_name(app, body_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    plane_obj = get_plane(app, plane)

    drafts = root.features.draftFeatures

    face_collection = adsk.core.ObjectCollection.create()
    for idx in face_indices:
        if idx < 0 or idx >= body.faces.count:
            raise ValueError("Face index {} out of range (0-{})".format(
                idx, body.faces.count - 1))
        face_collection.add(body.faces.item(idx))

    draft_input = drafts.createInput(
        face_collection, plane_obj,
        adsk.core.ValueInput.createByReal(deg_to_rad(angle)),
        False,
    )

    feature = drafts.add(draft_input)
    return "Draft {}deg on {} faces of '{}' (plane: {}) -> '{}'".format(
        angle, len(face_indices), body_name, plane, feature.name)
