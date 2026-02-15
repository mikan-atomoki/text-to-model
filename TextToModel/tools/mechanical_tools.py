"""Mechanical element tools (keyway, bearing hole, O-ring groove) for Fusion 360."""

import math
from utils.geometry import mm_to_cm, point3d, deg_to_rad
from data import jis_keyways, jis_bearings, jis_orings


def register(registry):
    """Register all mechanical element tools."""

    registry.register(
        name="create_keyway",
        description="Create a JIS B1301 parallel keyway (shaft keyway) on a cylindrical surface. Automatically determines key width and depth from shaft diameter.",
        input_schema={
            "type": "object",
            "properties": {
                "shaft_diameter": {
                    "type": "number",
                    "description": "Shaft diameter in mm (6-75mm).",
                },
                "key_length": {
                    "type": "number",
                    "description": "Key length in mm. If not specified, auto-selected from standard lengths.",
                },
                "position_z": {
                    "type": "number",
                    "description": "Z position (along shaft axis) for the keyway start in mm.",
                    "default": 0,
                },
                "body_name": {
                    "type": "string",
                    "description": "Name of the shaft body. Uses first body if not specified.",
                },
            },
            "required": ["shaft_diameter"],
        },
        handler=create_keyway,
    )

    registry.register(
        name="create_bearing_hole",
        description="Create a bearing bore hole sized to JIS B1520 standard bearing dimensions. Specify a bearing number (e.g., 6204) to get the correct bore dimensions.",
        input_schema={
            "type": "object",
            "properties": {
                "bearing_number": {
                    "type": "string",
                    "description": "Standard bearing number (e.g., '6204', '6305'). Either this or bore_diameter is required.",
                },
                "bore_diameter": {
                    "type": "number",
                    "description": "Alternatively, specify bore diameter in mm to auto-select a 6200 series bearing.",
                },
                "x": {"type": "number", "description": "Center X position in mm", "default": 0},
                "y": {"type": "number", "description": "Center Y position in mm", "default": 0},
                "body_name": {
                    "type": "string",
                    "description": "Target body name.",
                },
                "face_index": {
                    "type": "integer",
                    "description": "Face index for bore placement.",
                    "default": 0,
                },
            },
            "required": [],
        },
        handler=create_bearing_hole,
    )

    registry.register(
        name="create_oring_groove",
        description="Create a JIS B2401 O-ring groove on a cylindrical surface. Specify the O-ring number (e.g., P20, G50) for automatic groove dimensioning.",
        input_schema={
            "type": "object",
            "properties": {
                "oring_number": {
                    "type": "string",
                    "description": "O-ring designation (e.g., 'P10', 'P20', 'G50').",
                },
                "groove_type": {
                    "type": "string",
                    "description": "Groove type: 'shaft' (piston seal) or 'housing' (gland seal).",
                    "enum": ["shaft", "housing"],
                    "default": "shaft",
                },
                "position_z": {
                    "type": "number",
                    "description": "Z position along the axis for the groove center in mm.",
                    "default": 0,
                },
                "body_name": {
                    "type": "string",
                    "description": "Target body name.",
                },
            },
            "required": ["oring_number"],
        },
        handler=create_oring_groove,
    )


def create_keyway(app, shaft_diameter, key_length=None, position_z=0,
                   body_name=None, **kwargs):
    """Create a keyway on a shaft."""
    import adsk.core
    import adsk.fusion
    from utils.geometry import get_body_by_name

    design = app.activeProduct
    root = design.rootComponent

    # Get keyway dimensions
    kw = jis_keyways.get_keyway(shaft_diameter)
    b = kw["b"]    # key width
    t1 = kw["t1"]  # shaft keyway depth

    if key_length is None:
        key_length = jis_keyways.get_key_length(shaft_diameter)

    # Get target body
    if body_name:
        body = get_body_by_name(app, body_name)
        if not body:
            raise ValueError("Body '{}' not found.".format(body_name))
    else:
        if root.bRepBodies.count == 0:
            raise ValueError("No bodies in the design.")
        body = root.bRepBodies.item(0)

    # Create keyway sketch on XZ plane (assuming shaft along Z axis)
    xz_plane = root.xZConstructionPlane
    sketch = root.sketches.add(xz_plane)
    lines = sketch.sketchCurves.sketchLines

    # Keyway rectangle on the shaft surface
    r = shaft_diameter / 2.0
    half_b = b / 2.0

    # Rectangle at the top of the shaft
    x1 = mm_to_cm(-half_b)
    y1 = mm_to_cm(position_z)
    x2 = mm_to_cm(half_b)
    y2 = mm_to_cm(position_z + key_length)

    p1 = adsk.core.Point3D.create(x1, y1, 0)
    p2 = adsk.core.Point3D.create(x2, y2, 0)
    lines.addTwoPointRectangle(p1, p2)

    # Extrude cut from the top of the shaft downward
    profile = sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures

    # Cut to keyway depth from the shaft radius
    ext_input = extrudes.createInput(
        profile,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    # The cut depth is from the shaft surface inward
    cut_depth = t1
    ext_input.setDistanceExtent(
        False,
        adsk.core.ValueInput.createByReal(mm_to_cm(r))
    )
    # We need to position this correctly - cut from the top surface
    # Cut from Y+ direction
    ext_input.setDirectionFlip(False)

    # Set to start from offset
    start_from = adsk.fusion.FromEntityStartDefinition.create(
        root.xYConstructionPlane,
        adsk.core.ValueInput.createByReal(mm_to_cm(r - t1))
    )
    ext_input.startExtent = start_from
    ext_input.setDistanceExtent(
        False,
        adsk.core.ValueInput.createByReal(mm_to_cm(t1))
    )

    extrudes.add(ext_input)

    return "Created keyway on shaft d={}mm: width={}mm, depth={}mm, length={}mm at z={}mm".format(
        shaft_diameter, b, t1, key_length, position_z)


def create_bearing_hole(app, bearing_number=None, bore_diameter=None,
                         x=0, y=0, body_name=None, face_index=0, **kwargs):
    """Create a bearing bore hole."""
    import adsk.core
    import adsk.fusion
    from utils.geometry import get_body_by_name

    if bearing_number:
        bearing = jis_bearings.get_bearing(bearing_number)
    elif bore_diameter:
        bearing_number, bearing = jis_bearings.get_bearing_by_bore(bore_diameter)
    else:
        raise ValueError("Specify either bearing_number or bore_diameter.")

    D = bearing["D"]  # outer diameter (bore hole size for housing)
    B = bearing["B"]  # width (bore depth)

    design = app.activeProduct
    root = design.rootComponent

    # Get target face
    if body_name:
        body = get_body_by_name(app, body_name)
        if not body:
            raise ValueError("Body '{}' not found.".format(body_name))
    else:
        if root.bRepBodies.count == 0:
            raise ValueError("No bodies in the design.")
        body = root.bRepBodies.item(0)

    if face_index >= body.faces.count:
        raise ValueError("Face index {} out of range.".format(face_index))
    face = body.faces.item(face_index)

    # Create bore hole sketch on the face
    sketch = root.sketches.add(face)
    center = adsk.core.Point3D.create(mm_to_cm(x), mm_to_cm(y), 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(
        center, mm_to_cm(D / 2.0)
    )

    profile = sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures
    ext_input = extrudes.createInput(
        profile,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    ext_input.setDistanceExtent(
        False,
        adsk.core.ValueInput.createByReal(mm_to_cm(B))
    )
    ext_input.setDirectionFlip(True)
    extrudes.add(ext_input)

    return "Created bearing bore for {}: D={}mm, B={}mm at ({},{})".format(
        bearing_number, D, B, x, y)


def create_oring_groove(app, oring_number, groove_type="shaft",
                         position_z=0, body_name=None, **kwargs):
    """Create an O-ring groove on a cylindrical body."""
    import adsk.core
    import adsk.fusion
    from utils.geometry import get_body_by_name

    oring = jis_orings.get_oring(oring_number)
    groove = jis_orings.get_groove_dims(oring["w"], groove_type)

    d_oring = oring["d"]         # O-ring inner diameter
    w_oring = oring["w"]         # O-ring cross-section
    groove_width = groove["groove_width"]
    groove_depth = groove["groove_depth"]

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

    # For a shaft groove: cut a rectangular groove revolved around the shaft axis
    # The groove is at diameter d_oring (which sits on the shaft)

    if groove_type == "shaft":
        shaft_d = d_oring  # Approximate shaft diameter from O-ring ID
        groove_bottom_r = shaft_d / 2.0 - groove_depth
    else:
        shaft_d = d_oring + 2 * w_oring  # Approximate housing bore
        groove_bottom_r = shaft_d / 2.0 + groove_depth

    # Create groove profile on XZ plane and revolve
    xz_plane = root.xZConstructionPlane
    sketch = root.sketches.add(xz_plane)
    lines = sketch.sketchCurves.sketchLines

    half_w = groove_width / 2.0
    z_center = position_z

    if groove_type == "shaft":
        r_outer = mm_to_cm(shaft_d / 2.0)
        r_inner = mm_to_cm(groove_bottom_r)
        z1 = mm_to_cm(z_center - half_w)
        z2 = mm_to_cm(z_center + half_w)

        p1 = adsk.core.Point3D.create(r_inner, z1, 0)
        p2 = adsk.core.Point3D.create(r_outer, z1, 0)
        p3 = adsk.core.Point3D.create(r_outer, z2, 0)
        p4 = adsk.core.Point3D.create(r_inner, z2, 0)
    else:
        r_inner = mm_to_cm(shaft_d / 2.0)
        r_outer = mm_to_cm(groove_bottom_r)
        z1 = mm_to_cm(z_center - half_w)
        z2 = mm_to_cm(z_center + half_w)

        p1 = adsk.core.Point3D.create(r_inner, z1, 0)
        p2 = adsk.core.Point3D.create(r_outer, z1, 0)
        p3 = adsk.core.Point3D.create(r_outer, z2, 0)
        p4 = adsk.core.Point3D.create(r_inner, z2, 0)

    lines.addByTwoPoints(p1, p2)
    lines.addByTwoPoints(p2, p3)
    lines.addByTwoPoints(p3, p4)
    lines.addByTwoPoints(p4, p1)

    profile = sketch.profiles.item(0)
    revolves = root.features.revolveFeatures

    # Revolve around the Z axis (Y in XZ sketch) = the shaft centerline
    y_axis = root.yConstructionAxis
    rev_input = revolves.createInput(
        profile, y_axis,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    rev_input.setAngleExtent(
        False,
        adsk.core.ValueInput.createByReal(math.pi * 2)
    )
    revolves.add(rev_input)

    return "Created O-ring groove for {}: width={}mm, depth={}mm ({}) at z={}mm".format(
        oring_number, groove_width, groove_depth, groove_type, position_z)
