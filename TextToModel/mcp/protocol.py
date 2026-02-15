"""MCP protocol method dispatch (initialize, tools/list, tools/call, etc.)."""

import logging
import traceback

from mcp.jsonrpc import build_response, build_error, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL_ERROR

logger = logging.getLogger("TextToModel.protocol")

MCP_PROTOCOL_VERSION = "2024-11-05"


class MCPProtocol:
    """Handles MCP protocol messages and dispatches to appropriate handlers."""

    def __init__(self, server_name, server_version, tool_executor=None):
        self.server_name = server_name
        self.server_version = server_version
        self.tool_executor = tool_executor
        self._initialized = False

        self._handlers = {
            "initialize": self._handle_initialize,
            "initialized": self._handle_initialized,
            "ping": self._handle_ping,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "prompts/list": self._handle_prompts_list,
        }

    def handle_request(self, request):
        """Dispatch a parsed JSON-RPC request to the appropriate handler.

        Returns:
            JSON string response, or None for notifications.
        """
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")

        handler = self._handlers.get(method)
        if handler is None:
            logger.warning("Unknown method: %s", method)
            if request_id is not None:
                return build_error(METHOD_NOT_FOUND, "Method not found: {}".format(method), request_id)
            return None

        try:
            result = handler(params)
        except Exception as e:
            logger.exception("Error in handler for %s", method)
            if request_id is not None:
                return build_error(INTERNAL_ERROR, str(e), request_id)
            return None

        if request_id is not None:
            return build_response(result, request_id)
        return None

    def _handle_initialize(self, params):
        self._initialized = True
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
            },
            "serverInfo": {
                "name": self.server_name,
                "version": self.server_version,
            },
        }

    def _handle_initialized(self, params):
        logger.info("Client confirmed initialization")
        return {}

    def _handle_ping(self, params):
        return {}

    def _handle_tools_list(self, params):
        if self.tool_executor is None:
            return {"tools": []}
        tools = self.tool_executor.list_tools()
        return {"tools": tools}

    def _handle_tools_call(self, params):
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ValueError("Missing tool name")

        if self.tool_executor is None:
            return {
                "content": [{"type": "text", "text": "No tool executor configured"}],
                "isError": True,
            }

        try:
            result = self.tool_executor.execute_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.exception("Tool execution error: %s", tool_name)
            return {
                "content": [{"type": "text", "text": "Error: {}".format(str(e))}],
                "isError": True,
            }

    def _handle_resources_list(self, params):
        return {"resources": []}

    def _handle_resources_read(self, params):
        uri = params.get("uri", "")
        return {
            "contents": [{
                "uri": uri,
                "mimeType": "text/plain",
                "text": "Resource not found: {}".format(uri),
            }],
        }

    def _handle_prompts_list(self, params):
        return {"prompts": []}
