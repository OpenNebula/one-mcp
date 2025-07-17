"""Unit tests for vm.get_vm_status tool."""

import pytest

from src.tests.unit.conftest import register_tools

MODULE_PATH = "src.tools.vm.vm"

def _setup(monkeypatch, xml_out="<vm></vm>"):
    tools = register_tools(monkeypatch, MODULE_PATH, xml_out=xml_out, allow_write=True)
    return tools["get_vm_status"]


def test_get_vm_status_invalid_id(monkeypatch):
    get_vm_status = _setup(monkeypatch)
    # non-numeric id -> error
    assert get_vm_status("abc").startswith("<error>")
    # negative integer -> error
    assert get_vm_status("-1").startswith("<error>")


def test_get_vm_status_happy_path(monkeypatch):
    captured = {}

    def fake(cmd_parts, *a, **k):
        captured["cmd"] = cmd_parts
        return "<VM id='1'/>"

    tools = register_tools(monkeypatch, MODULE_PATH, xml_out="<VM id='1'/>", allow_write=True)
    monkeypatch.setattr(
        "src.tools.vm.vm.execute_one_command", fake, raising=True
    )

    output = tools["get_vm_status"]("1")
    assert output == "<VM id='1'/>"
    assert captured["cmd"] == ["onevm", "show", "1", "--xml"] 