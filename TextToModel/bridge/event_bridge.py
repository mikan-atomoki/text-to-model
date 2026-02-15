"""CustomEvent bridge for executing operations on Fusion 360's main thread.

Fusion 360's API is not thread-safe - all API calls must run on the main thread.
This module uses Fusion's CustomEvent mechanism to bridge calls from the HTTP
server's background threads to the main thread.
"""

import json
import logging
import threading
import uuid

import adsk.core

logger = logging.getLogger("TextToModel.bridge")

CUSTOM_EVENT_ID = "TextToModelBridgeEvent"

# Global list to prevent garbage collection of event handlers
_handlers = []


class PendingCall:
    """Represents a pending tool call waiting for main thread execution."""

    def __init__(self, tool_name, arguments):
        self.call_id = str(uuid.uuid4())
        self.tool_name = tool_name
        self.arguments = arguments
        self.result = None
        self.error = None
        self.event = threading.Event()

    def set_result(self, result):
        self.result = result
        self.event.set()

    def set_error(self, error):
        self.error = error
        self.event.set()

    def wait(self, timeout=60):
        """Wait for the result with timeout.

        Returns:
            True if completed, False if timed out.
        """
        return self.event.wait(timeout=timeout)


class BridgeEventHandler(adsk.core.CustomEventHandler):
    """Fusion 360 CustomEvent handler that runs on the main thread."""

    def __init__(self, bridge):
        super().__init__()
        self._bridge = bridge
        self._executor_fn = None

    def set_executor(self, executor_fn):
        self._executor_fn = executor_fn

    def notify(self, args):
        """Called by Fusion on the main thread when a CustomEvent fires."""
        try:
            payload = json.loads(args.additionalInfo)
            call_id = payload["call_id"]
            tool_name = payload["tool_name"]
            arguments = payload["arguments"]

            if self._executor_fn:
                self._bridge.execute_and_respond(
                    call_id, tool_name, arguments, self._executor_fn
                )
            else:
                call = self._bridge.get_pending_call(call_id)
                if call:
                    call.set_error("No executor configured")
                    self._bridge.remove_pending_call(call_id)
        except Exception as e:
            logger.exception("Error in BridgeEventHandler.notify")


class EventBridge:
    """Bridges tool calls from background threads to Fusion's main thread."""

    def __init__(self):
        self._pending = {}
        self._lock = threading.Lock()
        self._custom_event = None
        self._app = None
        self._handler = None
        self._timeout = 60

    def register(self, app):
        """Register the CustomEvent with Fusion 360.

        Args:
            app: adsk.core.Application instance.
        """
        self._app = app
        self._custom_event = app.registerCustomEvent(CUSTOM_EVENT_ID)
        self._handler = BridgeEventHandler(self)
        self._custom_event.add(self._handler)
        _handlers.append(self._handler)
        logger.info("EventBridge registered: %s", CUSTOM_EVENT_ID)

    def unregister(self):
        """Unregister the CustomEvent."""
        if self._app and self._custom_event:
            try:
                self._app.unregisterCustomEvent(CUSTOM_EVENT_ID)
            except Exception:
                pass
            self._custom_event = None
            if self._handler in _handlers:
                _handlers.remove(self._handler)
            self._handler = None
        with self._lock:
            for call in self._pending.values():
                call.set_error("Bridge shutting down")
            self._pending.clear()
        logger.info("EventBridge unregistered")

    def submit_call(self, tool_name, arguments):
        """Submit a tool call to be executed on the main thread.

        This method is called from background HTTP threads.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Dict of tool arguments.

        Returns:
            PendingCall object to wait on.
        """
        call = PendingCall(tool_name, arguments)
        with self._lock:
            self._pending[call.call_id] = call

        payload = json.dumps({
            "call_id": call.call_id,
            "tool_name": tool_name,
            "arguments": arguments,
        })
        self._app.fireCustomEvent(CUSTOM_EVENT_ID, payload)

        return call

    def get_pending_call(self, call_id):
        """Retrieve a pending call by ID."""
        with self._lock:
            return self._pending.get(call_id)

    def remove_pending_call(self, call_id):
        """Remove a completed pending call."""
        with self._lock:
            self._pending.pop(call_id, None)

    def execute_and_respond(self, call_id, tool_name, arguments, executor_fn):
        """Execute a tool call and set the result on the pending call.

        This method runs on the main thread via CustomEvent notification.
        """
        call = self.get_pending_call(call_id)
        if call is None:
            logger.warning("No pending call found: %s", call_id)
            return

        try:
            result = executor_fn(tool_name, arguments)
            call.set_result(result)
        except Exception as e:
            logger.exception("Error executing tool %s", tool_name)
            call.set_error(str(e))
        finally:
            self.remove_pending_call(call_id)
