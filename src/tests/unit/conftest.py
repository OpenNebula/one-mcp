"""Shared fixtures and helpers for unit tests."""

from typing import Callable
import pytest


class DummyMCP:
    """Minimal stub that mimics FastMCP's ``.tool`` decorator.

    It collects registered tools into ``self.tools`` so that unit tests can
    call them directly without spinning up the real server object.
    """

    def __init__(self) -> None:
        self.tools: dict[str, Callable] = {}

    def tool(self, *, name: str, description: str):  # noqa: D401
        """Return a decorator that stores *fn* under the given *name*."""

        def decorator(fn):
            self.tools[name] = fn
            return fn

        return decorator


# ---------------------------------------------------------------------------
# Helper to register infra tools quickly
# ---------------------------------------------------------------------------

def register_tools(monkeypatch, module_path: str, xml_out: str = "<xml/>"):
    """
    Register all tools defined in *module_path* with a DummyMCP instance,
    while patching that module's ``execute_one_command`` to return *xml_out*.

    Example:
        tools = register_tools(monkeypatch, "src.tools.infra.infra")
        tools = register_tools(monkeypatch, "src.tools.templates.templates")
    """
    import importlib

    module = importlib.import_module(module_path)

    dummy = DummyMCP()
    monkeypatch.setattr(module, "execute_one_command",
                        lambda *a, **k: xml_out,
                        raising=True)
    module.register_tools(dummy)
    return dummy.tools