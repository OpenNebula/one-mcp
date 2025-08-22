"""Unit tests for vm.list_vms validation."""

from src.tests.unit.conftest import register_tools

MODULE_PATH = "src.tools.vm.vm"

def _tool(monkeypatch):
    tools = register_tools(monkeypatch, MODULE_PATH, xml_out="<VM_POOL></VM_POOL>", allow_write=True)
    return tools["list_vms"]


def test_list_vms_invalid_filters(monkeypatch):
    list_vms = _tool(monkeypatch)

    # state non-digit -> error
    out = list_vms(state="abc", host_id=None, cluster_id=None)
    assert out.startswith("<error>")
    # host_id non-digit -> error
    out = list_vms(state=None, host_id="abc", cluster_id=None)
    assert out.startswith("<error>")
    # cluster_id non-digit -> error
    out = list_vms(state=None, host_id=None, cluster_id="xyz")
    assert out.startswith("<error>")

def test_list_vms_xml_success_structure(monkeypatch):
    """Test that list_vms returns properly structured XML for valid inputs."""
    expected_xml = "<VM_POOL><VM><ID>1</ID><STATE>3</STATE></VM></VM_POOL>"
    list_vms = _tool(monkeypatch)
    
    # Mock the execute_one_command to return specific XML
    import importlib
    module = importlib.import_module(MODULE_PATH)
    monkeypatch.setattr(module, "execute_one_command", lambda *a, **k: expected_xml, raising=True)
    
    out = list_vms()
    
    # Should return the XML with VM_POOL structure
    assert "<VM_POOL>" in out
    assert "</VM_POOL>" in out 