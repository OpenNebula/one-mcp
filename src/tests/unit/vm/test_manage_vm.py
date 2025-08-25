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


def test_manage_vm_start_from_invalid_state(monkeypatch):
    dummy_xml = "<VM><STATE>3</STATE><LCM_STATE>3</LCM_STATE></VM>"  # RUNNING state
    tools = register_tools(monkeypatch, MODULE_PATH, xml_out=dummy_xml, allow_write=True)
    manage_vm = tools["manage_vm"]

    out = manage_vm(vm_id="10", operation="start")
    assert "<error>" in out
    assert "VM must be in STOPPED" in out


def test_manage_vm_stop_invalid_lcm_state(monkeypatch):
    dummy_xml = "<VM><STATE>3</STATE><LCM_STATE>1</LCM_STATE></VM>"  # RUNNING but LCM_STATE != 3
    tools = register_tools(monkeypatch, MODULE_PATH, xml_out=dummy_xml, allow_write=True)
    manage_vm = tools["manage_vm"]

    out = manage_vm(vm_id="5", operation="stop")
    assert "<error>" in out
    assert "VM must be in RUNNING state to stop" in out


def test_manage_vm_successful_terminate(monkeypatch):
    dummy_xml = "<VM><STATE>3</STATE><LCM_STATE>3</LCM_STATE></VM>"
    tools = register_tools(monkeypatch, MODULE_PATH, xml_out=dummy_xml, allow_write=True)

    manage_vm = tools["manage_vm"]
    out = manage_vm(vm_id="2", operation="terminate", hard=True)

    assert "<result>" in out
    assert "<vm_id>2</vm_id>" in out
    assert "<operation>terminate</operation>" in out
    assert "<hard>True</hard>" in out
    assert "VM terminate operation executed successfully" in out


def test_manage_vm_zero_id_spec_conformance(monkeypatch):
    """Test that manage_vm handles VM ID '0' according to spec (should be valid non-negative integer)."""
    manage_vm = _tool(monkeypatch)
    
    out = manage_vm(vm_id="0", operation="terminate")
    
    # Current implementation should accept "0" per the spec
    assert "<result>" in out
    assert "<vm_id>0</vm_id>" in out
    assert "<operation>terminate</operation>" in out


def test_manage_vm_xml_error_structure_invalid_id(monkeypatch):
    """Test that manage_vm returns properly structured error XML for invalid VM IDs."""
    manage_vm = _tool(monkeypatch)
    
    out = manage_vm(vm_id="invalid", operation="start")
    
    # Verify error XML structure
    assert out.startswith("<error>")
    assert "<message>" in out
    assert "</message>" in out
    assert "</error>" in out
    assert "vm_id must be a non-negative integer" in out


def test_manage_vm_xml_error_structure_invalid_operation(monkeypatch):
    """Test that manage_vm returns properly structured error XML for invalid operations."""
    manage_vm = _tool(monkeypatch)
    
    out = manage_vm(vm_id="1", operation="invalid_op")
    
    # Verify error XML structure
    assert out.startswith("<error>")
    assert "<message>" in out
    assert "</message>" in out
    assert "</error>" in out
    assert "Invalid operation 'invalid_op'" in out
    assert "Valid operations: start, stop, reboot, terminate" in out


def test_manage_vm_xml_success_structure(monkeypatch):
    """Test that manage_vm returns properly structured success XML."""
    manage_vm = _tool(monkeypatch)
    
    # Use terminate operation which is valid from any state including RUNNING (state 3)
    out = manage_vm(vm_id="42", operation="terminate", hard=True)
    
    # Verify success XML structure
    assert "<result>" in out
    assert "</result>" in out
    assert "<vm_id>42</vm_id>" in out
    assert "<operation>terminate</operation>" in out
    assert "<hard>True</hard>" in out
    assert "<message>" in out
    assert "</message>" in out
    assert "<command_output>" in out
    assert "</command_output>" in out
