"""Unit tests for infra.list_datastores tool."""

import pytest

from src.tests.unit.conftest import register_infra_tools


def test_list_datastores_cli(monkeypatch):
    captured = {}

    xml_out = "<DATASTORE_POOL></DATASTORE_POOL>"

    def fake(cmd_parts, *a, **k):
        captured["cmd"] = cmd_parts
        return xml_out

    tools = register_infra_tools(monkeypatch, xml_out=xml_out)
    monkeypatch.setattr(
        "src.tools.infra.infra.execute_one_command", fake, raising=True
    )

    assert tools["list_datastores"]() == xml_out
    assert captured["cmd"] == ["onedatastore", "list", "--xml"] 