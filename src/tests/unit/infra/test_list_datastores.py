"""Unit tests for infra.list_datastores tool."""

import pytest

from src.tests.unit.conftest import register_infra_tools


def test_list_datastores_cli(monkeypatch):
    captured = {}

    def fake(cmd_parts, *a, **k):
        captured["cmd"] = cmd_parts
        return "<ds_pool/>"

    tools = register_infra_tools(monkeypatch, xml_out="<ds_pool/>")
    monkeypatch.setattr(
        "src.tools.infra.infra.execute_one_command", fake, raising=True
    )

    assert tools["list_datastores"]() == "<ds_pool/>"
    assert captured["cmd"] == ["onedatastore", "list", "--xml"] 