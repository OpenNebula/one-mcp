import pytest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET
from src.tools.tenancy import tenancy

@pytest.fixture
def tenancy_tools():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    tenancy.register_tools(mcp_mock, allow_write=True)
    return tools

@pytest.fixture
def tenancy_tools_read_only():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    tenancy.register_tools(mcp_mock, allow_write=False)
    return tools

def parse_result(xml_str):
    root = ET.fromstring(xml_str)
    if root.tag == "error":
        return {"status": "error", "message": root.find("message").text}
    return {
        "status": "success",
        "acl_id": root.find("acl_id").text,
        "message": root.find("message").text
    }

# --- list_acls ---

def test_list_acls_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "<ACL_POOL></ACL_POOL>"
        
        result = tenancy_tools['list_acls']()
        
        mock_exec.assert_called_once_with(["oneacl", "list", "--xml"])
        assert result == "<ACL_POOL></ACL_POOL>"

# --- create_acl ---

def test_create_acl_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "ID: 10"
        
        result_xml = tenancy_tools['create_acl'](user="#5", resources="VM+NET/#0", rights="USE+MANAGE")
        
        mock_exec.assert_called_once_with(["oneacl", "create", "#5 VM+NET/#0 USE+MANAGE"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["acl_id"] == "10"

def test_create_acl_read_only(tenancy_tools_read_only):
    result_xml = tenancy_tools_read_only['create_acl'](user="#5", resources="VM+NET/#0", rights="USE+MANAGE")
    assert "Write operations are disabled" in result_xml

# --- delete_acl ---

def test_delete_acl_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = tenancy_tools['delete_acl'](acl_id="10")
        
        mock_exec.assert_called_once_with(["oneacl", "delete", "10"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["acl_id"] == "10"

def test_delete_acl_invalid_input(tenancy_tools):
    result_xml = tenancy_tools['delete_acl'](acl_id="abc")
    assert "acl_id must be a non-negative integer" in result_xml

def test_delete_acl_read_only(tenancy_tools_read_only):
    result_xml = tenancy_tools_read_only['delete_acl'](acl_id="10")
    assert "Write operations are disabled" in result_xml
