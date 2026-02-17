"""Geometry helper utilities for Fusion 360 API.

Fusion 360 uses centimeters internally, while JIS standards use millimeters.
This module provides conversion helpers and Point3D/Vector3D factories.
"""

import math

try:
    import adsk.core
    HAS_FUSION = True
except ImportError:
    HAS_FUSION = False


def mm_to_cm(mm):
    """Convert millimeters to centimeters (Fusion internal unit)."""
    return mm * 0.1


def cm_to_mm(cm):
    """Convert centimeters to millimeters."""
    return cm * 10.0


def deg_to_rad(degrees):
    """Convert degrees to radians."""
    return degrees * math.pi / 180.0


def rad_to_deg(radians):
    """Convert radians to degrees."""
    return radians * 180.0 / math.pi


def point3d(x_mm=0, y_mm=0, z_mm=0):
    """Create a Point3D from mm coordinates (auto-converts to cm).

    Args:
        x_mm: X coordinate in mm.
        y_mm: Y coordinate in mm.
        z_mm: Z coordinate in mm.

    Returns:
        adsk.core.Point3D in cm.
    """
    if HAS_FUSION:
        return adsk.core.Point3D.create(
            mm_to_cm(x_mm), mm_to_cm(y_mm), mm_to_cm(z_mm)
        )
    return (mm_to_cm(x_mm), mm_to_cm(y_mm), mm_to_cm(z_mm))


def vector3d(x=0, y=0, z=0):
    """Create a Vector3D (unitless direction, no conversion).

    Args:
        x: X component.
        y: Y component.
        z: Z component.

    Returns:
        adsk.core.Vector3D.
    """
    if HAS_FUSION:
        return adsk.core.Vector3D.create(x, y, z)
    return (x, y, z)


def get_plane(app, plane_name):
    """Get a construction plane by name.

    Args:
        app: adsk.core.Application instance.
        plane_name: One of 'XY', 'XZ', 'YZ'.

    Returns:
        ConstructionPlane object.
    """
    design = app.activeProduct
    root = design.rootComponent

    planes = {
        "XY": root.xYConstructionPlane,
        "XZ": root.xZConstructionPlane,
        "YZ": root.yZConstructionPlane,
    }
    plane_name = plane_name.upper().replace(" ", "")
    plane = planes.get(plane_name)
    if plane is None:
        raise ValueError("Unknown plane: {}. Use XY, XZ, or YZ.".format(plane_name))
    return plane


def get_body_by_name(app, body_name, component_name=None):
    """Find a body by name, optionally within a specific component.

    Args:
        app: adsk.core.Application instance.
        body_name: Name of the body to find.
        component_name: Optional component name to search in.

    Returns:
        BRepBody or None.
    """
    design = app.activeProduct
    if component_name:
        for occ in design.rootComponent.allOccurrences:
            if occ.component.name == component_name:
                for body in occ.component.bRepBodies:
                    if body.name == body_name:
                        return body
    for body in design.rootComponent.bRepBodies:
        if body.name == body_name:
            return body
    return None


def get_edge_by_index(body, edge_index):
    """Get an edge from a body by its index.

    Args:
        body: BRepBody object.
        edge_index: Integer index into body.edges.

    Returns:
        BRepEdge object.
    """
    edges = body.edges
    if edge_index < 0 or edge_index >= edges.count:
        raise ValueError("Edge index {} out of range (0-{})".format(
            edge_index, edges.count - 1))
    return edges.item(edge_index)


def get_face_by_index(body, face_index):
    """Get a face from a body by its index.

    Args:
        body: BRepBody object.
        face_index: Integer index into body.faces.

    Returns:
        BRepFace object.
    """
    faces = body.faces
    if face_index < 0 or face_index >= faces.count:
        raise ValueError("Face index {} out of range (0-{})".format(
            face_index, faces.count - 1))
    return faces.item(face_index)


def cm2_to_mm2(cm2):
    """Convert square centimeters to square millimeters."""
    return cm2 * 100.0


def parse_entity_ref(app, ref_string):
    """Parse an entity reference string and return the Fusion object.

    Supported formats:
        'face:{body_name}:{face_index}' -> BRepFace
        'edge:{body_name}:{edge_index}' -> BRepEdge
        'plane:XY' / 'plane:XZ' / 'plane:YZ' -> ConstructionPlane

    Args:
        app: adsk.core.Application instance.
        ref_string: Entity reference string.

    Returns:
        The resolved Fusion 360 object.
    """
    parts = ref_string.split(":")
    kind = parts[0].lower()

    if kind == "face":
        if len(parts) != 3:
            raise ValueError("Face ref must be 'face:body_name:index', got '{}'".format(ref_string))
        body = get_body_by_name(app, parts[1])
        if not body:
            raise ValueError("Body '{}' not found.".format(parts[1]))
        idx = int(parts[2])
        return get_face_by_index(body, idx)

    elif kind == "edge":
        if len(parts) != 3:
            raise ValueError("Edge ref must be 'edge:body_name:index', got '{}'".format(ref_string))
        body = get_body_by_name(app, parts[1])
        if not body:
            raise ValueError("Body '{}' not found.".format(parts[1]))
        idx = int(parts[2])
        return get_edge_by_index(body, idx)

    elif kind == "plane":
        if len(parts) != 2:
            raise ValueError("Plane ref must be 'plane:XY|XZ|YZ', got '{}'".format(ref_string))
        return get_plane(app, parts[1])

    else:
        raise ValueError("Unknown entity ref type '{}'. Use face:, edge:, or plane:".format(kind))


def get_construction_plane(app, index, component_name=None):
    """Get a user-created construction plane by index.

    Args:
        app: adsk.core.Application instance.
        index: 0-based index into constructionPlanes collection.
        component_name: Optional component name.

    Returns:
        ConstructionPlane object.
    """
    design = app.activeProduct
    root = design.rootComponent

    target_comp = root
    if component_name:
        for occ in root.allOccurrences:
            if occ.component.name == component_name:
                target_comp = occ.component
                break

    planes = target_comp.constructionPlanes
    if index < 0 or index >= planes.count:
        raise ValueError("Construction plane index {} out of range (0-{})".format(
            index, planes.count - 1))
    return planes.item(index)
