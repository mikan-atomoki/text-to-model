"""Utility tools for design info, export, undo, and code execution."""

import json
import os
from utils.geometry import cm_to_mm


def register(registry):
    """Register all utility tools."""

    registry.register(
        name="get_design_info",
        description="Get information about the current Fusion 360 design including document name, components, and bodies.",
        input_schema={
            "type": "object",
            "properties": {},
        },
        handler=get_design_info,
    )

    registry.register(
        name="list_bodies",
        description="List all bodies in the design or in a specific component.",
        input_schema={
            "type": "object",
            "properties": {
                "component_name": {
                    "type": "string",
                    "description": "Optional component name. Lists all bodies if not specified.",
                },
            },
        },
        handler=list_bodies,
    )

    registry.register(
        name="list_components",
        description="List all components in the design.",
        input_schema={
            "type": "object",
            "properties": {},
        },
        handler=list_components,
    )

    registry.register(
        name="get_parameters",
        description="List all user parameters in the design.",
        input_schema={
            "type": "object",
            "properties": {},
        },
        handler=get_parameters,
    )

    registry.register(
        name="set_parameter",
        description="Set or create a user parameter.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Parameter name."},
                "value": {"type": "number", "description": "Parameter value in mm."},
                "comment": {"type": "string", "description": "Optional comment."},
            },
            "required": ["name", "value"],
        },
        handler=set_parameter,
    )

    registry.register(
        name="undo",
        description="Undo the last operation in Fusion 360.",
        input_schema={
            "type": "object",
            "properties": {},
        },
        handler=undo,
    )

    registry.register(
        name="export_step",
        description="Export the design as a STEP file.",
        input_schema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Full file path for the STEP export (e.g. 'C:/output/part.step').",
                },
            },
            "required": ["file_path"],
        },
        handler=export_step,
    )

    registry.register(
        name="export_stl",
        description="Export the design or a specific body as an STL file.",
        input_schema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Full file path for the STL export (e.g. 'C:/output/part.stl').",
                },
                "body_name": {
                    "type": "string",
                    "description": "Optional body name. Exports first body if not specified.",
                },
                "refinement": {
                    "type": "string",
                    "description": "Mesh refinement: 'low', 'medium', 'high'.",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                },
            },
            "required": ["file_path"],
        },
        handler=export_stl,
    )

    registry.register(
        name="execute_code",
        description="Execute arbitrary Fusion 360 Python API code. Use this for operations not covered by other tools. The code has access to 'app' (Application) and 'design' (active Design).",
        input_schema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Has access to variables: app, design, root (rootComponent).",
                },
            },
            "required": ["code"],
        },
        handler=execute_code,
    )


def get_design_info(app, **kwargs):
    """Get design information."""
    design = app.activeProduct
    doc = app.activeDocument

    info = {
        "document_name": doc.name if doc else "Untitled",
        "design_type": str(design.designType) if design else "Unknown",
        "root_component": design.rootComponent.name if design else "N/A",
        "component_count": design.allComponents.count if design else 0,
        "body_count": design.rootComponent.bRepBodies.count if design else 0,
        "sketch_count": design.rootComponent.sketches.count if design else 0,
        "units": design.unitsManager.defaultLengthUnits if design else "N/A",
    }
    return json.dumps(info, indent=2)


def list_bodies(app, component_name=None, **kwargs):
    """List all bodies."""
    design = app.activeProduct
    bodies = []

    if component_name:
        for comp in design.allComponents:
            if comp.name == component_name:
                for i in range(comp.bRepBodies.count):
                    body = comp.bRepBodies.item(i)
                    bodies.append({
                        "name": body.name,
                        "component": comp.name,
                        "is_visible": body.isVisible,
                        "volume_cm3": body.volume if body.isSolid else None,
                        "face_count": body.faces.count,
                        "edge_count": body.edges.count,
                    })
                break
    else:
        for comp in design.allComponents:
            for i in range(comp.bRepBodies.count):
                body = comp.bRepBodies.item(i)
                bodies.append({
                    "name": body.name,
                    "component": comp.name,
                    "is_visible": body.isVisible,
                    "face_count": body.faces.count,
                    "edge_count": body.edges.count,
                })

    return json.dumps(bodies, indent=2)


def list_components(app, **kwargs):
    """List all components."""
    design = app.activeProduct
    components = []

    for i in range(design.allComponents.count):
        comp = design.allComponents.item(i)
        components.append({
            "name": comp.name,
            "body_count": comp.bRepBodies.count,
            "sketch_count": comp.sketches.count,
            "occurrence_count": comp.occurrences.count,
        })

    return json.dumps(components, indent=2)


def get_parameters(app, **kwargs):
    """List all user parameters."""
    design = app.activeProduct
    params = []

    for i in range(design.userParameters.count):
        param = design.userParameters.item(i)
        params.append({
            "name": param.name,
            "value": param.value,
            "expression": param.expression,
            "unit": param.unit,
            "comment": param.comment,
        })

    return json.dumps(params, indent=2)


def set_parameter(app, name, value, comment="", **kwargs):
    """Set or create a user parameter."""
    import adsk.core

    design = app.activeProduct
    user_params = design.userParameters

    existing = user_params.itemByName(name)
    if existing:
        existing.expression = str(value)
        if comment:
            existing.comment = comment
        return "Updated parameter '{}' = {}".format(name, value)
    else:
        val_input = adsk.core.ValueInput.createByReal(value * 0.1)
        user_params.add(name, val_input, "mm", comment or "")
        return "Created parameter '{}' = {} mm".format(name, value)


def undo(app, **kwargs):
    """Undo the last operation."""
    doc = app.activeDocument
    if doc:
        doc.undo()
        return "Undo performed."
    return "No active document to undo."


def export_step(app, file_path, **kwargs):
    """Export design as STEP."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    export_mgr = design.exportManager
    step_options = export_mgr.createSTEPExportOptions(file_path, root)
    export_mgr.execute(step_options)

    return "Exported STEP to: {}".format(file_path)


def export_stl(app, file_path, body_name=None, refinement="medium", **kwargs):
    """Export design or body as STL."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    export_mgr = design.exportManager

    if body_name:
        target = None
        for i in range(root.bRepBodies.count):
            body = root.bRepBodies.item(i)
            if body.name == body_name:
                target = body
                break
        if target is None:
            raise ValueError("Body '{}' not found.".format(body_name))
    else:
        if root.bRepBodies.count == 0:
            raise ValueError("No bodies in the design.")
        target = root.bRepBodies.item(0)

    stl_options = export_mgr.createSTLExportOptions(target, file_path)

    refinement_map = {
        "low": adsk.fusion.MeshRefinementSettings.MeshRefinementLow,
        "medium": adsk.fusion.MeshRefinementSettings.MeshRefinementMedium,
        "high": adsk.fusion.MeshRefinementSettings.MeshRefinementHigh,
    }
    stl_options.meshRefinement = refinement_map.get(
        refinement, adsk.fusion.MeshRefinementSettings.MeshRefinementMedium)

    export_mgr.execute(stl_options)

    return "Exported STL to: {} (refinement: {})".format(file_path, refinement)


def execute_code(app, code, **kwargs):
    """Execute arbitrary Python code with access to Fusion API."""
    import adsk.core
    import adsk.fusion

    design = app.activeProduct
    root = design.rootComponent

    local_vars = {
        "app": app,
        "design": design,
        "root": root,
        "adsk": __import__("adsk"),
        "result": None,
    }

    exec(code, {"__builtins__": __builtins__}, local_vars)

    result = local_vars.get("result")
    if result is not None:
        return str(result)
    return "Code executed successfully."
