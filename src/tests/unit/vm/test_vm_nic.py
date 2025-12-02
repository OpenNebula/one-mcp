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

# --- vm_nic_attach ---

def test_vm_nic_attach_success(vm_tools):
    with patch('src.tools.vm.vm.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = vm_tools['vm_nic_attach'](vm_id="10", network_id="net1")
        
        mock_exec.assert_called_once_with(["onevm", "nic-attach", "10", "--network", "net1"])
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["operation"] == "nic-attach"

def test_vm_nic_attach_with_ip(vm_tools):
    with patch('src.tools.vm.vm.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = vm_tools['vm_nic_attach'](vm_id="10", network_id="net1", ip="192.168.1.10")
        
        mock_exec.assert_called_once_with(["onevm", "nic-attach", "10", "--network", "net1", "--ip", "192.168.1.10"])
        result = parse_result(result_xml)
        assert result["status"] == "success"

def test_vm_nic_attach_invalid_input(vm_tools):
    result_xml = vm_tools['vm_nic_attach'](vm_id="abc", network_id="net1")
    assert "vm_id must be a non-negative integer" in result_xml
    
    result_xml = vm_tools['vm_nic_attach'](vm_id="10", network_id="net1", ip="invalid-ip")
    assert "Invalid IP address" in result_xml

def test_vm_nic_attach_read_only(vm_tools_read_only):
    result_xml = vm_tools_read_only['vm_nic_attach'](vm_id="10", network_id="net1")
    assert "Write operations are disabled" in result_xml

# --- vm_nic_detach ---

def test_vm_nic_detach_success(vm_tools):
    with patch('src.tools.vm.vm.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = vm_tools['vm_nic_detach'](vm_id="10", nic_id="1")
        
        mock_exec.assert_called_once_with(["onevm", "nic-detach", "10", "1"])
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["operation"] == "nic-detach"

def test_vm_nic_detach_invalid_input(vm_tools):
    result_xml = vm_tools['vm_nic_detach'](vm_id="abc", nic_id="1")
    assert "vm_id and nic_id must be non-negative integers" in result_xml

def test_vm_nic_detach_read_only(vm_tools_read_only):
    result_xml = vm_tools_read_only['vm_nic_detach'](vm_id="10", nic_id="1")
    assert "Write operations are disabled" in result_xml
