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
        "group_id": root.find("group_id").text,
        "message": root.find("message").text
    }

# --- list_groups ---

def test_list_groups_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "<GROUP_POOL></GROUP_POOL>"
        
        result = tenancy_tools['list_groups']()
        
        mock_exec.assert_called_once_with(["onegroup", "list", "--xml"])
        assert result == "<GROUP_POOL></GROUP_POOL>"

# --- create_group ---

def test_create_group_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "ID: 10"
        
        result_xml = tenancy_tools['create_group'](name="testgroup")
        
        mock_exec.assert_called_once_with(["onegroup", "create", "testgroup"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["group_id"] == "10"

def test_create_group_read_only(tenancy_tools_read_only):
    result_xml = tenancy_tools_read_only['create_group'](name="testgroup")
    assert "Write operations are disabled" in result_xml

# --- add_user_to_group ---

def test_add_user_to_group_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = tenancy_tools['add_user_to_group'](group_id="10", user_id="5")
        
        mock_exec.assert_called_once_with(["onegroup", "add_user", "10", "5"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["group_id"] == "10"

def test_add_admin_to_group_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = tenancy_tools['add_user_to_group'](group_id="10", user_id="5", admin=True)
        
        mock_exec.assert_called_once_with(["onegroup", "add_admin", "10", "5"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["group_id"] == "10"

def test_add_user_to_group_invalid_input(tenancy_tools):
    result_xml = tenancy_tools['add_user_to_group'](group_id="abc", user_id="5")
    assert "group_id must be a non-negative integer" in result_xml
    
    result_xml = tenancy_tools['add_user_to_group'](group_id="10", user_id="abc")
    assert "user_id must be a non-negative integer" in result_xml

def test_add_user_to_group_read_only(tenancy_tools_read_only):
    result_xml = tenancy_tools_read_only['add_user_to_group'](group_id="10", user_id="5")
    assert "Write operations are disabled" in result_xml

# --- delete_group ---

def test_delete_group_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = tenancy_tools['delete_group'](group_id="10")
        
        mock_exec.assert_called_once_with(["onegroup", "delete", "10"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["group_id"] == "10"

def test_delete_group_invalid_input(tenancy_tools):
    result_xml = tenancy_tools['delete_group'](group_id="abc")
    assert "group_id must be a non-negative integer" in result_xml

def test_delete_group_read_only(tenancy_tools_read_only):
    result_xml = tenancy_tools_read_only['delete_group'](group_id="10")
    assert "Write operations are disabled" in result_xml
