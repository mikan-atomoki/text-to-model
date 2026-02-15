"""Tool executor that bridges MCP tool calls to Fusion 360 main thread execution."""

import logging

logger = logging.getLogger("TextToModel.executor")


class ToolExecutor:
    """Executes MCP tool calls, optionally via EventBridge for thread safety."""

    def __init__(self, registry, event_bridge=None):
        """
        Args:
            registry: ToolRegistry instance with registered tools.
            event_bridge: EventBridge instance for main-thread execution.
                         If None, tools execute directly (for testing).
        """
        self.registry = registry
        self.event_bridge = event_bridge

    def list_tools(self):
        """Return the list of available tools in MCP schema format."""
        return self.registry.list_tools()

    def execute_tool(self, tool_name, arguments):
        """Execute a tool by name with the given arguments.

        If an EventBridge is configured, submits the call to the main thread.
        Otherwise, executes directly in the current thread.

        Returns:
            MCP tool result dict with 'content' and optional 'isError'.
        """
        if not self.registry.has_tool(tool_name):
            return {
                "content": [{"type": "text", "text": "Unknown tool: {}".format(tool_name)}],
                "isError": True,
            }

        if self.event_bridge is not None:
            return self._execute_via_bridge(tool_name, arguments)
        else:
            return self._execute_direct(tool_name, arguments)

    def _execute_via_bridge(self, tool_name, arguments):
        """Submit tool call to main thread via EventBridge and wait for result."""
        call = self.event_bridge.submit_call(tool_name, arguments)

        if not call.wait(timeout=self.event_bridge._timeout):
            return {
                "content": [{"type": "text", "text": "Tool execution timed out: {}".format(tool_name)}],
                "isError": True,
            }

        if call.error:
            return {
                "content": [{"type": "text", "text": "Error: {}".format(call.error)}],
                "isError": True,
            }

        return call.result

    def _execute_direct(self, tool_name, arguments):
        """Execute tool directly in the current thread."""
        return self.registry.call_tool(tool_name, arguments)

    def direct_execute(self, tool_name, arguments):
        """Direct execution method for use by EventBridge on the main thread.

        This is the function passed to BridgeEventHandler.set_executor().
        """
        return self.registry.call_tool(tool_name, arguments)
