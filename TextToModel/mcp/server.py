"""HTTP/SSE server for MCP protocol communication."""

import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

from mcp.sse_handler import SSEConnection, SSEManager
from mcp.jsonrpc import parse_request, build_error, PARSE_ERROR, INTERNAL_ERROR
from mcp.protocol import MCPProtocol

logger = logging.getLogger("TextToModel.server")


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP server endpoints."""

    def log_message(self, format, *args):
        logger.debug(format, *args)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            self._handle_health()
        elif path == "/sse":
            self._handle_sse()
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/messages" or path == "/message":
            self._handle_message(query)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

    def _handle_health(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        status = {
            "status": "ok",
            "server": self.server.mcp_protocol.server_name,
            "version": self.server.mcp_protocol.server_version,
        }
        self.wfile.write(json.dumps(status).encode("utf-8"))

    def _handle_sse(self):
        """Establish an SSE connection for a client."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._send_cors_headers()
        self.end_headers()

        sse_manager = self.server.sse_manager
        conn = SSEConnection(self.wfile)
        session_id = sse_manager.add_connection(conn)

        logger.info("SSE connection established: %s", session_id)

        # Use the Host header from the request so the endpoint origin matches
        # the client's connection origin (e.g. localhost vs 127.0.0.1).
        request_host = self.headers.get("Host", "{}:{}".format(
            self.server.host, self.server.server_port
        ))
        endpoint_url = "http://{}/messages?sessionId={}".format(
            request_host, session_id
        )
        conn.send_event(endpoint_url, event="endpoint")

        try:
            while not conn.closed and not self.server.shutdown_flag.is_set():
                self.server.shutdown_flag.wait(timeout=30)
                if not conn.closed:
                    conn.send_event("", event="ping")
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            sse_manager.remove_connection(session_id)
            logger.info("SSE connection closed: %s", session_id)

    def _handle_message(self, query):
        """Handle a JSON-RPC message from a client."""
        session_ids = query.get("sessionId", [])
        if not session_ids:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            error = build_error(PARSE_ERROR, "Missing sessionId parameter")
            self.wfile.write(error.encode("utf-8"))
            return

        session_id = session_ids[0]

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        request = parse_request(body)
        if request is None:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            error = build_error(PARSE_ERROR, "Parse error")
            self.wfile.write(error.encode("utf-8"))
            return

        logger.info("Received: method=%s id=%s", request["method"], request["id"])

        try:
            response = self.server.mcp_protocol.handle_request(request)
        except Exception as e:
            logger.exception("Error handling request")
            response = build_error(INTERNAL_ERROR, str(e), request.get("id"))

        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(b"ok")

        if response is not None:
            sse_manager = self.server.sse_manager
            sse_manager.send_to_session(session_id, response, event="message")


class ThreadedMCPServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTP server for MCP protocol."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, host, port, protocol, sse_manager):
        self.host = host
        self.mcp_protocol = protocol
        self.sse_manager = sse_manager
        self.shutdown_flag = threading.Event()
        super().__init__((host, port), MCPRequestHandler)

    def shutdown_server(self):
        """Gracefully shut down the server."""
        self.shutdown_flag.set()
        self.sse_manager.cleanup()
        self.shutdown()
