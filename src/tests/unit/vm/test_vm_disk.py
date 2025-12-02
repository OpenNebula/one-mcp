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
    
    # Register tools with allow_write=True
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
    
    # Register tools with allow_write=False
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

# --- vm_disk_attach ---

def test_vm_disk_attach_success_image(vm_tools):
    with patch('src.tools.vm.vm.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = vm_tools['vm_disk_attach'](vm_id="10", image_id="5")
        
        mock_exec.assert_called_once_with(["onevm", "disk-attach", "10", "--image", "5"])
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["vm_id"] == "10"
        assert result["operation"] == "disk-attach"

def test_vm_disk_attach_success_size(vm_tools):
    with patch('src.tools.vm.vm.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = vm_tools['vm_disk_attach'](vm_id="10", size="1024")
        
        mock_exec.assert_called_once_with(["onevm", "disk-attach", "10", "--size", "1024"])
        result = parse_result(result_xml)
        assert result["status"] == "success"

def test_vm_disk_attach_invalid_input(vm_tools):
    result_xml = vm_tools['vm_disk_attach'](vm_id="abc", image_id="5")
    assert "vm_id must be a non-negative integer" in result_xml
    
    result_xml = vm_tools['vm_disk_attach'](vm_id="10", image_id="abc")
    assert "image_id must be a non-negative integer" in result_xml
    
    result_xml = vm_tools['vm_disk_attach'](vm_id="10", size="abc")
    assert "size must be a non-negative integer" in result_xml
    
    result_xml = vm_tools['vm_disk_attach'](vm_id="10")
    assert "Either image_id or size must be provided" in result_xml

def test_vm_disk_attach_read_only(vm_tools_read_only):
    result_xml = vm_tools_read_only['vm_disk_attach'](vm_id="10", image_id="5")
    assert "Write operations are disabled" in result_xml

# --- vm_disk_detach ---

def test_vm_disk_detach_success(vm_tools):
    with patch('src.tools.vm.vm.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = vm_tools['vm_disk_detach'](vm_id="10", disk_id="1")
        
        mock_exec.assert_called_once_with(["onevm", "disk-detach", "10", "1"])
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["operation"] == "disk-detach"

def test_vm_disk_detach_invalid_input(vm_tools):
    result_xml = vm_tools['vm_disk_detach'](vm_id="abc", disk_id="1")
    assert "vm_id and disk_id must be non-negative integers" in result_xml

def test_vm_disk_detach_read_only(vm_tools_read_only):
    result_xml = vm_tools_read_only['vm_disk_detach'](vm_id="10", disk_id="1")
    assert "Write operations are disabled" in result_xml

# --- vm_disk_resize ---

def test_vm_disk_resize_success(vm_tools):
    with patch('src.tools.vm.vm.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = vm_tools['vm_disk_resize'](vm_id="10", disk_id="1", size="2048")
        
        mock_exec.assert_called_once_with(["onevm", "disk-resize", "10", "1", "2048"])
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["operation"] == "disk-resize"

def test_vm_disk_resize_invalid_input(vm_tools):
    result_xml = vm_tools['vm_disk_resize'](vm_id="10", disk_id="1", size="abc")
    assert "vm_id, disk_id and size must be non-negative integers" in result_xml

def test_vm_disk_resize_read_only(vm_tools_read_only):
    result_xml = vm_tools_read_only['vm_disk_resize'](vm_id="10", disk_id="1", size="2048")
    assert "Write operations are disabled" in result_xml
