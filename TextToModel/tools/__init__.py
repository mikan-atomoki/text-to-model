"""Tool registration for all MCP tools."""

from tools import sketch_tools
from tools import feature_tools
from tools import modify_tools
from tools import pattern_tools
from tools import utility_tools
from tools import jis_fastener_tools
from tools import jis_hole_tools
from tools import mechanical_tools
from tools import construction_tools
from tools import inspect_tools
from tools import surface_tools
from tools import split_tools
from tools import transform_tools
from tools import import_tools
from tools import constraint_tools
from tools import appearance_tools


def register_all(registry):
    """Register all available tools with the registry."""
    sketch_tools.register(registry)
    feature_tools.register(registry)
    modify_tools.register(registry)
    pattern_tools.register(registry)
    utility_tools.register(registry)
    jis_fastener_tools.register(registry)
    jis_hole_tools.register(registry)
    mechanical_tools.register(registry)
    construction_tools.register(registry)
    inspect_tools.register(registry)
    surface_tools.register(registry)
    split_tools.register(registry)
    transform_tools.register(registry)
    import_tools.register(registry)
    constraint_tools.register(registry)
    appearance_tools.register(registry)
