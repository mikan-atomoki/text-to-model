"""Tool registration for all MCP tools."""

from tools import sketch_tools
from tools import feature_tools
from tools import modify_tools
from tools import pattern_tools
from tools import utility_tools
from tools import jis_fastener_tools
from tools import jis_hole_tools
from tools import mechanical_tools


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
