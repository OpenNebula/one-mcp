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
    return {
        "status": "success",
        "host_id": root.find("host_id").text,
        "message": root.find("message").text
    }

# --- enable_host ---

def test_enable_host_success(infra_tools):
    with patch('src.tools.infra.infra.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = infra_tools['enable_host'](host_id="10")
        
        mock_exec.assert_called_once_with(["onehost", "enable", "10"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["host_id"] == "10"

def test_enable_host_invalid_input(infra_tools):
    result_xml = infra_tools['enable_host'](host_id="abc")
    assert "host_id must be a non-negative integer" in result_xml

def test_enable_host_read_only(infra_tools_read_only):
    result_xml = infra_tools_read_only['enable_host'](host_id="10")
    assert "Write operations are disabled" in result_xml

# --- disable_host ---

def test_disable_host_success(infra_tools):
    with patch('src.tools.infra.infra.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = infra_tools['disable_host'](host_id="10")
        
        mock_exec.assert_called_once_with(["onehost", "disable", "10"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["host_id"] == "10"

def test_disable_host_invalid_input(infra_tools):
    result_xml = infra_tools['disable_host'](host_id="abc")
    assert "host_id must be a non-negative integer" in result_xml

def test_disable_host_read_only(infra_tools_read_only):
    result_xml = infra_tools_read_only['disable_host'](host_id="10")
    assert "Write operations are disabled" in result_xml

# --- host_monitoring ---

def test_host_monitoring_success(infra_tools):
    with patch('src.tools.infra.infra.execute_one_command') as mock_exec:
        mock_exec.return_value = "<HOST><ID>10</ID><NAME>host1</NAME></HOST>"
        
        result_xml = infra_tools['host_monitoring'](host_id="10")
        
        mock_exec.assert_called_once_with(["onehost", "show", "10", "--xml"])
        assert result_xml == "<HOST><ID>10</ID><NAME>host1</NAME></HOST>"

def test_host_monitoring_invalid_input(infra_tools):
    result_xml = infra_tools['host_monitoring'](host_id="abc")
    assert "host_id must be a non-negative integer" in result_xml
