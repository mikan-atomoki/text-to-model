"""Inspection tools for querying body/sketch geometry in Fusion 360."""

import json
from utils.geometry import cm_to_mm, get_body_by_name


def register(registry):
    """Register all inspection tools."""

    registry.register(
        name="list_edges",
        description="List all edges of a body with their type, geometry, and index. Use this to identify edges for fillet/chamfer operations.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {"type": "string", "description": "Name of the body to inspect."},
                "component_name": {"type": "string", "description": "Optional component name."},
            },
            "required": ["body_name"],
        },
        handler=list_edges,
    )

    registry.register(
        name="list_faces",
        description="List all faces of a body with their type, area, centroid, and normal. Use this to identify faces for shell/sketch-on-face operations.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {"type": "string", "description": "Name of the body to inspect."},
                "component_name": {"type": "string", "description": "Optional component name."},
            },
            "required": ["body_name"],
        },
        handler=list_faces,
    )

    registry.register(
        name="list_sketches",
        description="List all sketches in the design with their name, profile count, and curve count.",
        input_schema={
            "type": "object",
            "properties": {
                "component_name": {"type": "string", "description": "Optional component name."},
            },
            "required": [],
        },
        handler=list_sketches,
    )

    registry.register(
        name="get_body_bounds",
        description="Get the bounding box of a body (min/max/size/center in mm).",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {"type": "string", "description": "Name of the body."},
                "component_name": {"type": "string", "description": "Optional component name."},
            },
            "required": ["body_name"],
        },
        handler=get_body_bounds,
    )

    registry.register(
        name="list_construction_planes",
        description="List all user-created construction planes in the design.",
        input_schema={
            "type": "object",
            "properties": {
                "component_name": {"type": "string", "description": "Optional component name."},
            },
            "required": [],
        },
        handler=list_construction_planes,
    )


def _edge_type_name(edge):
    """Get a human-readable edge type name."""
    import adsk.core
    geom = edge.geometry
    type_name = type(geom).__name__
    type_map = {
        "Line3D": "linear",
        "Circle3D": "circular",
        "Arc3D": "arc",
        "EllipticalArc3D": "elliptical_arc",
        "NurbsCurve3D": "spline",
        "InfiniteLine3D": "linear",
    }
    return type_map.get(type_name, type_name.lower())


def _face_type_name(face):
    """Get a human-readable face type name."""
    import adsk.core
    geom = face.geometry
    type_name = type(geom).__name__
    type_map = {
        "Plane": "planar",
        "Cylinder": "cylindrical",
        "Cone": "conical",
        "Sphere": "spherical",
        "Torus": "toroidal",
        "NurbsSurface": "freeform",
        "EllipticalCylinder": "elliptical_cylinder",
        "EllipticalCone": "elliptical_cone",
    }
    return type_map.get(type_name, type_name.lower())


def list_edges(app, body_name, component_name=None, **kwargs):
    """List all edges of a body."""
    body = get_body_by_name(app, body_name, component_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    edges = []
    for i in range(body.edges.count):
        edge = body.edges.item(i)
        sp = edge.startVertex.geometry if edge.startVertex else None
        ep = edge.endVertex.geometry if edge.endVertex else None

        edge_info = {
            "index": i,
            "type": _edge_type_name(edge),
            "length_mm": round(cm_to_mm(edge.length), 4),
        }
        if sp:
            edge_info["start"] = {
                "x": round(cm_to_mm(sp.x), 4),
                "y": round(cm_to_mm(sp.y), 4),
                "z": round(cm_to_mm(sp.z), 4),
            }
        if ep:
            edge_info["end"] = {
                "x": round(cm_to_mm(ep.x), 4),
                "y": round(cm_to_mm(ep.y), 4),
                "z": round(cm_to_mm(ep.z), 4),
            }
        edges.append(edge_info)

    result = {
        "body": body_name,
        "edge_count": len(edges),
        "edges": edges,
    }
    return json.dumps(result, indent=2)


def list_faces(app, body_name, component_name=None, **kwargs):
    """List all faces of a body."""
    body = get_body_by_name(app, body_name, component_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    faces = []
    for i in range(body.faces.count):
        face = body.faces.item(i)
        centroid = face.centroid
        area_mm2 = cm_to_mm(cm_to_mm(face.area))  # cm^2 -> mm^2

        face_info = {
            "index": i,
            "type": _face_type_name(face),
            "area_mm2": round(area_mm2, 4),
            "centroid": {
                "x": round(cm_to_mm(centroid.x), 4),
                "y": round(cm_to_mm(centroid.y), 4),
                "z": round(cm_to_mm(centroid.z), 4),
            },
        }

        evaluator = face.evaluator
        ok, normal = evaluator.getNormalAtPoint(centroid)
        if ok:
            face_info["normal"] = {
                "x": round(normal.x, 6),
                "y": round(normal.y, 6),
                "z": round(normal.z, 6),
            }

        faces.append(face_info)

    result = {
        "body": body_name,
        "face_count": len(faces),
        "faces": faces,
    }
    return json.dumps(result, indent=2)


def list_sketches(app, component_name=None, **kwargs):
    """List all sketches in the design."""
    design = app.activeProduct
    root = design.rootComponent

    target_comp = root
    if component_name:
        for occ in root.allOccurrences:
            if occ.component.name == component_name:
                target_comp = occ.component
                break

    sketches = target_comp.sketches
    result_list = []
    for i in range(sketches.count):
        sk = sketches.item(i)
        result_list.append({
            "index": i,
            "name": sk.name,
            "profile_count": sk.profiles.count,
            "curve_count": sk.sketchCurves.count,
            "is_visible": sk.isVisible,
        })

    result = {
        "sketch_count": len(result_list),
        "sketches": result_list,
    }
    return json.dumps(result, indent=2)


def get_body_bounds(app, body_name, component_name=None, **kwargs):
    """Get the bounding box of a body."""
    body = get_body_by_name(app, body_name, component_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    bb = body.boundingBox
    min_pt = bb.minPoint
    max_pt = bb.maxPoint

    min_mm = {
        "x": round(cm_to_mm(min_pt.x), 4),
        "y": round(cm_to_mm(min_pt.y), 4),
        "z": round(cm_to_mm(min_pt.z), 4),
    }
    max_mm = {
        "x": round(cm_to_mm(max_pt.x), 4),
        "y": round(cm_to_mm(max_pt.y), 4),
        "z": round(cm_to_mm(max_pt.z), 4),
    }
    size_mm = {
        "x": round(max_mm["x"] - min_mm["x"], 4),
        "y": round(max_mm["y"] - min_mm["y"], 4),
        "z": round(max_mm["z"] - min_mm["z"], 4),
    }
    center_mm = {
        "x": round((min_mm["x"] + max_mm["x"]) / 2, 4),
        "y": round((min_mm["y"] + max_mm["y"]) / 2, 4),
        "z": round((min_mm["z"] + max_mm["z"]) / 2, 4),
    }

    result = {
        "body": body_name,
        "min": min_mm,
        "max": max_mm,
        "size": size_mm,
        "center": center_mm,
    }
    return json.dumps(result, indent=2)


def list_construction_planes(app, component_name=None, **kwargs):
    """List all user-created construction planes."""
    design = app.activeProduct
    root = design.rootComponent

    target_comp = root
    if component_name:
        for occ in root.allOccurrences:
            if occ.component.name == component_name:
                target_comp = occ.component
                break

    planes = target_comp.constructionPlanes
    result_list = []
    for i in range(planes.count):
        plane = planes.item(i)
        origin = plane.geometry.origin
        normal = plane.geometry.normal

        result_list.append({
            "index": i,
            "name": plane.name,
            "origin": {
                "x": round(cm_to_mm(origin.x), 4),
                "y": round(cm_to_mm(origin.y), 4),
                "z": round(cm_to_mm(origin.z), 4),
            },
            "normal": {
                "x": round(normal.x, 6),
                "y": round(normal.y, 6),
                "z": round(normal.z, 6),
            },
        })

    result = {
        "plane_count": len(result_list),
        "planes": result_list,
    }
    return json.dumps(result, indent=2)
