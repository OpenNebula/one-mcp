import pytest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET
from src.tools.vm import vm

@pytest.fixture
def vm_tools():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    vm.register_tools(mcp_mock, allow_write=True)
    return tools

@pytest.fixture
def vm_tools_read_only():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    vm.register_tools(mcp_mock, allow_write=False)
    return tools

def parse_result(xml_str):
    root = ET.fromstring(xml_str)
    if root.tag == "error":
        return {"status": "error", "message": root.find("message").text}
    return {
        "status": "success",
        "vm_id": root.find("vm_id").text,
        "operation": root.find("operation").text,
        "command_output": root.find("command_output").text
    }

# --- vm_snapshot_create ---

def test_vm_snapshot_create_success(vm_tools):
    with patch('src.tools.vm.vm.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = vm_tools['vm_snapshot_create'](vm_id="10", name="snap1")
        
        mock_exec.assert_called_once_with(["onevm", "snapshot-create", "10", "snap1"])
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["operation"] == "snapshot-create"

def test_vm_snapshot_create_invalid_input(vm_tools):
    result_xml = vm_tools['vm_snapshot_create'](vm_id="abc", name="snap1")
    assert "vm_id must be a non-negative integer" in result_xml

def test_vm_snapshot_create_read_only(vm_tools_read_only):
    result_xml = vm_tools_read_only['vm_snapshot_create'](vm_id="10", name="snap1")
    assert "Write operations are disabled" in result_xml

# --- vm_snapshot_revert ---

def test_vm_snapshot_revert_success(vm_tools):
    with patch('src.tools.vm.vm.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = vm_tools['vm_snapshot_revert'](vm_id="10", snapshot_id="1")
        
        mock_exec.assert_called_once_with(["onevm", "snapshot-revert", "10", "1"])
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["operation"] == "snapshot-revert"

def test_vm_snapshot_revert_invalid_input(vm_tools):
    result_xml = vm_tools['vm_snapshot_revert'](vm_id="abc", snapshot_id="1")
    assert "vm_id and snapshot_id must be non-negative integers" in result_xml

def test_vm_snapshot_revert_read_only(vm_tools_read_only):
    result_xml = vm_tools_read_only['vm_snapshot_revert'](vm_id="10", snapshot_id="1")
    assert "Write operations are disabled" in result_xml
