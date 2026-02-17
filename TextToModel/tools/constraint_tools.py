"""Sketch constraint and dimension tools for Fusion 360."""

import json
from utils.geometry import mm_to_cm, deg_to_rad, cm_to_mm


def register(registry):
    """Register all constraint tools."""

    registry.register(
        name="add_sketch_constraint",
        description=(
            "Add a geometric constraint to sketch entities. "
            "Supported types: coincident, tangent, perpendicular, parallel, "
            "horizontal, vertical, equal, concentric, midpoint, colinear, smooth."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "sketch_index": {
                    "type": "integer",
                    "description": "Index of the sketch (0-based).",
                },
                "constraint_type": {
                    "type": "string",
                    "description": "Type of constraint.",
                    "enum": [
                        "coincident", "tangent", "perpendicular", "parallel",
                        "horizontal", "vertical", "equal", "concentric",
                        "midpoint", "colinear", "smooth",
                    ],
                },
                "entity1_index": {
                    "type": "integer",
                    "description": "Index of the first sketch entity (curve or point).",
                },
                "entity2_index": {
                    "type": "integer",
                    "description": "Index of the second sketch entity (if required by constraint type).",
                },
            },
            "required": ["sketch_index", "constraint_type", "entity1_index"],
        },
        handler=add_sketch_constraint,
    )

    registry.register(
        name="add_sketch_dimension",
        description=(
            "Add a dimension constraint to sketch entities. "
            "Supported types: distance, radius, diameter, angle."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "sketch_index": {
                    "type": "integer",
                    "description": "Index of the sketch (0-based).",
                },
                "dimension_type": {
                    "type": "string",
                    "description": "Type of dimension.",
                    "enum": ["distance", "radius", "diameter", "angle"],
                },
                "entity1_index": {
                    "type": "integer",
                    "description": "Index of the first sketch entity.",
                },
                "entity2_index": {
                    "type": "integer",
                    "description": "Index of the second entity (for distance between two entities or angle).",
                },
                "value": {
                    "type": "number",
                    "description": "Dimension value: mm for distance/radius/diameter, degrees for angle.",
                },
                "text_position_x": {
                    "type": "number",
                    "description": "X position for the dimension text in mm.",
                    "default": 0,
                },
                "text_position_y": {
                    "type": "number",
                    "description": "Y position for the dimension text in mm.",
                    "default": 0,
                },
            },
            "required": ["sketch_index", "dimension_type", "entity1_index", "value"],
        },
        handler=add_sketch_dimension,
    )

    registry.register(
        name="list_sketch_entities",
        description="List all entities (curves, points) in a sketch for use with constraints and dimensions.",
        input_schema={
            "type": "object",
            "properties": {
                "sketch_index": {
                    "type": "integer",
                    "description": "Index of the sketch (0-based).",
                },
            },
            "required": ["sketch_index"],
        },
        handler=list_sketch_entities,
    )


def _get_sketch(app, sketch_index):
    """Get a sketch by index."""
    design = app.activeProduct
    sketches = design.rootComponent.sketches
    if sketches.count == 0:
        raise ValueError("No sketches exist.")
    if sketch_index < 0 or sketch_index >= sketches.count:
        raise ValueError("Sketch index {} out of range (0-{})".format(
            sketch_index, sketches.count - 1))
    return sketches.item(sketch_index)


def _get_sketch_entity(sketch, entity_index):
    """Get a sketch entity (curve) by index from the combined curves collection."""
    curves = sketch.sketchCurves
    if entity_index < 0 or entity_index >= curves.count:
        raise ValueError("Entity index {} out of range (0-{})".format(
            entity_index, curves.count - 1))
    return curves.item(entity_index)


def add_sketch_constraint(app, sketch_index, constraint_type, entity1_index,
                            entity2_index=None, **kwargs):
    """Add a geometric constraint to sketch entities."""
    import adsk.fusion

    sketch = _get_sketch(app, sketch_index)
    constraints = sketch.geometricConstraints

    e1 = _get_sketch_entity(sketch, entity1_index)
    e2 = _get_sketch_entity(sketch, entity2_index) if entity2_index is not None else None

    two_entity_types = {
        "coincident", "tangent", "perpendicular", "parallel",
        "equal", "concentric", "colinear", "smooth",
    }
    if constraint_type in two_entity_types and e2 is None:
        raise ValueError("'{}' constraint requires entity2_index.".format(constraint_type))

    if constraint_type == "coincident":
        constraints.addCoincident(e1, e2)
    elif constraint_type == "tangent":
        constraints.addTangent(e1, e2)
    elif constraint_type == "perpendicular":
        constraints.addPerpendicular(e1, e2)
    elif constraint_type == "parallel":
        constraints.addParallel(e1, e2)
    elif constraint_type == "horizontal":
        constraints.addHorizontal(e1)
    elif constraint_type == "vertical":
        constraints.addVertical(e1)
    elif constraint_type == "equal":
        constraints.addEqual(e1, e2)
    elif constraint_type == "concentric":
        constraints.addConcentric(e1, e2)
    elif constraint_type == "midpoint":
        if e2 is None:
            raise ValueError("'midpoint' constraint requires entity2_index (the line).")
        constraints.addMidPoint(e1, e2)
    elif constraint_type == "colinear":
        constraints.addCollinear(e1, e2)
    elif constraint_type == "smooth":
        constraints.addSmooth(e1, e2)
    else:
        raise ValueError("Unknown constraint type: {}".format(constraint_type))

    return "Added '{}' constraint on sketch '{}' (entities: {}{})".format(
        constraint_type, sketch.name, entity1_index,
        ", {}".format(entity2_index) if entity2_index is not None else "")


def add_sketch_dimension(app, sketch_index, dimension_type, entity1_index, value,
                           entity2_index=None, text_position_x=0, text_position_y=0,
                           **kwargs):
    """Add a dimension constraint to sketch entities."""
    import adsk.core
    from utils.geometry import point3d

    sketch = _get_sketch(app, sketch_index)
    dims = sketch.sketchDimensions
    text_pt = point3d(text_position_x, text_position_y, 0)

    e1 = _get_sketch_entity(sketch, entity1_index)

    if dimension_type == "distance":
        if entity2_index is not None:
            e2 = _get_sketch_entity(sketch, entity2_index)
            dims.addDistanceDimension(
                e1, e2,
                adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                text_pt,
            )
        else:
            dims.addDistanceDimension(
                e1.startSketchPoint, e1.endSketchPoint,
                adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                text_pt,
            )
        dim = sketch.sketchDimensions.item(sketch.sketchDimensions.count - 1)
        dim.parameter.value = mm_to_cm(value)
        return "Added distance dimension {}mm on sketch '{}'".format(value, sketch.name)

    elif dimension_type == "radius":
        dims.addRadialDimension(e1, text_pt)
        dim = sketch.sketchDimensions.item(sketch.sketchDimensions.count - 1)
        dim.parameter.value = mm_to_cm(value)
        return "Added radius dimension {}mm on sketch '{}'".format(value, sketch.name)

    elif dimension_type == "diameter":
        dims.addDiameterDimension(e1, text_pt)
        dim = sketch.sketchDimensions.item(sketch.sketchDimensions.count - 1)
        dim.parameter.value = mm_to_cm(value)
        return "Added diameter dimension {}mm on sketch '{}'".format(value, sketch.name)

    elif dimension_type == "angle":
        if entity2_index is None:
            raise ValueError("'angle' dimension requires entity2_index.")
        e2 = _get_sketch_entity(sketch, entity2_index)
        dims.addAngularDimension(e1, e2, text_pt)
        dim = sketch.sketchDimensions.item(sketch.sketchDimensions.count - 1)
        dim.parameter.value = deg_to_rad(value)
        return "Added angle dimension {}deg on sketch '{}'".format(value, sketch.name)

    else:
        raise ValueError("Unknown dimension type: {}".format(dimension_type))


def list_sketch_entities(app, sketch_index, **kwargs):
    """List all entities in a sketch."""
    sketch = _get_sketch(app, sketch_index)

    entities = []
    curves = sketch.sketchCurves

    for i in range(curves.count):
        curve = curves.item(i)
        type_name = type(curve).__name__
        type_map = {
            "SketchLine": "line",
            "SketchCircle": "circle",
            "SketchArc": "arc",
            "SketchFittedSpline": "spline",
            "SketchEllipse": "ellipse",
            "SketchEllipticalArc": "elliptical_arc",
            "SketchConicCurve": "conic",
        }
        entity_type = type_map.get(type_name, type_name)

        info = {
            "index": i,
            "type": entity_type,
            "is_construction": curve.isConstruction if hasattr(curve, "isConstruction") else False,
        }

        if hasattr(curve, "startSketchPoint") and curve.startSketchPoint:
            sp = curve.startSketchPoint.geometry
            info["start"] = {
                "x": round(cm_to_mm(sp.x), 4),
                "y": round(cm_to_mm(sp.y), 4),
            }
        if hasattr(curve, "endSketchPoint") and curve.endSketchPoint:
            ep = curve.endSketchPoint.geometry
            info["end"] = {
                "x": round(cm_to_mm(ep.x), 4),
                "y": round(cm_to_mm(ep.y), 4),
            }
        if entity_type == "circle" and hasattr(curve, "centerSketchPoint"):
            cp = curve.centerSketchPoint.geometry
            info["center"] = {
                "x": round(cm_to_mm(cp.x), 4),
                "y": round(cm_to_mm(cp.y), 4),
            }
            info["radius_mm"] = round(cm_to_mm(curve.radius), 4)

        entities.append(info)

    result = {
        "sketch": sketch.name,
        "entity_count": len(entities),
        "entities": entities,
    }
    return json.dumps(result, indent=2)
