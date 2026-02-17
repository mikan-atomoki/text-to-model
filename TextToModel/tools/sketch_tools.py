"""Sketch creation and drawing tools for Fusion 360."""

import math
from utils.geometry import mm_to_cm, point3d, get_plane


def register(registry):
    """Register all sketch tools."""

    registry.register(
        name="create_sketch",
        description=(
            "Create a new sketch on a construction plane (XY, XZ, YZ), "
            "a user-created construction plane (by index), or a planar face "
            "(by 'face:{body_name}:{face_index}')."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "plane": {
                    "type": "string",
                    "description": "Construction plane name: 'XY', 'XZ', or 'YZ'. Ignored if construction_plane_index or face_ref is provided.",
                    "enum": ["XY", "XZ", "YZ"],
                },
                "construction_plane_index": {
                    "type": "integer",
                    "description": "Index of a user-created construction plane (0-based). Overrides 'plane'.",
                },
                "face_ref": {
                    "type": "string",
                    "description": "Planar face reference: 'face:{body_name}:{face_index}'. Overrides 'plane' and 'construction_plane_index'.",
                },
                "component_name": {
                    "type": "string",
                    "description": "Optional component name. Uses root component if not specified.",
                },
            },
            "required": [],
        },
        handler=create_sketch,
    )

    registry.register(
        name="draw_circle",
        description="Draw a circle on the active or most recent sketch.",
        input_schema={
            "type": "object",
            "properties": {
                "center_x": {"type": "number", "description": "Center X coordinate in mm", "default": 0},
                "center_y": {"type": "number", "description": "Center Y coordinate in mm", "default": 0},
                "radius": {"type": "number", "description": "Radius in mm"},
                "sketch_index": {"type": "integer", "description": "Sketch index (0-based). Uses last sketch if not specified."},
            },
            "required": ["radius"],
        },
        handler=draw_circle,
    )

    registry.register(
        name="draw_rectangle",
        description="Draw a rectangle defined by two corner points on a sketch.",
        input_schema={
            "type": "object",
            "properties": {
                "x1": {"type": "number", "description": "First corner X in mm", "default": 0},
                "y1": {"type": "number", "description": "First corner Y in mm", "default": 0},
                "x2": {"type": "number", "description": "Second corner X in mm"},
                "y2": {"type": "number", "description": "Second corner Y in mm"},
                "sketch_index": {"type": "integer", "description": "Sketch index (0-based). Uses last sketch if not specified."},
            },
            "required": ["x2", "y2"],
        },
        handler=draw_rectangle,
    )

    registry.register(
        name="draw_line",
        description="Draw a line between two points on a sketch.",
        input_schema={
            "type": "object",
            "properties": {
                "x1": {"type": "number", "description": "Start X in mm", "default": 0},
                "y1": {"type": "number", "description": "Start Y in mm", "default": 0},
                "x2": {"type": "number", "description": "End X in mm"},
                "y2": {"type": "number", "description": "End Y in mm"},
                "sketch_index": {"type": "integer", "description": "Sketch index (0-based). Uses last sketch if not specified."},
            },
            "required": ["x2", "y2"],
        },
        handler=draw_line,
    )

    registry.register(
        name="draw_arc",
        description="Draw a 3-point arc on a sketch.",
        input_schema={
            "type": "object",
            "properties": {
                "start_x": {"type": "number", "description": "Start X in mm"},
                "start_y": {"type": "number", "description": "Start Y in mm"},
                "mid_x": {"type": "number", "description": "Mid-point X in mm"},
                "mid_y": {"type": "number", "description": "Mid-point Y in mm"},
                "end_x": {"type": "number", "description": "End X in mm"},
                "end_y": {"type": "number", "description": "End Y in mm"},
                "sketch_index": {"type": "integer", "description": "Sketch index (0-based). Uses last sketch if not specified."},
            },
            "required": ["start_x", "start_y", "mid_x", "mid_y", "end_x", "end_y"],
        },
        handler=draw_arc,
    )

    registry.register(
        name="draw_spline",
        description="Draw a spline through a series of points on a sketch.",
        input_schema={
            "type": "object",
            "properties": {
                "points": {
                    "type": "array",
                    "description": "Array of [x, y] coordinate pairs in mm",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                    "minItems": 2,
                },
                "sketch_index": {"type": "integer", "description": "Sketch index (0-based). Uses last sketch if not specified."},
            },
            "required": ["points"],
        },
        handler=draw_spline,
    )

    registry.register(
        name="draw_polygon",
        description="Draw a regular polygon (3-12 sides) on a sketch.",
        input_schema={
            "type": "object",
            "properties": {
                "sides": {
                    "type": "integer",
                    "description": "Number of sides (3-12).",
                    "minimum": 3,
                    "maximum": 12,
                },
                "radius": {
                    "type": "number",
                    "description": "Circumscribed radius (center to vertex) in mm.",
                },
                "center_x": {"type": "number", "description": "Center X in mm.", "default": 0},
                "center_y": {"type": "number", "description": "Center Y in mm.", "default": 0},
                "rotation": {
                    "type": "number",
                    "description": "Rotation angle in degrees (0 = first vertex at top).",
                    "default": 0,
                },
                "sketch_index": {"type": "integer", "description": "Sketch index (0-based). Uses last sketch if not specified."},
            },
            "required": ["sides", "radius"],
        },
        handler=draw_polygon,
    )


def _get_sketch(app, sketch_index=None):
    """Get a sketch by index or return the last sketch."""
    design = app.activeProduct
    root = design.rootComponent
    sketches = root.sketches

    if sketches.count == 0:
        raise ValueError("No sketches exist. Create a sketch first with create_sketch.")

    if sketch_index is not None:
        if sketch_index < 0 or sketch_index >= sketches.count:
            raise ValueError("Sketch index {} out of range (0-{})".format(
                sketch_index, sketches.count - 1))
        return sketches.item(sketch_index)

    return sketches.item(sketches.count - 1)


def create_sketch(app, plane="XY", construction_plane_index=None,
                   face_ref=None, component_name=None, **kwargs):
    """Create a new sketch on a plane, construction plane, or face."""
    import adsk.fusion
    from utils.geometry import get_construction_plane, get_body_by_name

    design = app.activeProduct
    root = design.rootComponent

    target_comp = root
    if component_name:
        for occ in root.allOccurrences:
            if occ.component.name == component_name:
                target_comp = occ.component
                break

    if face_ref:
        parts = face_ref.split(":")
        if len(parts) != 3 or parts[0] != "face":
            raise ValueError("face_ref must be 'face:body_name:face_index', got '{}'".format(face_ref))
        body = get_body_by_name(app, parts[1])
        if not body:
            raise ValueError("Body '{}' not found.".format(parts[1]))
        face_index = int(parts[2])
        if face_index < 0 or face_index >= body.faces.count:
            raise ValueError("Face index {} out of range (0-{})".format(
                face_index, body.faces.count - 1))
        plane_obj = body.faces.item(face_index)
        plane_desc = face_ref
    elif construction_plane_index is not None:
        plane_obj = get_construction_plane(app, construction_plane_index, component_name)
        plane_desc = "construction plane #{}".format(construction_plane_index)
    else:
        plane_obj = get_plane(app, plane)
        plane_desc = "{} plane".format(plane)

    sketch = target_comp.sketches.add(plane_obj)

    return "Created sketch '{}' on {} (index: {})".format(
        sketch.name, plane_desc, target_comp.sketches.count - 1)


def draw_circle(app, radius, center_x=0, center_y=0, sketch_index=None, **kwargs):
    """Draw a circle on a sketch."""
    sketch = _get_sketch(app, sketch_index)
    circles = sketch.sketchCurves.sketchCircles

    center = point3d(center_x, center_y, 0)
    circle = circles.addByCenterRadius(center, mm_to_cm(radius))

    return "Drew circle: center=({}, {})mm, radius={}mm on '{}'".format(
        center_x, center_y, radius, sketch.name)


def draw_rectangle(app, x2, y2, x1=0, y1=0, sketch_index=None, **kwargs):
    """Draw a rectangle on a sketch."""
    sketch = _get_sketch(app, sketch_index)
    lines = sketch.sketchCurves.sketchLines

    p1 = point3d(x1, y1, 0)
    p2 = point3d(x2, y2, 0)
    lines.addTwoPointRectangle(p1, p2)

    return "Drew rectangle: ({}, {}) to ({}, {})mm on '{}'".format(
        x1, y1, x2, y2, sketch.name)


def draw_line(app, x2, y2, x1=0, y1=0, sketch_index=None, **kwargs):
    """Draw a line on a sketch."""
    sketch = _get_sketch(app, sketch_index)
    lines = sketch.sketchCurves.sketchLines

    p1 = point3d(x1, y1, 0)
    p2 = point3d(x2, y2, 0)
    lines.addByTwoPoints(p1, p2)

    return "Drew line: ({}, {}) to ({}, {})mm on '{}'".format(
        x1, y1, x2, y2, sketch.name)


def draw_arc(app, start_x, start_y, mid_x, mid_y, end_x, end_y, sketch_index=None, **kwargs):
    """Draw a 3-point arc on a sketch."""
    sketch = _get_sketch(app, sketch_index)
    arcs = sketch.sketchCurves.sketchArcs

    p_start = point3d(start_x, start_y, 0)
    p_mid = point3d(mid_x, mid_y, 0)
    p_end = point3d(end_x, end_y, 0)
    arcs.addByThreePoints(p_start, p_mid, p_end)

    return "Drew arc through ({},{}), ({},{}), ({},{})mm on '{}'".format(
        start_x, start_y, mid_x, mid_y, end_x, end_y, sketch.name)


def draw_spline(app, points, sketch_index=None, **kwargs):
    """Draw a spline through a series of points on a sketch."""
    import adsk.core

    sketch = _get_sketch(app, sketch_index)

    point_collection = adsk.core.ObjectCollection.create()
    for pt in points:
        point_collection.add(point3d(pt[0], pt[1], 0))

    sketch.sketchCurves.sketchFittedSplines.add(point_collection)

    return "Drew spline through {} points on '{}'".format(len(points), sketch.name)


def draw_polygon(app, sides, radius, center_x=0, center_y=0, rotation=0,
                  sketch_index=None, **kwargs):
    """Draw a regular polygon by connecting vertices with lines."""
    from utils.geometry import deg_to_rad

    if sides < 3 or sides > 12:
        raise ValueError("Sides must be 3-12, got {}.".format(sides))

    sketch = _get_sketch(app, sketch_index)
    lines = sketch.sketchCurves.sketchLines

    angle_step = 2 * math.pi / sides
    start_angle = deg_to_rad(rotation) - math.pi / 2  # default: first vertex at top

    vertices = []
    for i in range(sides):
        angle = start_angle + i * angle_step
        vx = center_x + radius * math.cos(angle)
        vy = center_y + radius * math.sin(angle)
        vertices.append(point3d(vx, vy, 0))

    for i in range(sides):
        p1 = vertices[i]
        p2 = vertices[(i + 1) % sides]
        lines.addByTwoPoints(p1, p2)

    return "Drew {}-sided polygon: center=({}, {})mm, radius={}mm on '{}'".format(
        sides, center_x, center_y, radius, sketch.name)
