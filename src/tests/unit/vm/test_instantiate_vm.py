"""Unit tests for vm.instantiate_vm parameter validation."""

from src.tests.unit.conftest import register_tools

MODULE_PATH = "src.tools.vm.vm"

def _tool(monkeypatch):
    tools = register_tools(monkeypatch, MODULE_PATH, xml_out="ignored", allow_write=True)
    return tools["instantiate_vm"]


def test_instantiate_vm_invalid_numeric(monkeypatch):
    instantiate_vm = _tool(monkeypatch)
    # negative cpu
    out = instantiate_vm(template_id="1", vm_name="vm", cpu="-2")
    assert out.startswith("<error>")
    # non-digit memory
    out = instantiate_vm(template_id="1", vm_name="vm", memory="abc")
    assert out.startswith("<error>")
    # negative template id
    out = instantiate_vm(template_id="-1")
    assert out.startswith("<error>") 