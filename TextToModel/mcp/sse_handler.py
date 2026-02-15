"""SSE (Server-Sent Events) connection management for MCP transport."""

import json
import threading
import uuid
import time


class SSEConnection:
    """Represents a single SSE client connection."""

    def __init__(self, wfile, session_id=None):
        self.wfile = wfile
        self.session_id = session_id or str(uuid.uuid4())
        self.lock = threading.Lock()
        self.closed = False

    def send_event(self, data, event=None, event_id=None):
        """Send an SSE event to the client.

        Args:
            data: String data to send.
            event: Optional event type.
            event_id: Optional event ID.
        """
        if self.closed:
            return False
        try:
            with self.lock:
                lines = []
                if event_id is not None:
                    lines.append("id: {}".format(event_id))
                if event is not None:
                    lines.append("event: {}".format(event))
                lines.append("data: {}".format(data))
                lines.append("")
                lines.append("")
                message = "\n".join(lines)
                self.wfile.write(message.encode("utf-8"))
                self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError, OSError):
            self.closed = True
            return False

    def close(self):
        self.closed = True


class SSEManager:
    """Manages multiple SSE connections."""

    def __init__(self):
        self._connections = {}
        self._lock = threading.Lock()

    def add_connection(self, connection):
        """Register a new SSE connection."""
        with self._lock:
            self._connections[connection.session_id] = connection
        return connection.session_id

    def remove_connection(self, session_id):
        """Remove and close an SSE connection."""
        with self._lock:
            conn = self._connections.pop(session_id, None)
            if conn:
                conn.close()

    def get_connection(self, session_id):
        """Get an SSE connection by session ID."""
        with self._lock:
            return self._connections.get(session_id)

    def send_to_session(self, session_id, data, event=None, event_id=None):
        """Send an event to a specific session."""
        conn = self.get_connection(session_id)
        if conn:
            return conn.send_event(data, event=event, event_id=event_id)
        return False

    def broadcast(self, data, event=None):
        """Send an event to all connected clients."""
        with self._lock:
            dead = []
            for sid, conn in self._connections.items():
                if not conn.send_event(data, event=event):
                    dead.append(sid)
            for sid in dead:
                self._connections.pop(sid, None)

    def get_session_ids(self):
        """Get all active session IDs."""
        with self._lock:
            return list(self._connections.keys())

    def cleanup(self):
        """Close and remove all connections."""
        with self._lock:
            for conn in self._connections.values():
                conn.close()
            self._connections.clear()
