"""Feature creation tools (extrude, revolve, sweep, loft) for Fusion 360."""

import math
from utils.geometry import mm_to_cm, deg_to_rad


def register(registry):
    """Register all feature tools."""

    registry.register(
        name="extrude",
        description="Extrude a sketch profile to create a solid body. Supports symmetric, one-direction, or two-direction extrusion.",
        input_schema={
            "type": "object",
            "properties": {
                "sketch_index": {
                    "type": "integer",
                    "description": "Index of the sketch containing the profile (0-based). Uses last sketch if not specified.",
                },
                "profile_index": {
                    "type": "integer",
                    "description": "Index of the profile within the sketch (0-based). Uses first profile (0) if not specified.",
                    "default": 0,
                },
                "distance": {
                    "type": "number",
                    "description": "Extrusion distance in mm.",
                },
                "direction": {
                    "type": "string",
                    "description": "Extrusion direction: 'positive', 'negative', or 'symmetric'.",
                    "enum": ["positive", "negative", "symmetric"],
                    "default": "positive",
                },
                "operation": {
                    "type": "string",
                    "description": "Boolean operation: 'new_body', 'join', 'cut', 'intersect'.",
                    "enum": ["new_body", "join", "cut", "intersect"],
                    "default": "new_body",
                },
                "taper_angle": {
                    "type": "number",
                    "description": "Taper angle in degrees (0 = no taper).",
                    "default": 0,
                },
            },
            "required": ["distance"],
        },
        handler=extrude,
    )

    registry.register(
        name="revolve",
        description="Revolve a sketch profile around an axis to create a solid body.",
        input_schema={
            "type": "object",
            "properties": {
                "sketch_index": {
                    "type": "integer",
                    "description": "Index of the sketch (0-based). Uses last sketch if not specified.",
                },
                "profile_index": {
                    "type": "integer",
                    "description": "Index of the profile (0-based).",
                    "default": 0,
                },
                "axis": {
                    "type": "string",
                    "description": "Revolution axis: 'X', 'Y', 'Z', or a sketch line index like 'line:0'.",
                    "default": "X",
                },
                "angle": {
                    "type": "number",
                    "description": "Revolution angle in degrees. Use 360 for full revolution.",
                    "default": 360,
                },
                "operation": {
                    "type": "string",
                    "description": "Boolean operation: 'new_body', 'join', 'cut', 'intersect'.",
                    "enum": ["new_body", "join", "cut", "intersect"],
                    "default": "new_body",
                },
            },
            "required": [],
        },
        handler=revolve,
    )

    registry.register(
        name="sweep",
        description="Sweep a sketch profile along a path to create a solid body.",
        input_schema={
            "type": "object",
            "properties": {
                "profile_sketch_index": {
                    "type": "integer",
                    "description": "Index of the sketch containing the profile.",
                },
                "profile_index": {
                    "type": "integer",
                    "description": "Index of the profile (0-based).",
                    "default": 0,
                },
                "path_sketch_index": {
                    "type": "integer",
                    "description": "Index of the sketch containing the sweep path.",
                },
                "path_curve_index": {
                    "type": "integer",
                    "description": "Index of the curve in the path sketch to use as path.",
                    "default": 0,
                },
                "operation": {
                    "type": "string",
                    "description": "Boolean operation: 'new_body', 'join', 'cut', 'intersect'.",
                    "enum": ["new_body", "join", "cut", "intersect"],
                    "default": "new_body",
                },
            },
            "required": ["profile_sketch_index", "path_sketch_index"],
        },
        handler=sweep,
    )

    registry.register(
        name="loft",
        description="Create a loft between two or more sketch profiles.",
        input_schema={
            "type": "object",
            "properties": {
                "profiles": {
                    "type": "array",
                    "description": "Array of {sketch_index, profile_index} objects defining loft sections.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sketch_index": {"type": "integer"},
                            "profile_index": {"type": "integer", "default": 0},
                        },
                        "required": ["sketch_index"],
                    },
                    "minItems": 2,
                },
                "operation": {
                    "type": "string",
                    "description": "Boolean operation: 'new_body', 'join', 'cut', 'intersect'.",
                    "enum": ["new_body", "join", "cut", "intersect"],
                    "default": "new_body",
                },
            },
            "required": ["profiles"],
        },
        handler=loft,
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


def _get_sketch(app, sketch_index=None):
    """Get a sketch by index or the last one."""
    design = app.activeProduct
    sketches = design.rootComponent.sketches
    if sketches.count == 0:
        raise ValueError("No sketches exist. Create a sketch first.")
    if sketch_index is not None:
        if sketch_index < 0 or sketch_index >= sketches.count:
            raise ValueError("Sketch index {} out of range (0-{})".format(
                sketch_index, sketches.count - 1))
        return sketches.item(sketch_index)
    return sketches.item(sketches.count - 1)


def _get_profile(sketch, profile_index=0):
    """Get a profile from a sketch."""
    profiles = sketch.profiles
    if profiles.count == 0:
        raise ValueError("Sketch '{}' has no closed profiles.".format(sketch.name))
    if profile_index < 0 or profile_index >= profiles.count:
        raise ValueError("Profile index {} out of range (0-{})".format(
            profile_index, profiles.count - 1))
    return profiles.item(profile_index)


def extrude(app, distance, sketch_index=None, profile_index=0,
            direction="positive", operation="new_body", taper_angle=0, **kwargs):
    """Extrude a profile to create a 3D body."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    sketch = _get_sketch(app, sketch_index)
    profile = _get_profile(sketch, profile_index)

    extrudes = root.features.extrudeFeatures
    ext_input = extrudes.createInput(profile, _get_operation(operation))

    dist_cm = mm_to_cm(distance)
    dist_val = adsk.core.ValueInput.createByReal(dist_cm)

    if direction == "symmetric":
        ext_input.setSymmetricExtent(dist_val, True)
    elif direction == "negative":
        ext_input.setDistanceExtent(False, dist_val)
        ext_input.setDirectionFlip(True)
    else:
        ext_input.setDistanceExtent(False, dist_val)

    if taper_angle != 0:
        taper_val = adsk.core.ValueInput.createByReal(deg_to_rad(taper_angle))
        ext_input.taperAngle = taper_val

    feature = extrudes.add(ext_input)
    return "Extruded '{}' profile {} by {}mm ({}) -> '{}'".format(
        sketch.name, profile_index, distance, direction, feature.name)


def revolve(app, sketch_index=None, profile_index=0, axis="X",
            angle=360, operation="new_body", **kwargs):
    """Revolve a profile around an axis."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    sketch = _get_sketch(app, sketch_index)
    profile = _get_profile(sketch, profile_index)

    revolves = root.features.revolveFeatures

    if axis.startswith("line:"):
        line_idx = int(axis.split(":")[1])
        lines = sketch.sketchCurves.sketchLines
        if line_idx < 0 or line_idx >= lines.count:
            raise ValueError("Line index {} out of range".format(line_idx))
        axis_obj = lines.item(line_idx)
    else:
        axis_map = {
            "X": root.xConstructionAxis,
            "Y": root.yConstructionAxis,
            "Z": root.zConstructionAxis,
        }
        axis_obj = axis_map.get(axis.upper())
        if axis_obj is None:
            raise ValueError("Unknown axis: {}. Use X, Y, Z, or 'line:N'.".format(axis))

    rev_input = revolves.createInput(profile, axis_obj, _get_operation(operation))

    angle_val = adsk.core.ValueInput.createByReal(deg_to_rad(angle))
    rev_input.setAngleExtent(False, angle_val)

    feature = revolves.add(rev_input)
    return "Revolved '{}' profile {} by {}deg around {} -> '{}'".format(
        sketch.name, profile_index, angle, axis, feature.name)


def sweep(app, profile_sketch_index, path_sketch_index, profile_index=0,
          path_curve_index=0, operation="new_body", **kwargs):
    """Sweep a profile along a path."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    prof_sketch = _get_sketch(app, profile_sketch_index)
    profile = _get_profile(prof_sketch, profile_index)

    path_sketch = _get_sketch(app, path_sketch_index)
    path_curves = path_sketch.sketchCurves
    all_curves = []
    for i in range(path_curves.count):
        all_curves.append(path_curves.item(i))
    if path_curve_index >= len(all_curves):
        raise ValueError("Path curve index {} out of range".format(path_curve_index))

    sweeps = root.features.sweepFeatures

    path_obj = root.features.createPath(all_curves[path_curve_index])

    sweep_input = sweeps.createInput(profile, path_obj, _get_operation(operation))
    feature = sweeps.add(sweep_input)
    return "Swept '{}' along path in '{}' -> '{}'".format(
        prof_sketch.name, path_sketch.name, feature.name)


def loft(app, profiles, operation="new_body", **kwargs):
    """Create a loft between multiple profiles."""
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    lofts = root.features.loftFeatures
    loft_input = lofts.createInput(_get_operation(operation))

    for prof_def in profiles:
        sketch = _get_sketch(app, prof_def["sketch_index"])
        profile = _get_profile(sketch, prof_def.get("profile_index", 0))
        loft_input.loftSections.add(profile)

    feature = lofts.add(loft_input)
    return "Lofted {} profiles -> '{}'".format(len(profiles), feature.name)
