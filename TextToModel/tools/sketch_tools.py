"""Sketch creation and drawing tools for Fusion 360."""

import math
from utils.geometry import mm_to_cm, point3d, get_plane


def register(registry):
    """Register all sketch tools."""

    registry.register(
        name="create_sketch",
        description="Create a new sketch on a construction plane (XY, XZ, or YZ) or on a planar face.",
        input_schema={
            "type": "object",
            "properties": {
                "plane": {
                    "type": "string",
                    "description": "Construction plane name: 'XY', 'XZ', or 'YZ'",
                    "enum": ["XY", "XZ", "YZ"],
                },
                "component_name": {
                    "type": "string",
                    "description": "Optional component name. Uses root component if not specified.",
                },
            },
            "required": ["plane"],
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


def create_sketch(app, plane="XY", component_name=None, **kwargs):
    """Create a new sketch on the specified plane."""
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    target_comp = root
    if component_name:
        for occ in root.allOccurrences:
            if occ.component.name == component_name:
                target_comp = occ.component
                break

    plane_obj = get_plane(app, plane)
    sketch = target_comp.sketches.add(plane_obj)

    return "Created sketch '{}' on {} plane (index: {})".format(
        sketch.name, plane, target_comp.sketches.count - 1)


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
