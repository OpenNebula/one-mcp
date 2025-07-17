"""Unit tests for infra.list_images tool."""

import pytest

from src.tests.unit.conftest import register_infra_tools


def test_list_images_cli(monkeypatch):
    captured = {}

    def fake(cmd_parts, *a, **k):
        captured["cmd"] = cmd_parts
        return "<images/>"

    tools = register_infra_tools(monkeypatch, xml_out="<images/>")
    monkeypatch.setattr(
        "src.tools.infra.infra.execute_one_command", fake, raising=True
    )

    assert tools["list_images"]() == "<images/>"
    assert captured["cmd"] == ["oneimage", "list", "--xml"] 