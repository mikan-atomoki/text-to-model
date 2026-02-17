"""Appearance and naming tools for Fusion 360."""

from utils.geometry import get_body_by_name


def register(registry):
    """Register all appearance tools."""

    registry.register(
        name="set_body_color",
        description="Set the color (appearance) of a body using RGB values.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {"type": "string", "description": "Name of the body."},
                "red": {"type": "integer", "description": "Red component (0-255).", "minimum": 0, "maximum": 255},
                "green": {"type": "integer", "description": "Green component (0-255).", "minimum": 0, "maximum": 255},
                "blue": {"type": "integer", "description": "Blue component (0-255).", "minimum": 0, "maximum": 255},
                "opacity": {
                    "type": "number",
                    "description": "Opacity (0.0 = transparent, 1.0 = opaque).",
                    "default": 1.0,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "component_name": {"type": "string", "description": "Optional component name."},
            },
            "required": ["body_name", "red", "green", "blue"],
        },
        handler=set_body_color,
    )

    registry.register(
        name="rename_body",
        description="Rename a body.",
        input_schema={
            "type": "object",
            "properties": {
                "body_name": {"type": "string", "description": "Current name of the body."},
                "new_name": {"type": "string", "description": "New name for the body."},
                "component_name": {"type": "string", "description": "Optional component name."},
            },
            "required": ["body_name", "new_name"],
        },
        handler=rename_body,
    )


def set_body_color(app, body_name, red, green, blue, opacity=1.0,
                    component_name=None, **kwargs):
    """Set body color via custom appearance."""
    import adsk.core
    import adsk.fusion

    body = get_body_by_name(app, body_name, component_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    design = app.activeProduct

    appearance_name = "TextToModel_{}_{}_{}".format(red, green, blue)

    existing = design.appearances.itemByName(appearance_name)
    if existing:
        body.appearance = existing
    else:
        lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
        if not lib:
            libs = app.materialLibraries
            if libs.count > 0:
                lib = libs.item(0)
            else:
                raise ValueError("No appearance libraries available.")

        base_appearance = None
        for i in range(lib.appearances.count):
            a = lib.appearances.item(i)
            if "Generic" in a.name or "Plastic" in a.name:
                base_appearance = a
                break
        if not base_appearance:
            base_appearance = lib.appearances.item(0)

        new_appearance = design.appearances.addByCopy(base_appearance, appearance_name)

        color_prop = None
        for prop in new_appearance.appearanceProperties:
            if prop.name == "Color" and hasattr(prop, "value"):
                color_prop = prop
                break

        if color_prop:
            color_prop.value = adsk.core.Color.create(red, green, blue, int(opacity * 255))

        body.appearance = new_appearance

    return "Set '{}' color to RGB({}, {}, {}) opacity={}".format(
        body_name, red, green, blue, opacity)


def rename_body(app, body_name, new_name, component_name=None, **kwargs):
    """Rename a body."""
    body = get_body_by_name(app, body_name, component_name)
    if not body:
        raise ValueError("Body '{}' not found.".format(body_name))

    old_name = body.name
    body.name = new_name
    return "Renamed body '{}' -> '{}'".format(old_name, new_name)
