"""JIS standard hole creation tools for Fusion 360.

Creates threaded holes, counterbore holes, and countersink holes
based on JIS thread and fastener dimensions.
"""

import math
from utils.geometry import mm_to_cm, point3d, get_body_by_name
from data import jis_threads, jis_bolts, jis_screws


def register(registry):
    """Register all JIS hole tools."""

    registry.register(
        name="create_threaded_hole",
        description="Create a threaded hole (tap hole) on a face. Uses JIS metric thread dimensions for the correct tap drill diameter.",
        input_schema={
            "type": "object",
            "properties": {
                "size": {
                    "type": "string",
                    "description": "Thread size: M2 through M12.",
                },
                "depth": {
                    "type": "number",
                    "description": "Hole depth in mm. Use 0 for through-all.",
                },
                "x": {"type": "number", "description": "Hole center X position in mm", "default": 0},
                "y": {"type": "number", "description": "Hole center Y position in mm", "default": 0},
                "body_name": {
                    "type": "string",
                    "description": "Target body name. Uses first body if not specified.",
                },
                "face_index": {
                    "type": "integer",
                    "description": "Face index on the body to place the hole. Uses top face if not specified.",
                    "default": 0,
                },
                "through_all": {
                    "type": "boolean",
                    "description": "Whether the hole goes through the entire body.",
                    "default": False,
                },
            },
            "required": ["size", "depth"],
        },
        handler=create_threaded_hole,
    )

    registry.register(
        name="create_counterbore_hole",
        description="Create a counterbore hole sized for a JIS socket head cap screw (B1176). Automatically uses correct head diameter and depth.",
        input_schema={
            "type": "object",
            "properties": {
                "size": {
                    "type": "string",
                    "description": "Bolt size: M2 through M12.",
                },
                "hole_depth": {
                    "type": "number",
                    "description": "Through-hole depth in mm. Use 0 for through-all.",
                },
                "x": {"type": "number", "description": "Hole center X position in mm", "default": 0},
                "y": {"type": "number", "description": "Hole center Y position in mm", "default": 0},
                "body_name": {
                    "type": "string",
                    "description": "Target body name.",
                },
                "face_index": {
                    "type": "integer",
                    "description": "Face index for hole placement.",
                    "default": 0,
                },
            },
            "required": ["size", "hole_depth"],
        },
        handler=create_counterbore_hole,
    )

    registry.register(
        name="create_countersink_hole",
        description="Create a countersink hole sized for a JIS flat head screw (B1111 皿小ねじ). Automatically uses correct head diameter and angle.",
        input_schema={
            "type": "object",
            "properties": {
                "size": {
                    "type": "string",
                    "description": "Screw size: M2 through M10.",
                },
                "hole_depth": {
                    "type": "number",
                    "description": "Through-hole depth in mm. Use 0 for through-all.",
                },
                "x": {"type": "number", "description": "Hole center X position in mm", "default": 0},
                "y": {"type": "number", "description": "Hole center Y position in mm", "default": 0},
                "body_name": {
                    "type": "string",
                    "description": "Target body name.",
                },
                "face_index": {
                    "type": "integer",
                    "description": "Face index for hole placement.",
                    "default": 0,
                },
            },
            "required": ["size", "hole_depth"],
        },
        handler=create_countersink_hole,
    )


def _get_target_face(app, body_name=None, face_index=0):
    """Get a target face for hole placement."""
    design = app.activeProduct
    root = design.rootComponent

    if body_name:
        body = get_body_by_name(app, body_name)
        if not body:
            raise ValueError("Body '{}' not found.".format(body_name))
    else:
        if root.bRepBodies.count == 0:
            raise ValueError("No bodies in the design.")
        body = root.bRepBodies.item(0)

    if face_index < 0 or face_index >= body.faces.count:
        raise ValueError("Face index {} out of range (0-{})".format(
            face_index, body.faces.count - 1))

    return body.faces.item(face_index)


def create_threaded_hole(app, size, depth, x=0, y=0, body_name=None,
                          face_index=0, through_all=False, **kwargs):
    """Create a threaded hole using sketch + extrude cut."""
    import adsk.core
    import adsk.fusion

    size = size.upper()
    thread = jis_threads.get_thread(size)
    tap_drill = thread["d1"]

    design = app.activeProduct
    root = design.rootComponent

    face = _get_target_face(app, body_name, face_index)

    # Create sketch on the face
    sketch = root.sketches.add(face)
    center = adsk.core.Point3D.create(mm_to_cm(x), mm_to_cm(y), 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(
        center, mm_to_cm(tap_drill / 2.0)
    )

    profile = sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures
    ext_input = extrudes.createInput(
        profile,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )

    if through_all or depth == 0:
        ext_input.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
    else:
        ext_input.setDistanceExtent(
            False,
            adsk.core.ValueInput.createByReal(mm_to_cm(depth))
        )
        ext_input.setDirectionFlip(True)

    extrudes.add(ext_input)

    depth_str = "through-all" if (through_all or depth == 0) else "{}mm".format(depth)
    return "Created {} threaded hole (tap drill={:.2f}mm) depth={} at ({},{})".format(
        size, tap_drill, depth_str, x, y)


def create_counterbore_hole(app, size, hole_depth, x=0, y=0,
                             body_name=None, face_index=0, **kwargs):
    """Create a counterbore hole for socket head cap screws."""
    import adsk.core
    import adsk.fusion

    size = size.upper()
    thread = jis_threads.get_thread(size)
    head = jis_bolts.get_socket_head(size)

    d_clearance = thread["d"] + 0.5  # clearance hole
    dk = head["dk"]  # counterbore diameter
    k = head["k"]    # counterbore depth (head height)

    design = app.activeProduct
    root = design.rootComponent

    face = _get_target_face(app, body_name, face_index)

    # Counterbore (larger circle)
    cb_sketch = root.sketches.add(face)
    center = adsk.core.Point3D.create(mm_to_cm(x), mm_to_cm(y), 0)
    cb_sketch.sketchCurves.sketchCircles.addByCenterRadius(
        center, mm_to_cm(dk / 2.0)
    )

    cb_profile = cb_sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures
    cb_input = extrudes.createInput(
        cb_profile,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    cb_input.setDistanceExtent(
        False,
        adsk.core.ValueInput.createByReal(mm_to_cm(k))
    )
    cb_input.setDirectionFlip(True)
    extrudes.add(cb_input)

    # Through hole (smaller circle)
    hole_sketch = root.sketches.add(face)
    hole_sketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(mm_to_cm(x), mm_to_cm(y), 0),
        mm_to_cm(d_clearance / 2.0)
    )

    hole_profile = hole_sketch.profiles.item(0)
    hole_input = extrudes.createInput(
        hole_profile,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    if hole_depth == 0:
        hole_input.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
    else:
        hole_input.setDistanceExtent(
            False,
            adsk.core.ValueInput.createByReal(mm_to_cm(hole_depth))
        )
        hole_input.setDirectionFlip(True)
    extrudes.add(hole_input)

    return "Created counterbore hole for {} bolt: bore d={}mm h={}mm, hole d={:.1f}mm at ({},{})".format(
        size, dk, k, d_clearance, x, y)


def create_countersink_hole(app, size, hole_depth, x=0, y=0,
                             body_name=None, face_index=0, **kwargs):
    """Create a countersink hole for flat head screws."""
    import adsk.core
    import adsk.fusion

    size = size.upper()
    thread = jis_threads.get_thread(size)
    head = jis_screws.get_flat_head(size)

    d_clearance = thread["d"] + 0.5
    dk = head["dk"]       # countersink diameter
    k = head["k"]         # countersink depth

    design = app.activeProduct
    root = design.rootComponent

    face = _get_target_face(app, body_name, face_index)

    # Create countersink using revolve (cone shape)
    xz_plane = root.xZConstructionPlane
    cs_sketch = root.sketches.add(xz_plane)
    lines = cs_sketch.sketchCurves.sketchLines

    # Countersink profile (triangle to revolve)
    r_outer = mm_to_cm(dk / 2.0)
    r_inner = mm_to_cm(d_clearance / 2.0)
    h = mm_to_cm(k)

    p0 = adsk.core.Point3D.create(0, 0, 0)
    p1 = adsk.core.Point3D.create(r_inner, 0, 0)
    p2 = adsk.core.Point3D.create(r_outer, h, 0)
    p3 = adsk.core.Point3D.create(0, h, 0)

    lines.addByTwoPoints(p0, p1)
    lines.addByTwoPoints(p1, p2)
    lines.addByTwoPoints(p2, p3)
    lines.addByTwoPoints(p3, p0)

    cs_profile = cs_sketch.profiles.item(0)
    revolves = root.features.revolveFeatures

    y_axis = root.yConstructionAxis
    rev_input = revolves.createInput(
        cs_profile, y_axis,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    rev_input.setAngleExtent(
        False,
        adsk.core.ValueInput.createByReal(math.pi * 2)
    )
    revolves.add(rev_input)

    # Through hole
    hole_sketch = root.sketches.add(face)
    hole_sketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(mm_to_cm(x), mm_to_cm(y), 0),
        mm_to_cm(d_clearance / 2.0)
    )

    hole_profile = hole_sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures
    hole_input = extrudes.createInput(
        hole_profile,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    if hole_depth == 0:
        hole_input.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)
    else:
        hole_input.setDistanceExtent(
            False,
            adsk.core.ValueInput.createByReal(mm_to_cm(hole_depth))
        )
        hole_input.setDirectionFlip(True)
    extrudes.add(hole_input)

    return "Created countersink hole for {} screw: cs d={}mm, hole d={:.1f}mm at ({},{})".format(
        size, dk, d_clearance, x, y)
