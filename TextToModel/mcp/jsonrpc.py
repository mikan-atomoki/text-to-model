"""JSON-RPC 2.0 parsing and response building for MCP protocol."""

import json


JSONRPC_VERSION = "2.0"
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def parse_request(data):
    """Parse a JSON-RPC 2.0 request from bytes or string.

    Returns:
        dict with keys: jsonrpc, method, params, id
        On parse error, returns None.
    """
    try:
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        obj = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(obj, dict):
        return None

    return {
        "jsonrpc": obj.get("jsonrpc", ""),
        "method": obj.get("method", ""),
        "params": obj.get("params", {}),
        "id": obj.get("id"),
    }


def build_response(result, request_id):
    """Build a JSON-RPC 2.0 success response."""
    return json.dumps({
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "result": result,
    })


def build_error(code, message, request_id=None, data=None):
    """Build a JSON-RPC 2.0 error response."""
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return json.dumps({
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": error,
    })


def build_notification(method, params=None):
    """Build a JSON-RPC 2.0 notification (no id)."""
    msg = {
        "jsonrpc": JSONRPC_VERSION,
        "method": method,
    }
    if params is not None:
        msg["params"] = params
    return json.dumps(msg)
