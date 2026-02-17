"""Import tools (SVG, DXF) for Fusion 360."""


def register(registry):
    """Register all import tools."""

    registry.register(
        name="import_svg",
        description=(
            "Import an SVG file as sketch curves onto a sketch plane. "
            "The SVG is imported as sketch geometry that can be extruded or used as profiles."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the SVG file.",
                },
                "plane": {
                    "type": "string",
                    "description": "Target plane: 'XY', 'XZ', or 'YZ'.",
                    "enum": ["XY", "XZ", "YZ"],
                    "default": "XY",
                },
                "x_offset": {
                    "type": "number",
                    "description": "X position offset in mm.",
                    "default": 0,
                },
                "y_offset": {
                    "type": "number",
                    "description": "Y position offset in mm.",
                    "default": 0,
                },
            },
            "required": ["file_path"],
        },
        handler=import_svg,
    )

    registry.register(
        name="import_dxf",
        description=(
            "Import a DXF file as sketch curves onto a sketch plane. "
            "The DXF is imported as 2D sketch geometry."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the DXF file.",
                },
                "plane": {
                    "type": "string",
                    "description": "Target plane: 'XY', 'XZ', or 'YZ'.",
                    "enum": ["XY", "XZ", "YZ"],
                    "default": "XY",
                },
            },
            "required": ["file_path"],
        },
        handler=import_dxf,
    )


def import_svg(app, file_path, plane="XY", x_offset=0, y_offset=0, **kwargs):
    """Import SVG as sketch curves."""
    import adsk.core
    import adsk.fusion
    import os
    from utils.geometry import get_plane, mm_to_cm

    if not os.path.isfile(file_path):
        raise ValueError("SVG file not found: {}".format(file_path))

    design = app.activeProduct
    root = design.rootComponent

    plane_obj = get_plane(app, plane)
    sketch = root.sketches.add(plane_obj)

    import_mgr = app.importManager
    svg_options = import_mgr.createSVGImportOptions(file_path, sketch)

    if x_offset != 0 or y_offset != 0:
        svg_options.position = adsk.core.Point2D.create(
            mm_to_cm(x_offset), mm_to_cm(y_offset))

    import_mgr.importToTarget(svg_options, sketch)

    return "Imported SVG '{}' onto {} plane -> sketch '{}' ({} curves, {} profiles)".format(
        os.path.basename(file_path), plane, sketch.name,
        sketch.sketchCurves.count, sketch.profiles.count)


def import_dxf(app, file_path, plane="XY", **kwargs):
    """Import DXF as sketch curves."""
    import adsk.core
    import adsk.fusion
    import os
    from utils.geometry import get_plane

    if not os.path.isfile(file_path):
        raise ValueError("DXF file not found: {}".format(file_path))

    design = app.activeProduct
    root = design.rootComponent

    plane_obj = get_plane(app, plane)

    import_mgr = app.importManager
    dxf_options = import_mgr.createDXF2DImportOptions(file_path, plane_obj)

    import_mgr.importToTarget(dxf_options, root)

    last_sketch = root.sketches.item(root.sketches.count - 1)
    return "Imported DXF '{}' onto {} plane -> sketch '{}' ({} curves, {} profiles)".format(
        os.path.basename(file_path), plane, last_sketch.name,
        last_sketch.sketchCurves.count, last_sketch.profiles.count)
