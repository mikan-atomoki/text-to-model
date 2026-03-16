"""Stdio MCP server for Docker introspection.

Reads JSON-RPC from stdin, writes responses to stdout.
Used by Glama to run introspection queries in Docker.
"""

import json
import os
import sys

# Install adsk mocks before any other imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adsk_mock
adsk_mock.install()

import logging

from mcp.protocol import MCPProtocol
from mcp.jsonrpc import parse_request
from bridge.executor import ToolExecutor
from tools.registry import ToolRegistry
from tools import register_all

# Log to stderr so stdout stays clean for JSON-RPC
logging.basicConfig(level=logging.INFO, format="[%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("TextToModel")

registry = ToolRegistry()
register_all(registry)
logger.info("Registered %d tools", len(registry.list_tools()))

executor = ToolExecutor(registry, event_bridge=None)

config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
try:
    with open(config_path) as f:
        config = json.load(f)
except (IOError, json.JSONDecodeError):
    config = {}

protocol = MCPProtocol(
    server_name=config.get("server_name", "fusion360-mcp"),
    server_version=config.get("server_version", "1.0.0"),
    tool_executor=executor,
)

logger.info("Stdio MCP server ready")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        request = parse_request(line.encode("utf-8"))
        if request is None:
            continue

        logger.info("Received: method=%s id=%s", request.get("method"), request.get("id"))

        response = protocol.handle_request(request)
        if response is not None:
            sys.stdout.write(response + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
