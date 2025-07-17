"""Unit tests for vm.manage_vm validation."""

from src.tests.unit.conftest import register_tools

MODULE_PATH = "src.tools.vm.vm"

def _tool(monkeypatch):
    # patch execute_one_command to return minimal XML for status
    dummy_xml = """<VM><STATE>3</STATE><LCM_STATE>3</LCM_STATE></VM>"""
    tools = register_tools(monkeypatch, MODULE_PATH, xml_out=dummy_xml, allow_write=True)
    return tools["manage_vm"]


def test_manage_vm_invalid_id(monkeypatch):
    manage_vm = _tool(monkeypatch)
    out = manage_vm(vm_id="abc", operation="start")
    assert out.startswith("<error>")


def test_manage_vm_invalid_operation(monkeypatch):
    manage_vm = _tool(monkeypatch)
    out = manage_vm(vm_id="1", operation="hibernate")
    assert out.startswith("<error>") 