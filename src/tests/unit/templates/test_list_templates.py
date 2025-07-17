"""Unit test for templates.list_templates tool."""

from src.tests.unit.conftest import register_tools


def test_list_templates_cli(monkeypatch):
    captured = {}
    xml_out = "<VMTEMPLATE_POOL></VMTEMPLATE_POOL>"

    def fake(cmd_parts, *a, **k):
        captured["cmd"] = cmd_parts
        return xml_out

    tools = register_tools(monkeypatch, "src.tools.templates.templates", xml_out=xml_out)
    monkeypatch.setattr(
        "src.tools.templates.templates.execute_one_command", fake, raising=True
    )

    assert tools["list_templates"]() == xml_out
    assert captured["cmd"] == ["onetemplate", "list", "--xml"]