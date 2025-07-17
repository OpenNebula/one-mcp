"""Unit tests for infra.list_networks tool."""

import pytest

from src.tests.unit.conftest import register_infra_tools


def test_list_networks_cli(monkeypatch):
    captured = {}

    def fake(cmd_parts, *a, **k):
        captured["cmd"] = cmd_parts
        return "<vnet_pool/>"

    tools = register_infra_tools(monkeypatch, xml_out="<vnet_pool/>")
    monkeypatch.setattr(
        "src.tools.infra.infra.execute_one_command", fake, raising=True
    )

    assert tools["list_networks"]() == "<vnet_pool/>"
    assert captured["cmd"] == ["onevnet", "list", "--xml"] 