"""Unit tests for infra.list_hosts filtering logic."""

import xml.etree.ElementTree as ET
import pytest
from types import SimpleNamespace

from src.tools.infra import infra as infra_module

# ----------------------------------------------------------------------------
# Helper: dummy MCP object to capture registered tool functions
# ----------------------------------------------------------------------------

class DummyMCP:
    """Minimal stub that imitates FastMCP just enough for unit-testing.

    FastMCP exposes a ``.tool`` decorator that registers a function.

    """

    def __init__(self):
        # Tools will be stored as {name: function}
        self.tools = {}

    def tool(self, *, name: str, description: str):  # noqa: D401
        """Return a *decorator* because Python expects it.

        Decorator chain behind the syntax:
            @mcp.tool(...)
            def func(): ...

        is equivalent to:
            def func(): ...
            func = mcp.tool(...)(func)

        Therefore ``dummy.tool`` must *return* another function that
        receives the new tool function, stores it, and then hands it
        back unchanged."""

        def decorator(fn):
            self.tools[name] = fn
            return fn

        return decorator


def _get_list_hosts_func(monkeypatch, hosts_xml: str):
    """Register tools into DummyMCP and patch execute_one_command output."""

    dummy = DummyMCP()

    # 1. Stub out execute_one_command **inside** infra.py so when the
    #    list_hosts function is defined, it will already reference the
    #    fake implementation that returns our XML fixture.  This avoids any
    #    real subprocess calls.
    monkeypatch.setattr(
        infra_module, "execute_one_command", lambda *args, **kwargs: hosts_xml
    )

    # 2. Run the normal registration code, which will create the list_hosts
    #    function and store it in dummy.tools via the decorator above.
    infra_module.register_tools(dummy)

    # 3. Return the plain Python function so tests can call it directly.
    return dummy.tools["list_hosts"]


# ----------------------------------------------------------------------------
# XML fixtures
# ----------------------------------------------------------------------------

HOSTS_XML = """<HOST_POOL>
    <HOST><ID>1</ID><CLUSTER_ID>100</CLUSTER_ID></HOST>
    <HOST><ID>2</ID><CLUSTER_ID>200</CLUSTER_ID></HOST>
</HOST_POOL>"""

INVALID_XML = "<broken>"

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_list_hosts_filters_by_cluster(monkeypatch):
    list_hosts = _get_list_hosts_func(monkeypatch, HOSTS_XML)

    output = list_hosts("100")
    root = ET.fromstring(output)
    hosts = root.findall("HOST")
    assert len(hosts) == 1
    assert hosts[0].find("ID").text == "1"


def test_list_hosts_no_hosts_found(monkeypatch):
    list_hosts = _get_list_hosts_func(monkeypatch, HOSTS_XML)

    output = list_hosts("999")
    assert output.startswith("<error>")
    assert "No hosts found" in output


def test_list_hosts_non_digit_cluster(monkeypatch):
    """Non-digit cluster_id should bypass filtering and return raw XML."""
    list_hosts = _get_list_hosts_func(monkeypatch, HOSTS_XML)
    output = list_hosts("abc")
    assert output == HOSTS_XML


def test_list_hosts_invalid_xml(monkeypatch):
    """Invalid XML should return <error>"""

    list_hosts = _get_list_hosts_func(monkeypatch, INVALID_XML)
    output = list_hosts("100")

    assert output.startswith("<error>")
    assert "Failed to parse" in output 