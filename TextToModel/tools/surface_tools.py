"""Surface modeling tools (patch, thicken, offset, boundary fill) for Fusion 360."""

from utils.geometry import mm_to_cm, get_body_by_name


def register(registry):
    """Register all surface tools."""

    registry.register(
        name="patch_surface",
        description=(
            "Create a surface patch from boundary edges of an open body or selected edges. "
            "Useful for closing open surfaces or creating complex surface shapes."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {
                    "type": "string",
                    "description": "Name of the body whose boundary edges to patch.",
                },
                "edge_indices": {
                    "type": "array",
                    "description": "Array of edge indices forming a closed boundary loop. If omitted, uses all boundary edges.",
                    "items": {"type": "integer"},
                },
                "continuity": {
                    "type": "string",
                    "description": "Surface continuity: 'connected' (G0), 'tangent' (G1), or 'curvature' (G2).",
                    "enum": ["connected", "tangent", "curvature"],
                    "default": "connected",
                },
                "operation": {
                    "type": "string",
                    "description": "Boolean operation: 'new_body', 'join'.",
                    "enum": ["new_body", "join"],
                    "default": "new_body",
                },
            },
            "required": ["body_name"],
        },
        handler=patch_surface,
    )

    registry.register(
        name="thicken_surface",
        description="Thicken a surface body into a solid body by adding thickness.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {
                    "type": "string",
                    "description": "Name of the surface body to thicken.",
                },
                "thickness": {
                    "type": "number",
                    "description": "Thickness in mm.",
                },
                "direction": {
                    "type": "string",
                    "description": "Thicken direction: 'symmetric', 'positive', 'negative'.",
                    "enum": ["symmetric", "positive", "negative"],
                    "default": "symmetric",
                },
                "operation": {
                    "type": "string",
                    "description": "Boolean operation: 'new_body', 'join'.",
                    "enum": ["new_body", "join"],
                    "default": "new_body",
                },
            },
            "required": ["body_name", "thickness"],
        },
        handler=thicken_surface,
    )

    registry.register(
        name="offset_surface",
        description="Create an offset copy of one or more faces.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {
                    "type": "string",
                    "description": "Name of the body containing the faces.",
                },
                "face_indices": {
                    "type": "array",
                    "description": "Array of face indices to offset.",
                    "items": {"type": "integer"},
                },
                "offset": {
                    "type": "number",
                    "description": "Offset distance in mm.",
                },
                "operation": {
                    "type": "string",
                    "description": "Boolean operation: 'new_body', 'join'.",
                    "enum": ["new_body", "join"],
                    "default": "new_body",
                },
            },
            "required": ["body_name", "face_indices", "offset"],
        },
        handler=offset_surface,
    )

    registry.register(
        name="boundary_fill",
        description=(
            "Fill a closed volume defined by surfaces/planes with a solid body. "
            "Select the cells (volumes) to keep."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool_bodies": {
                    "type": "array",
                    "description": "Array of body names that form the boundary.",
                    "items": {"type": "string"},
                },
                "cell_index": {
                    "type": "integer",
                    "description": "Index of the cell (volume) to keep (0-based). Default 0.",
                    "default": 0,
                },
                "operation": {
                    "type": "string",
                    "description": "Boolean operation: 'new_body', 'join'.",
                    "enum": ["new_body", "join"],
                    "default": "new_body",
                },
            },
            "required": ["tool_bodies"],
        },
        handler=boundary_fill,
    )


def _get_operation(op_name):
    """Convert operation name to Fusion FeatureOperations enum."""
    import adsk.fusion
    ops = {
        "new_body": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
        "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation,
    }
    return ops.get(op_name, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)


def patch_surface(app, body_name, edge_indices=None, continuity="connected",
                   operation="new_body", **kwargs):
    """Create a surface patch from boundary edges."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body = get_body_by_name(app, body_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    patches = root.features.patchFeatures

    edge_collection = adsk.core.ObjectCollection.create()
    if edge_indices:
        for idx in edge_indices:
            if idx < 0 or idx >= body.edges.count:
                raise ValueError("Edge index {} out of range (0-{})".format(
                    idx, body.edges.count - 1))
            edge_collection.add(body.edges.item(idx))
    else:
        for i in range(body.edges.count):
            edge_collection.add(body.edges.item(i))

    patch_input = patches.createInput(edge_collection, _get_operation(operation))

    continuity_map = {
        "connected": adsk.fusion.SurfaceContinuityTypes.ConnectedSurfaceContinuityType,
        "tangent": adsk.fusion.SurfaceContinuityTypes.TangentSurfaceContinuityType,
        "curvature": adsk.fusion.SurfaceContinuityTypes.CurvatureSurfaceContinuityType,
    }
    patch_input.continuity = continuity_map.get(
        continuity, adsk.fusion.SurfaceContinuityTypes.ConnectedSurfaceContinuityType)

    feature = patches.add(patch_input)
    return "Created patch surface from '{}' ({} edges, {}) -> '{}'".format(
        body_name, edge_collection.count, continuity, feature.name)


def thicken_surface(app, body_name, thickness, direction="symmetric",
                     operation="new_body", **kwargs):
    """Thicken a surface body into a solid."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body = get_body_by_name(app, body_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    thickens = root.features.thickenFeatures

    face_collection = adsk.core.ObjectCollection.create()
    for i in range(body.faces.count):
        face_collection.add(body.faces.item(i))

    thickness_val = adsk.core.ValueInput.createByReal(mm_to_cm(thickness))
    thicken_input = thickens.createInput(
        face_collection, thickness_val, direction == "symmetric",
        _get_operation(operation),
    )

    if direction == "negative":
        thicken_input.isFlipped = True

    feature = thickens.add(thicken_input)
    return "Thickened '{}' by {}mm ({}) -> '{}'".format(
        body_name, thickness, direction, feature.name)


def offset_surface(app, body_name, face_indices, offset, operation="new_body", **kwargs):
    """Create an offset copy of faces."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    body = get_body_by_name(app, body_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    offsets = root.features.offsetFeatures

    face_collection = adsk.core.ObjectCollection.create()
    for idx in face_indices:
        if idx < 0 or idx >= body.faces.count:
            raise ValueError("Face index {} out of range (0-{})".format(
                idx, body.faces.count - 1))
        face_collection.add(body.faces.item(idx))

    offset_val = adsk.core.ValueInput.createByReal(mm_to_cm(offset))
    offset_input = offsets.createInput(
        face_collection, offset_val, _get_operation(operation),
    )

    feature = offsets.add(offset_input)
    return "Offset {} faces on '{}' by {}mm -> '{}'".format(
        len(face_indices), body_name, offset, feature.name)


def boundary_fill(app, tool_bodies, cell_index=0, operation="new_body", **kwargs):
    """Fill a closed volume defined by boundary surfaces."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    fills = root.features.boundaryFillFeatures

    body_collection = adsk.core.ObjectCollection.create()
    for name in tool_bodies:
        body = get_body_by_name(app, name)
        if not body:
            raise ValueError("Body '{}' not found.".format(name))
        body_collection.add(body)

    fill_input = fills.createInput(body_collection, _get_operation(operation))

    cells = fill_input.bRepCells
    if cell_index < 0 or cell_index >= cells.count:
        raise ValueError("Cell index {} out of range (0-{})".format(
            cell_index, cells.count - 1))
    cells.item(cell_index).isSelected = True

    feature = fills.add(fill_input)
    return "Boundary fill from {} bodies (cell {}) -> '{}'".format(
        len(tool_bodies), cell_index, feature.name)
