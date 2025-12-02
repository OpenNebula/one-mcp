import pytest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET
from src.tools.infra import infra

@pytest.fixture
def infra_tools():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    infra.register_tools(mcp_mock, allow_write=True)
    return tools

@pytest.fixture
def infra_tools_read_only():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    infra.register_tools(mcp_mock, allow_write=False)
    return tools

def parse_result(xml_str):
    root = ET.fromstring(xml_str)
    if root.tag == "error":
        return {"status": "error", "message": root.find("message").text}
    result = {"status": "success"}
    if root.find("vnet_id") is not None:
        result["vnet_id"] = root.find("vnet_id").text
    if root.find("reservation_id") is not None:
        result["reservation_id"] = root.find("reservation_id").text
    return result

# --- create_vnet ---

def test_create_vnet_success(infra_tools):
    with patch('src.tools.infra.infra.execute_one_command') as mock_exec, \
         patch('tempfile.NamedTemporaryFile') as mock_temp, \
         patch('os.path.exists', return_value=True), \
         patch('os.remove'):
        
        mock_exec.return_value = "ID: 10"
        
        mock_file = MagicMock()
        mock_temp.return_value.__enter__.return_value = mock_file
        mock_file.name = "/tmp/test_vnet"
        
        result_xml = infra_tools['create_vnet'](template_content="NAME=test-net")
        
        mock_file.write.assert_called_once_with("NAME=test-net")
        mock_exec.assert_called_once_with(["onevnet", "create", "/tmp/test_vnet"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["vnet_id"] == "10"

def test_create_vnet_read_only(infra_tools_read_only):
    result_xml = infra_tools_read_only['create_vnet'](template_content="NAME=test-net")
    assert "Write operations are disabled" in result_xml

# --- delete_vnet ---

def test_delete_vnet_success(infra_tools):
    with patch('src.tools.infra.infra.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = infra_tools['delete_vnet'](vnet_id="10")
        
        mock_exec.assert_called_once_with(["onevnet", "delete", "10"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["vnet_id"] == "10"

def test_delete_vnet_invalid_input(infra_tools):
    result_xml = infra_tools['delete_vnet'](vnet_id="abc")
    assert "vnet_id must be a non-negative integer" in result_xml

def test_delete_vnet_read_only(infra_tools_read_only):
    result_xml = infra_tools_read_only['delete_vnet'](vnet_id="10")
    assert "Write operations are disabled" in result_xml

# --- reserve_vnet ---

def test_reserve_vnet_success(infra_tools):
    with patch('src.tools.infra.infra.execute_one_command') as mock_exec:
        mock_exec.return_value = "ID: 11"
        
        result_xml = infra_tools['reserve_vnet'](vnet_id="10", size="5", name="my-reservation")
        
        mock_exec.assert_called_once_with(["onevnet", "reserve", "10", "--size", "5", "--name", "my-reservation"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["reservation_id"] == "11"

def test_reserve_vnet_invalid_input(infra_tools):
    result_xml = infra_tools['reserve_vnet'](vnet_id="abc", size="5")
    assert "vnet_id must be a non-negative integer" in result_xml
    
    result_xml = infra_tools['reserve_vnet'](vnet_id="10", size="abc")
    assert "size must be a non-negative integer" in result_xml

def test_reserve_vnet_read_only(infra_tools_read_only):
    result_xml = infra_tools_read_only['reserve_vnet'](vnet_id="10", size="5")
    assert "Write operations are disabled" in result_xml
