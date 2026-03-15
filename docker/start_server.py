"""Start the MCP server with mocked Fusion 360 API for introspection."""

import os
import sys

# Install adsk mocks before any other imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adsk_mock
adsk_mock.install()

# Add TextToModel to path
addin_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "TextToModel")
sys.path.insert(0, addin_dir)

import json
import logging
import threading

from mcp.server import ThreadedMCPServer
from mcp.sse_handler import SSEManager
from mcp.protocol import MCPProtocol
from bridge.executor import ToolExecutor
from tools.registry import ToolRegistry
from tools import register_all

logging.basicConfig(level=logging.INFO, format="[%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("TextToModel")

config_path = os.path.join(addin_dir, "config.json")
try:
    with open(config_path) as f:
        config = json.load(f)
except (IOError, json.JSONDecodeError):
    config = {}

registry = ToolRegistry()
register_all(registry)
logger.info("Registered %d tools", len(registry.list_tools()))

executor = ToolExecutor(registry, event_bridge=None)

protocol = MCPProtocol(
    server_name=config.get("server_name", "fusion360-mcp"),
    server_version=config.get("server_version", "1.0.0"),
    tool_executor=executor,
)

sse_manager = SSEManager()

host = "0.0.0.0"
port = int(os.environ.get("PORT", config.get("port", 13405)))

server = ThreadedMCPServer(host, port, protocol, sse_manager)
logger.info("MCP server starting on http://%s:%d (Docker introspection mode)", host, port)
server.serve_forever()
