"""Modification tools (fillet, chamfer, shell, mirror) for Fusion 360."""

from utils.geometry import mm_to_cm, get_body_by_name


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
        description="Shell a body to make it hollow, removing selected faces.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {"type": "string", "description": "Name of the body."},
                "face_indices": {
                    "type": "array",
                    "description": "Array of face indices to remove (open faces).",
                    "items": {"type": "integer"},
                },
                "thickness": {"type": "number", "description": "Wall thickness in mm."},
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


def shell(app, body_name, face_indices, thickness, direction="inside", **kwargs):
    """Shell a body to make it hollow."""
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

    feature = shells.add(shell_input)
    return "Shelled '{}' with {}mm thickness ({}) -> '{}'".format(
        body_name, thickness, direction, feature.name)


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
