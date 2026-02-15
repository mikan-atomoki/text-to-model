"""TextToModel - MCP Server add-in for Fusion 360.

Starts an HTTP/SSE server that exposes Fusion 360's API as MCP tools,
allowing Claude Desktop to directly control Fusion 360 for CAD operations.
"""

import json
import logging
import os
import sys
import threading

# Add add-in directory to sys.path for package imports
_ADDIN_DIR = os.path.dirname(os.path.abspath(__file__))
if _ADDIN_DIR not in sys.path:
    sys.path.insert(0, _ADDIN_DIR)

# Fusion 360 imports
import adsk.core
import adsk.fusion

# Local imports - use absolute imports from the add-in root
from mcp.server import ThreadedMCPServer
from mcp.sse_handler import SSEManager
from mcp.protocol import MCPProtocol
from bridge.event_bridge import EventBridge
from bridge.executor import ToolExecutor
from tools.registry import ToolRegistry
from tools import register_all

_app = None
_ui = None
_server = None
_server_thread = None
_event_bridge = None
_logger = None

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def _setup_logging(log_level="INFO"):
    """Configure logging for the add-in."""
    logger = logging.getLogger("TextToModel")
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "[%(name)s] %(levelname)s: %(message)s"
        ))
        logger.addHandler(handler)

    return logger


def _load_config():
    """Load configuration from config.json."""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return {
            "host": "127.0.0.1",
            "port": 13405,
            "server_name": "fusion360-mcp",
            "server_version": "1.0.0",
            "log_level": "INFO",
        }


def run(context):
    """Start the TextToModel MCP server add-in."""
    global _app, _ui, _server, _server_thread, _event_bridge, _logger

    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        config = _load_config()
        _logger = _setup_logging(config.get("log_level", "INFO"))
        _logger.info("TextToModel starting...")

        # Initialize tool registry and register all tools
        registry = ToolRegistry()
        register_all(registry)
        _logger.info("Registered %d tools", len(registry.list_tools()))

        # Initialize EventBridge for thread-safe Fusion API access
        _event_bridge = EventBridge()
        _event_bridge.register(_app)

        # Initialize tool executor with bridge
        executor = ToolExecutor(registry, _event_bridge)

        # Set up the bridge handler to use direct execution
        _event_bridge._handler.set_executor(executor.direct_execute)

        # Initialize MCP protocol
        protocol = MCPProtocol(
            server_name=config.get("server_name", "fusion360-mcp"),
            server_version=config.get("server_version", "1.0.0"),
            tool_executor=executor,
        )

        # Initialize SSE manager
        sse_manager = SSEManager()

        # Create and start HTTP server
        host = config.get("host", "127.0.0.1")
        port = config.get("port", 13405)

        _server = ThreadedMCPServer(host, port, protocol, sse_manager)

        _server_thread = threading.Thread(
            target=_server.serve_forever,
            name="TextToModel-MCPServer",
            daemon=True,
        )
        _server_thread.start()

        _logger.info("MCP server started on http://%s:%d", host, port)
        _ui.messageBox(
            "TextToModel MCP Server started on port {}.\n"
            "Connect Claude Desktop with mcp-remote.".format(port)
        )

    except Exception as e:
        if _ui:
            _ui.messageBox("TextToModel failed to start:\n{}".format(str(e)))
        raise


def stop(context):
    """Stop the TextToModel MCP server add-in."""
    global _server, _server_thread, _event_bridge, _logger

    try:
        if _logger:
            _logger.info("TextToModel stopping...")

        if _server:
            _server.shutdown_server()
            _server = None

        if _server_thread:
            _server_thread.join(timeout=5)
            _server_thread = None

        if _event_bridge:
            _event_bridge.unregister()
            _event_bridge = None

        if _logger:
            _logger.info("TextToModel stopped")

        if _ui:
            _ui.messageBox("TextToModel MCP Server stopped.")

    except Exception:
        if _ui:
            _ui.messageBox("TextToModel error during shutdown.")
