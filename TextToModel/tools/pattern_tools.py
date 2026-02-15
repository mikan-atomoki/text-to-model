"""Pattern and combine tools for Fusion 360."""

import math
from utils.geometry import mm_to_cm, get_body_by_name, deg_to_rad


def register(registry):
    """Register all pattern tools."""

    registry.register(
        name="circular_pattern",
        description="Create a circular pattern of bodies around an axis.",
        input_schema={
            "type": "object",
            "properties": {
                "body_names": {
                    "type": "array",
                    "description": "Array of body names to pattern.",
                    "items": {"type": "string"},
                },
                "axis": {
                    "type": "string",
                    "description": "Pattern axis: 'X', 'Y', or 'Z'.",
                    "enum": ["X", "Y", "Z"],
                },
                "count": {
                    "type": "integer",
                    "description": "Number of instances (including original).",
                },
                "angle": {
                    "type": "number",
                    "description": "Total angle in degrees. Use 360 for full circle.",
                    "default": 360,
                },
            },
            "required": ["body_names", "axis", "count"],
        },
        handler=circular_pattern,
    )

    registry.register(
        name="rectangular_pattern",
        description="Create a rectangular pattern of bodies along one or two directions.",
        input_schema={
            "type": "object",
            "properties": {
                "body_names": {
                    "type": "array",
                    "description": "Array of body names to pattern.",
                    "items": {"type": "string"},
                },
                "direction1_axis": {
                    "type": "string",
                    "description": "First direction axis: 'X', 'Y', or 'Z'.",
                    "enum": ["X", "Y", "Z"],
                },
                "count1": {
                    "type": "integer",
                    "description": "Number of instances in direction 1.",
                },
                "spacing1": {
                    "type": "number",
                    "description": "Spacing in direction 1 in mm.",
                },
                "direction2_axis": {
                    "type": "string",
                    "description": "Second direction axis (optional).",
                    "enum": ["X", "Y", "Z"],
                },
                "count2": {
                    "type": "integer",
                    "description": "Number of instances in direction 2.",
                    "default": 1,
                },
                "spacing2": {
                    "type": "number",
                    "description": "Spacing in direction 2 in mm.",
                    "default": 0,
                },
            },
            "required": ["body_names", "direction1_axis", "count1", "spacing1"],
        },
        handler=rectangular_pattern,
    )

    registry.register(
        name="combine",
        description="Combine multiple bodies using boolean operations (join, cut, intersect).",
        input_schema={
            "type": "object",
            "properties": {
                "target_body": {
                    "type": "string",
                    "description": "Name of the target (base) body.",
                },
                "tool_bodies": {
                    "type": "array",
                    "description": "Names of the tool bodies to combine with target.",
                    "items": {"type": "string"},
                },
                "operation": {
                    "type": "string",
                    "description": "Boolean operation: 'join', 'cut', 'intersect'.",
                    "enum": ["join", "cut", "intersect"],
                },
                "keep_tools": {
                    "type": "boolean",
                    "description": "Whether to keep the tool bodies after combining.",
                    "default": False,
                },
            },
            "required": ["target_body", "tool_bodies", "operation"],
        },
        handler=combine,
    )


def _get_axis(root, axis_name):
    """Get a construction axis by name."""
    axis_map = {
        "X": root.xConstructionAxis,
        "Y": root.yConstructionAxis,
        "Z": root.zConstructionAxis,
    }
    axis = axis_map.get(axis_name.upper())
    if axis is None:
        raise ValueError("Unknown axis: {}. Use X, Y, or Z.".format(axis_name))
    return axis


def circular_pattern(app, body_names, axis, count, angle=360, **kwargs):
    """Create a circular pattern of bodies."""
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

    axis_obj = _get_axis(root, axis)

    patterns = root.features.circularPatternFeatures
    pattern_input = patterns.createInput(body_collection, axis_obj)
    pattern_input.quantity = adsk.core.ValueInput.createByReal(count)
    pattern_input.totalAngle = adsk.core.ValueInput.createByReal(deg_to_rad(angle))
    pattern_input.isSymmetric = False

    feature = patterns.add(pattern_input)
    return "Circular pattern: {} bodies x{} around {} ({}deg) -> '{}'".format(
        len(body_names), count, axis, angle, feature.name)


def rectangular_pattern(app, body_names, direction1_axis, count1, spacing1,
                         direction2_axis=None, count2=1, spacing2=0, **kwargs):
    """Create a rectangular pattern of bodies."""
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

    axis1 = _get_axis(root, direction1_axis)

    patterns = root.features.rectangularPatternFeatures
    pattern_input = patterns.createInput(body_collection, axis1,
        adsk.core.ValueInput.createByReal(count1),
        adsk.core.ValueInput.createByReal(mm_to_cm(spacing1)),
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
    )

    if direction2_axis and count2 > 1:
        axis2 = _get_axis(root, direction2_axis)
        pattern_input.setDirectionTwo(
            axis2,
            adsk.core.ValueInput.createByReal(count2),
            adsk.core.ValueInput.createByReal(mm_to_cm(spacing2)),
        )

    feature = patterns.add(pattern_input)
    result = "Rectangular pattern: {} bodies x{} along {}".format(
        len(body_names), count1, direction1_axis)
    if direction2_axis and count2 > 1:
        result += " x{} along {}".format(count2, direction2_axis)
    result += " -> '{}'".format(feature.name)
    return result


def combine(app, target_body, tool_bodies, operation, keep_tools=False, **kwargs):
    """Combine bodies with boolean operations."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    target = get_body_by_name(app, target_body)
    if not target:
        raise ValueError("Target body '{}' not found.".format(target_body))

    tool_collection = adsk.core.ObjectCollection.create()
    for name in tool_bodies:
        body = get_body_by_name(app, name)
        if not body:
            raise ValueError("Tool body '{}' not found.".format(name))
        tool_collection.add(body)

    combines = root.features.combineFeatures

    op_map = {
        "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
        "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation,
    }
    operation_enum = op_map.get(operation)
    if operation_enum is None:
        raise ValueError("Unknown operation: {}".format(operation))

    combine_input = combines.createInput(target, tool_collection)
    combine_input.operation = operation_enum
    combine_input.isKeepToolBodies = keep_tools

    feature = combines.add(combine_input)
    return "Combined '{}' with {} bodies ({}) -> '{}'".format(
        target_body, len(tool_bodies), operation, feature.name)
