"""Tool registry for managing MCP tool schemas and handlers."""

import logging

logger = logging.getLogger("TextToModel.registry")


class ToolRegistry:
    """Registry for MCP tools with schemas and handler functions."""

    def __init__(self):
        self._tools = {}

    def register(self, name, description, input_schema, handler):
        """Register a tool.

        Args:
            name: Unique tool name.
            description: Human-readable description.
            input_schema: JSON Schema dict for tool parameters.
            handler: Callable(app, **arguments) -> result string.
        """
        self._tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
            "handler": handler,
        }
        logger.debug("Registered tool: %s", name)

    def has_tool(self, name):
        """Check if a tool is registered."""
        return name in self._tools

    def list_tools(self):
        """Return list of tool schemas (without handlers) for MCP tools/list."""
        tools = []
        for tool in self._tools.values():
            tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["inputSchema"],
            })
        return tools

    def get_handler(self, name):
        """Get the handler function for a tool."""
        tool = self._tools.get(name)
        if tool:
            return tool["handler"]
        return None

    def call_tool(self, name, arguments):
        """Execute a tool and return MCP-formatted result.

        Args:
            name: Tool name.
            arguments: Dict of arguments.

        Returns:
            MCP tool result dict.
        """
        handler = self.get_handler(name)
        if handler is None:
            return {
                "content": [{"type": "text", "text": "Unknown tool: {}".format(name)}],
                "isError": True,
            }
        try:
            import adsk.core
            app = adsk.core.Application.get()
            result = handler(app, **arguments)

            if isinstance(result, dict) and "content" in result:
                return result

            if isinstance(result, str):
                return {"content": [{"type": "text", "text": result}]}

            import json
            return {"content": [{"type": "text", "text": json.dumps(result, default=str)}]}

        except Exception as e:
            logger.exception("Tool %s failed", name)
            return {
                "content": [{"type": "text", "text": "Error in {}: {}".format(name, str(e))}],
                "isError": True,
            }
