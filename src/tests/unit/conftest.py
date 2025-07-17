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

def register_infra_tools(monkeypatch: pytest.MonkeyPatch, xml_out: str = "<xml/>"):
    """Return a dict of infra tools with *execute_one_command* stubbed.

    Usage::

        tools = register_infra_tools(monkeypatch, "<xml/>")
        output = tools["list_clusters"]()
    """
    from src.tools.infra import infra as infra_module  # local import to avoid cycles

    dummy = DummyMCP()
    monkeypatch.setattr(
        infra_module,
        "execute_one_command",
        lambda *args, **kwargs: xml_out,
        raising=True,
    )
    infra_module.register_tools(dummy)
    return dummy.tools