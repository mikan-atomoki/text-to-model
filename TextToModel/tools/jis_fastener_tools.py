"""JIS standard fastener creation tools for Fusion 360.

Creates parametric bolt, nut, screw, and washer models based on JIS dimensions.
Each fastener is created as a separate component for easy reuse and positioning.
"""

import math
from utils.geometry import mm_to_cm, point3d, deg_to_rad
from data import jis_threads, jis_bolts, jis_nuts, jis_screws, jis_washers


def register(registry):
    """Register all JIS fastener tools."""

    registry.register(
        name="create_jis_bolt",
        description="Create a JIS standard bolt (socket head cap screw B1176 or hexagon head B1180). The bolt is created as a new component at the specified position.",
        input_schema={
            "type": "object",
            "properties": {
                "size": {
                    "type": "string",
                    "description": "Thread size: M2, M2.5, M3, M4, M5, M6, M8, M10, M12",
                },
                "length": {
                    "type": "number",
                    "description": "Bolt length in mm (shank length, excluding head).",
                },
                "bolt_type": {
                    "type": "string",
                    "description": "Bolt type: 'socket_head' (B1176 六角穴付き) or 'hex_head' (B1180 六角)",
                    "enum": ["socket_head", "hex_head"],
                    "default": "socket_head",
                },
                "x": {"type": "number", "description": "Position X in mm", "default": 0},
                "y": {"type": "number", "description": "Position Y in mm", "default": 0},
                "z": {"type": "number", "description": "Position Z in mm", "default": 0},
            },
            "required": ["size", "length"],
        },
        handler=create_jis_bolt,
    )

    registry.register(
        name="create_jis_nut",
        description="Create a JIS B1181 hexagon nut. Created as a new component.",
        input_schema={
            "type": "object",
            "properties": {
                "size": {
                    "type": "string",
                    "description": "Thread size: M2 through M12.",
                },
                "style": {
                    "type": "string",
                    "description": "Nut style: 'style1' (standard) or 'thin'.",
                    "enum": ["style1", "thin"],
                    "default": "style1",
                },
                "x": {"type": "number", "description": "Position X in mm", "default": 0},
                "y": {"type": "number", "description": "Position Y in mm", "default": 0},
                "z": {"type": "number", "description": "Position Z in mm", "default": 0},
            },
            "required": ["size"],
        },
        handler=create_jis_nut,
    )

    registry.register(
        name="create_jis_screw",
        description="Create a JIS B1111 machine screw (pan head or flat head). Created as a new component.",
        input_schema={
            "type": "object",
            "properties": {
                "size": {
                    "type": "string",
                    "description": "Thread size: M2 through M10.",
                },
                "length": {
                    "type": "number",
                    "description": "Screw length in mm.",
                },
                "head_type": {
                    "type": "string",
                    "description": "Head type: 'pan' (なべ) or 'flat' (皿).",
                    "enum": ["pan", "flat"],
                    "default": "pan",
                },
                "x": {"type": "number", "description": "Position X in mm", "default": 0},
                "y": {"type": "number", "description": "Position Y in mm", "default": 0},
                "z": {"type": "number", "description": "Position Z in mm", "default": 0},
            },
            "required": ["size", "length"],
        },
        handler=create_jis_screw,
    )

    registry.register(
        name="create_jis_washer",
        description="Create a JIS B1256 plain washer. Created as a new component.",
        input_schema={
            "type": "object",
            "properties": {
                "size": {
                    "type": "string",
                    "description": "Nominal size: M2 through M12.",
                },
                "series": {
                    "type": "string",
                    "description": "Series: 'normal', 'small', or 'spring'.",
                    "enum": ["normal", "small", "spring"],
                    "default": "normal",
                },
                "x": {"type": "number", "description": "Position X in mm", "default": 0},
                "y": {"type": "number", "description": "Position Y in mm", "default": 0},
                "z": {"type": "number", "description": "Position Z in mm", "default": 0},
            },
            "required": ["size"],
        },
        handler=create_jis_washer,
    )


def _create_component(app, name):
    """Create a new component and return (occurrence, component)."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = name
    return occ, comp


def _create_hex_profile(sketch, across_flats, center_x=0, center_y=0):
    """Draw a regular hexagon on a sketch.

    Args:
        sketch: Sketch object.
        across_flats: Width across flats in mm.
        center_x, center_y: Center position in mm.
    """
    r = mm_to_cm(across_flats / 2.0)
    cx = mm_to_cm(center_x)
    cy = mm_to_cm(center_y)

    # Hexagon vertices (flat-to-flat orientation)
    import adsk.core
    lines = sketch.sketchCurves.sketchLines
    points = []
    for i in range(6):
        angle = math.radians(30 + 60 * i)
        x = cx + r / math.cos(math.radians(30)) * math.cos(angle)
        y = cy + r / math.cos(math.radians(30)) * math.sin(angle)
        points.append(adsk.core.Point3D.create(x, y, 0))

    for i in range(6):
        lines.addByTwoPoints(points[i], points[(i + 1) % 6])


def create_jis_bolt(app, size, length, bolt_type="socket_head", x=0, y=0, z=0, **kwargs):
    """Create a JIS bolt as a new component."""
    import adsk.core
    import adsk.fusion

    size = size.upper()
    thread = jis_threads.get_thread(size)

    occ, comp = _create_component(app, "{}_{}x{}_bolt".format(bolt_type, size, length))

    sketches = comp.sketches
    xy_plane = comp.xYConstructionPlane

    d = thread["d"]  # nominal diameter

    if bolt_type == "socket_head":
        head = jis_bolts.get_socket_head(size)
        dk = head["dk"]  # head diameter
        k = head["k"]    # head height
        s = head["s"]    # socket size

        # Sketch for head cylinder
        head_sketch = sketches.add(xy_plane)
        circles = head_sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0),
            mm_to_cm(dk / 2.0)
        )

        # Extrude head
        head_profile = head_sketch.profiles.item(0)
        extrudes = comp.features.extrudeFeatures
        head_input = extrudes.createInput(
            head_profile,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        head_input.setDistanceExtent(
            False,
            adsk.core.ValueInput.createByReal(mm_to_cm(k))
        )
        extrudes.add(head_input)

        # Hex socket cut
        socket_sketch = sketches.add(xy_plane)
        _create_hex_profile(socket_sketch, s)
        # Find the inner profile (hexagon)
        socket_profile = None
        for i in range(socket_sketch.profiles.count):
            p = socket_sketch.profiles.item(i)
            # Use the profile that is smaller (the hex profile)
            area = p.areaProperties().area
            if socket_profile is None or area < socket_profile.areaProperties().area:
                socket_profile = p

        if socket_profile:
            socket_input = extrudes.createInput(
                socket_profile,
                adsk.fusion.FeatureOperations.CutFeatureOperation
            )
            socket_input.setDistanceExtent(
                False,
                adsk.core.ValueInput.createByReal(mm_to_cm(k * 0.6))
            )
            extrudes.add(socket_input)

    else:  # hex_head
        head = jis_bolts.get_hex_head(size)
        s_af = head["s"]  # across flats
        k = head["k"]    # head height

        head_sketch = sketches.add(xy_plane)
        _create_hex_profile(head_sketch, s_af)

        head_profile = head_sketch.profiles.item(0)
        extrudes = comp.features.extrudeFeatures
        head_input = extrudes.createInput(
            head_profile,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        head_input.setDistanceExtent(
            False,
            adsk.core.ValueInput.createByReal(mm_to_cm(k))
        )
        extrudes.add(head_input)

    # Shank (threaded body)
    shank_sketch = sketches.add(xy_plane)
    shank_circles = shank_sketch.sketchCurves.sketchCircles
    shank_circles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0),
        mm_to_cm(d / 2.0)
    )
    shank_profile = shank_sketch.profiles.item(0)
    shank_input = extrudes.createInput(
        shank_profile,
        adsk.fusion.FeatureOperations.JoinFeatureOperation
    )
    shank_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(length)))
    shank_input.setDirectionFlip(True)
    extrudes.add(shank_input)

    # Move occurrence to position
    if x != 0 or y != 0 or z != 0:
        transform = occ.transform
        transform.translation = adsk.core.Vector3D.create(mm_to_cm(x), mm_to_cm(y), mm_to_cm(z))
        occ.transform = transform

    return "Created JIS {} bolt {} x {}mm at ({},{},{})".format(
        bolt_type, size, length, x, y, z)


def create_jis_nut(app, size, style="style1", x=0, y=0, z=0, **kwargs):
    """Create a JIS hexagon nut as a new component."""
    import adsk.core
    import adsk.fusion

    size = size.upper()
    thread = jis_threads.get_thread(size)
    nut = jis_nuts.get_nut(size, style)

    occ, comp = _create_component(app, "{}_{}_nut".format(size, style))

    sketches = comp.sketches
    xy_plane = comp.xYConstructionPlane

    # Hex body
    hex_sketch = sketches.add(xy_plane)
    _create_hex_profile(hex_sketch, nut["s"])

    hex_profile = hex_sketch.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    ext_input = extrudes.createInput(
        hex_profile,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_input.setDistanceExtent(
        False,
        adsk.core.ValueInput.createByReal(mm_to_cm(nut["m"]))
    )
    extrudes.add(ext_input)

    # Thread hole
    hole_sketch = sketches.add(xy_plane)
    hole_sketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0),
        mm_to_cm(thread["d"] / 2.0)
    )

    # Find the hole profile (circle only, not including the hex)
    hole_profile = hole_sketch.profiles.item(0)
    cut_input = extrudes.createInput(
        hole_profile,
        adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    cut_input.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
    extrudes.add(cut_input)

    if x != 0 or y != 0 or z != 0:
        transform = occ.transform
        transform.translation = adsk.core.Vector3D.create(mm_to_cm(x), mm_to_cm(y), mm_to_cm(z))
        occ.transform = transform

    return "Created JIS {} nut {} at ({},{},{})".format(style, size, x, y, z)


def create_jis_screw(app, size, length, head_type="pan", x=0, y=0, z=0, **kwargs):
    """Create a JIS machine screw as a new component."""
    import adsk.core
    import adsk.fusion

    size = size.upper()
    thread = jis_threads.get_thread(size)
    d = thread["d"]

    occ, comp = _create_component(app, "{}_{}x{}_screw".format(head_type, size, length))

    sketches = comp.sketches
    xy_plane = comp.xYConstructionPlane
    xz_plane = comp.xZConstructionPlane

    extrudes = comp.features.extrudeFeatures
    revolves = comp.features.revolveFeatures

    if head_type == "pan":
        head = jis_screws.get_pan_head(size)
        dk = head["dk"]
        k = head["k"]

        # Pan head profile (revolve a rounded rectangle shape)
        head_sketch = sketches.add(xz_plane)
        lines = head_sketch.sketchCurves.sketchLines
        arcs = head_sketch.sketchCurves.sketchArcs

        # Simple approximation: revolve a rectangle with rounded top
        r_head = mm_to_cm(dk / 2.0)
        h_head = mm_to_cm(k)

        p0 = adsk.core.Point3D.create(0, 0, 0)
        p1 = adsk.core.Point3D.create(r_head, 0, 0)
        p2 = adsk.core.Point3D.create(r_head, h_head * 0.7, 0)
        p3 = adsk.core.Point3D.create(r_head * 0.8, h_head, 0)
        p4 = adsk.core.Point3D.create(0, h_head, 0)

        lines.addByTwoPoints(p0, p1)
        lines.addByTwoPoints(p1, p2)
        lines.addByTwoPoints(p2, p3)
        lines.addByTwoPoints(p3, p4)
        lines.addByTwoPoints(p4, p0)

        head_profile = head_sketch.profiles.item(0)
        x_axis = comp.xConstructionAxis
        rev_input = revolves.createInput(
            head_profile, x_axis,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        rev_input.setAngleExtent(
            False,
            adsk.core.ValueInput.createByReal(math.pi * 2)
        )
        revolves.add(rev_input)

    else:  # flat head
        head = jis_screws.get_flat_head(size)
        dk = head["dk"]
        k = head["k"]

        # Countersunk head profile (revolve a triangle)
        head_sketch = sketches.add(xz_plane)
        lines = head_sketch.sketchCurves.sketchLines

        r_head = mm_to_cm(dk / 2.0)
        r_shank = mm_to_cm(d / 2.0)
        h_head = mm_to_cm(k)

        p0 = adsk.core.Point3D.create(0, 0, 0)
        p1 = adsk.core.Point3D.create(r_shank, 0, 0)
        p2 = adsk.core.Point3D.create(r_head, h_head, 0)
        p3 = adsk.core.Point3D.create(0, h_head, 0)

        lines.addByTwoPoints(p0, p1)
        lines.addByTwoPoints(p1, p2)
        lines.addByTwoPoints(p2, p3)
        lines.addByTwoPoints(p3, p0)

        head_profile = head_sketch.profiles.item(0)
        x_axis = comp.xConstructionAxis
        rev_input = revolves.createInput(
            head_profile, x_axis,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        rev_input.setAngleExtent(
            False,
            adsk.core.ValueInput.createByReal(math.pi * 2)
        )
        revolves.add(rev_input)

    # Shank
    shank_sketch = sketches.add(xy_plane)
    shank_sketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0),
        mm_to_cm(d / 2.0)
    )
    shank_profile = shank_sketch.profiles.item(0)
    shank_input = extrudes.createInput(
        shank_profile,
        adsk.fusion.FeatureOperations.JoinFeatureOperation
    )
    shank_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(length)))
    shank_input.setDirectionFlip(True)
    extrudes.add(shank_input)

    if x != 0 or y != 0 or z != 0:
        transform = occ.transform
        transform.translation = adsk.core.Vector3D.create(mm_to_cm(x), mm_to_cm(y), mm_to_cm(z))
        occ.transform = transform

    return "Created JIS {} head screw {} x {}mm at ({},{},{})".format(
        head_type, size, length, x, y, z)


def create_jis_washer(app, size, series="normal", x=0, y=0, z=0, **kwargs):
    """Create a JIS plain washer as a new component."""
    import adsk.core
    import adsk.fusion

    size = size.upper()
    washer = jis_washers.get_washer(size, series)

    occ, comp = _create_component(app, "{}_{}_washer".format(size, series))

    sketches = comp.sketches
    xy_plane = comp.xYConstructionPlane

    # Outer circle and inner circle
    sketch = sketches.add(xy_plane)
    circles = sketch.sketchCurves.sketchCircles
    center = adsk.core.Point3D.create(0, 0, 0)
    circles.addByCenterRadius(center, mm_to_cm(washer["d2"] / 2.0))
    circles.addByCenterRadius(center, mm_to_cm(washer["d1"] / 2.0))

    # Get the annular profile (ring between two circles)
    # The profile between two concentric circles is the ring
    profile = None
    for i in range(sketch.profiles.count):
        p = sketch.profiles.item(i)
        area = p.areaProperties().area
        # The ring profile area should be between the full circle and hole
        outer_area = math.pi * mm_to_cm(washer["d2"] / 2.0) ** 2
        inner_area = math.pi * mm_to_cm(washer["d1"] / 2.0) ** 2
        expected = outer_area - inner_area
        if abs(area - expected) / expected < 0.1:
            profile = p
            break

    if profile is None:
        # Fallback: use the largest profile that isn't the full circle
        profile = sketch.profiles.item(0)

    extrudes = comp.features.extrudeFeatures
    ext_input = extrudes.createInput(
        profile,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_input.setDistanceExtent(
        False,
        adsk.core.ValueInput.createByReal(mm_to_cm(washer["t"]))
    )
    extrudes.add(ext_input)

    if x != 0 or y != 0 or z != 0:
        transform = occ.transform
        transform.translation = adsk.core.Vector3D.create(mm_to_cm(x), mm_to_cm(y), mm_to_cm(z))
        occ.transform = transform

    return "Created JIS {} washer {} (d1={}, d2={}, t={}) at ({},{},{})".format(
        series, size, washer["d1"], washer["d2"], washer["t"], x, y, z)
