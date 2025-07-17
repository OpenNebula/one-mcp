"""Unit tests for infra.list_clusters tool."""

import pytest

from src.tests.unit.conftest import register_infra_tools


def test_list_clusters_happy_path(monkeypatch):
    """Should forward correct command and return XML unchanged."""

    captured = {}

    def fake_exec(cmd_parts, *a, **k):  # noqa: D401 – test helper
        captured["cmd"] = cmd_parts
        return "<cluster_pool/>"

    # Register tools with our spy
    tools = register_infra_tools(monkeypatch, xml_out="<cluster_pool/>")
    monkeypatch.setattr(
        "src.tools.infra.infra.execute_one_command", fake_exec, raising=True
    )

    output = tools["list_clusters"]()

    assert output == "<cluster_pool/>"
    assert captured["cmd"] == ["onecluster", "list", "--xml"] 