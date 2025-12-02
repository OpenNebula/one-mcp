import pytest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET
from src.tools.oneflow import oneflow

@pytest.fixture
def oneflow_tools():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    oneflow.register_tools(mcp_mock, allow_write=True)
    return tools

@pytest.fixture
def oneflow_tools_read_only():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    oneflow.register_tools(mcp_mock, allow_write=False)
    return tools

def parse_result(xml_str):
    root = ET.fromstring(xml_str)
    if root.tag == "error":
        return {"status": "error", "message": root.find("message").text}
    return {
        "status": "success",
        "service_id": root.find("service_id").text,
        "message": root.find("message").text
    }

# --- list_service_templates ---

def test_list_service_templates_success(oneflow_tools):
    with patch('src.tools.oneflow.oneflow.execute_one_command') as mock_exec:
        mock_exec.return_value = '{"DOCUMENT_POOL": []}'
        
        result = oneflow_tools['list_service_templates']()
        
        mock_exec.assert_called_once_with(["oneflow-template", "list", "--json"])
        assert result == '{"DOCUMENT_POOL": []}'

# --- deploy_service ---

def test_deploy_service_success(oneflow_tools):
    with patch('src.tools.oneflow.oneflow.execute_one_command') as mock_exec:
        mock_exec.return_value = "ID: 10"
        
        result_xml = oneflow_tools['deploy_service'](template_id="5", name="my-service")
        
        mock_exec.assert_called_once_with(["oneflow-template", "instantiate", "5", "--name", "my-service"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["service_id"] == "10"

def test_deploy_service_invalid_input(oneflow_tools):
    result_xml = oneflow_tools['deploy_service'](template_id="abc")
    assert "template_id must be a non-negative integer" in result_xml

def test_deploy_service_read_only(oneflow_tools_read_only):
    result_xml = oneflow_tools_read_only['deploy_service'](template_id="5")
    assert "Write operations are disabled" in result_xml

# --- list_services ---

def test_list_services_success(oneflow_tools):
    with patch('src.tools.oneflow.oneflow.execute_one_command') as mock_exec:
        mock_exec.return_value = '{"DOCUMENT_POOL": []}'
        
        result = oneflow_tools['list_services']()
        
        mock_exec.assert_called_once_with(["oneflow", "list", "--json"])
        assert result == '{"DOCUMENT_POOL": []}'

# --- get_service_info ---

def test_get_service_info_success(oneflow_tools):
    with patch('src.tools.oneflow.oneflow.execute_one_command') as mock_exec:
        mock_exec.return_value = '{"SERVICE": {"ID": "10"}}'
        
        result = oneflow_tools['get_service_info'](service_id="10")
        
        mock_exec.assert_called_once_with(["oneflow", "show", "10", "--json"])
        assert result == '{"SERVICE": {"ID": "10"}}'

def test_get_service_info_invalid_input(oneflow_tools):
    result_xml = oneflow_tools['get_service_info'](service_id="abc")
    assert "service_id must be a non-negative integer" in result_xml

# --- delete_service ---

def test_delete_service_success(oneflow_tools):
    with patch('src.tools.oneflow.oneflow.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = oneflow_tools['delete_service'](service_id="10")
        
        mock_exec.assert_called_once_with(["oneflow", "delete", "10"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["service_id"] == "10"

def test_delete_service_invalid_input(oneflow_tools):
    result_xml = oneflow_tools['delete_service'](service_id="abc")
    assert "service_id must be a non-negative integer" in result_xml

def test_delete_service_read_only(oneflow_tools_read_only):
    result_xml = oneflow_tools_read_only['delete_service'](service_id="10")
    assert "Write operations are disabled" in result_xml

# --- service_action ---

def test_service_action_success(oneflow_tools):
    with patch('src.tools.oneflow.oneflow.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = oneflow_tools['service_action'](service_id="10", action="shutdown")
        
        mock_exec.assert_called_once_with(["oneflow", "action", "shutdown", "10"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["service_id"] == "10"

def test_service_action_invalid_input(oneflow_tools):
    result_xml = oneflow_tools['service_action'](service_id="abc", action="shutdown")
    assert "service_id must be a non-negative integer" in result_xml

def test_service_action_read_only(oneflow_tools_read_only):
    result_xml = oneflow_tools_read_only['service_action'](service_id="10", action="shutdown")
    assert "Write operations are disabled" in result_xml

# --- scale_service ---

def test_scale_service_success(oneflow_tools):
    with patch('src.tools.oneflow.oneflow.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = oneflow_tools['scale_service'](service_id="10", role_name="worker", cardinality="5")
        
        mock_exec.assert_called_once_with(["oneflow", "scale", "10", "worker", "5"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["service_id"] == "10"

def test_scale_service_invalid_input(oneflow_tools):
    result_xml = oneflow_tools['scale_service'](service_id="abc", role_name="worker", cardinality="5")
    assert "service_id must be a non-negative integer" in result_xml
    
    result_xml = oneflow_tools['scale_service'](service_id="10", role_name="worker", cardinality="abc")
    assert "cardinality must be a non-negative integer" in result_xml

def test_scale_service_read_only(oneflow_tools_read_only):
    result_xml = oneflow_tools_read_only['scale_service'](service_id="10", role_name="worker", cardinality="5")
    assert "Write operations are disabled" in result_xml

# --- recover_service ---

def test_recover_service_success(oneflow_tools):
    with patch('src.tools.oneflow.oneflow.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = oneflow_tools['recover_service'](service_id="10")
        
        mock_exec.assert_called_once_with(["oneflow", "recover", "10"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["service_id"] == "10"

def test_recover_service_invalid_input(oneflow_tools):
    result_xml = oneflow_tools['recover_service'](service_id="abc")
    assert "service_id must be a non-negative integer" in result_xml

def test_recover_service_read_only(oneflow_tools_read_only):
    result_xml = oneflow_tools_read_only['recover_service'](service_id="10")
    assert "Write operations are disabled" in result_xml
