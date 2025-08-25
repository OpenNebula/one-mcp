"""Unit tests for infra.list_clusters tool."""

import pytest

from src.tests.unit.conftest import register_tools


def test_list_clusters_happy_path(monkeypatch):
    """Should forward correct command and return XML unchanged."""

    captured = {}

    xml_out = "<CLUSTER_POOL></CLUSTER_POOL>"

    def fake_exec(cmd_parts, *a, **k):
        # Record the command we got from list_clusters() so we can assert on it later
        captured["cmd"] = cmd_parts
        # Return dummy XML that the wrapper should pass through untouched
        return xml_out

    # Register tools with our spy
    tools = register_tools(monkeypatch, "src.tools.infra.infra", xml_out=xml_out)
    monkeypatch.setattr(
        "src.tools.infra.infra.execute_one_command", fake_exec, raising=True
    )

    output = tools["list_clusters"]()

    assert output == xml_out
    assert captured["cmd"] == ["onecluster", "list", "--xml"] 