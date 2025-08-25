"""Unit tests for infra.list_networks tool."""

import pytest

from src.tests.unit.conftest import register_tools


def test_list_networks_cli(monkeypatch):
    captured = {}

    xml_out = "<VNET_POOL></VNET_POOL>"

    def fake(cmd_parts, *a, **k):
        captured["cmd"] = cmd_parts
        return xml_out

    tools = register_tools(monkeypatch, "src.tools.infra.infra", xml_out=xml_out)
    monkeypatch.setattr(
        "src.tools.infra.infra.execute_one_command", fake, raising=True
    )

    assert tools["list_networks"]() == xml_out
    assert captured["cmd"] == ["onevnet", "list", "--xml"]