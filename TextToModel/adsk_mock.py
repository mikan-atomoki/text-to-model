"""Mock adsk modules for Docker introspection.

Provides stub adsk.core and adsk.fusion so the MCP server can start
and respond to introspection queries (initialize, tools/list) without
Fusion 360 installed.
"""

import sys
import types


def _create_mock_module(name):
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


class _MockApplication:
    @staticmethod
    def get():
        return _MockApplication()

    def registerCustomEvent(self, event_id):
        return _MockCustomEvent()

    def unregisterCustomEvent(self, event_id):
        pass

    def fireCustomEvent(self, event_id, payload):
        pass


class _MockCustomEvent:
    def add(self, handler):
        pass

    def remove(self, handler):
        pass


class _MockCustomEventHandler:
    def __init__(self):
        pass


class _MockCustomEventArgs:
    additionalInfo = "{}"


class _MockPoint3D:
    @staticmethod
    def create(x=0, y=0, z=0):
        return (x, y, z)


class _MockVector3D:
    @staticmethod
    def create(x=0, y=0, z=0):
        return (x, y, z)


def install():
    """Install mock adsk modules into sys.modules."""
    adsk = _create_mock_module("adsk")
    adsk_core = _create_mock_module("adsk.core")
    adsk_fusion = _create_mock_module("adsk.fusion")

    adsk.core = adsk_core
    adsk.fusion = adsk_fusion

    adsk_core.Application = _MockApplication
    adsk_core.CustomEventHandler = _MockCustomEventHandler
    adsk_core.CustomEventArgs = _MockCustomEventArgs
    adsk_core.Point3D = _MockPoint3D
    adsk_core.Vector3D = _MockVector3D
