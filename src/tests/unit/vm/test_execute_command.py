"""Unit tests for vm.execute_command tool."""

from src.tests.unit.conftest import register_tools
import pytest

MODULE_PATH = "src.tools.vm.vm"

def _tool(monkeypatch, allow_write=True):
    tools = register_tools(monkeypatch, MODULE_PATH, xml_out="<ok/>", allow_write=allow_write)
    return tools["execute_command"]


def test_execute_command_write_disabled(monkeypatch):
    execute_command = _tool(monkeypatch, allow_write=False)
    out = execute_command("192.168.1.1", "echo hi")
    assert "Write operations are disabled" in out


def test_execute_command_write_enabled(monkeypatch):
    execute_command = _tool(monkeypatch, allow_write=True)
    out = execute_command("192.168.1.1", "echo hi")
    assert "echo hi" in out


def test_execute_command_invalid_ip(monkeypatch):
    execute_command = _tool(monkeypatch)
    out = execute_command("not_an_ip", "echo hi")
    assert "Invalid IP address" in out 