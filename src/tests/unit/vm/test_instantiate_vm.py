"""Unit tests for vm.instantiate_vm parameter validation."""

from src.tests.unit.conftest import register_tools

MODULE_PATH = "src.tools.vm.vm"

def _tool(monkeypatch):
    tools = register_tools(monkeypatch, MODULE_PATH, xml_out="ignored", allow_write=True)
    return tools["instantiate_vm"]


def test_instantiate_vm_invalid_template_id(monkeypatch):
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

    # non-digit template id
    out = instantiate_vm(template_id="abc")
    assert out.startswith("<error>")


def test_instantiate_vm_zero_template_id_spec_conformance(monkeypatch):
    """Test that instantiate_vm handles template_id '0' according to spec (should be valid non-negative integer)."""
    instantiate_vm = _tool(monkeypatch)
    
    # Mock the execute_one_command to simulate successful VM creation
    import importlib
    module = importlib.import_module(MODULE_PATH)
    
    def mock_execute(cmd_parts):
        if "instantiate" in cmd_parts:
            return "VM ID: 100"
        else:  # onevm show command
            return "<VM><ID>100</ID><STATE>1</STATE></VM>"
    
    monkeypatch.setattr(module, "execute_one_command", mock_execute, raising=True)
    
    out = instantiate_vm(template_id="0")
    
    # Should succeed since "0" is a valid non-negative integer
    assert out == "<VM><ID>100</ID><STATE>1</STATE></VM>"