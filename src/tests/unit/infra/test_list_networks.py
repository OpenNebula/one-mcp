"""Smoke test placeholder for infra.list_networks tool."""

import pytest
from src.tools.infra import infra as infra_module
from src.tests.unit.conftest import DummyMCP


def _register(monkeypatch, xml_out="<vnet_pool/>"):
    dummy = DummyMCP()
    monkeypatch.setattr(infra_module, "execute_one_command", lambda *a, **k: xml_out)
    infra_module.register_tools(dummy)
    return dummy.tools


@pytest.mark.skip("placeholder – extend with real assertions later")
def test_list_networks_smoke(monkeypatch):
    tools = _register(monkeypatch)
    assert "list_networks" in tools
    assert tools["list_networks"]() == "<vnet_pool/>" 