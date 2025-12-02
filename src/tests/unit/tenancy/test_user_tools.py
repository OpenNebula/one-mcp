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
        "user_id": root.find("user_id").text,
        "message": root.find("message").text
    }

# --- list_users ---

def test_list_users_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "<USER_POOL></USER_POOL>"
        
        result = tenancy_tools['list_users']()
        
        mock_exec.assert_called_once_with(["oneuser", "list", "--xml"])
        assert result == "<USER_POOL></USER_POOL>"

# --- create_user ---

def test_create_user_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "ID: 10"
        
        result_xml = tenancy_tools['create_user'](name="testuser", password="password123")
        
        mock_exec.assert_called_once_with(["oneuser", "create", "testuser", "password123"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["user_id"] == "10"

def test_create_user_with_driver(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "ID: 11"
        
        result_xml = tenancy_tools['create_user'](name="testuser", password="password123", auth_driver="public")
        
        mock_exec.assert_called_once_with(["oneuser", "create", "testuser", "password123", "--driver", "public"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["user_id"] == "11"

def test_create_user_read_only(tenancy_tools_read_only):
    result_xml = tenancy_tools_read_only['create_user'](name="testuser", password="password123")
    assert "Write operations are disabled" in result_xml

# --- update_user_quota ---

def test_update_user_quota_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec, \
         patch('tempfile.NamedTemporaryFile') as mock_temp, \
         patch('os.path.exists', return_value=True), \
         patch('os.remove'):
        
        mock_exec.return_value = "Success"
        
        mock_file = MagicMock()
        mock_temp.return_value.__enter__.return_value = mock_file
        mock_file.name = "/tmp/quota_file"
        
        result_xml = tenancy_tools['update_user_quota'](user_id="10", quota_template="VM=[CPU=1]")
        
        mock_file.write.assert_called_once_with("VM=[CPU=1]")
        mock_exec.assert_called_once_with(["oneuser", "quota", "10", "/tmp/quota_file"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["user_id"] == "10"

def test_update_user_quota_invalid_input(tenancy_tools):
    result_xml = tenancy_tools['update_user_quota'](user_id="abc", quota_template="VM=[CPU=1]")
    assert "user_id must be a non-negative integer" in result_xml

def test_update_user_quota_read_only(tenancy_tools_read_only):
    result_xml = tenancy_tools_read_only['update_user_quota'](user_id="10", quota_template="VM=[CPU=1]")
    assert "Write operations are disabled" in result_xml

# --- delete_user ---

def test_delete_user_success(tenancy_tools):
    with patch('src.tools.tenancy.tenancy.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = tenancy_tools['delete_user'](user_id="10")
        
        mock_exec.assert_called_once_with(["oneuser", "delete", "10"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["user_id"] == "10"

def test_delete_user_invalid_input(tenancy_tools):
    result_xml = tenancy_tools['delete_user'](user_id="abc")
    assert "user_id must be a non-negative integer" in result_xml

def test_delete_user_read_only(tenancy_tools_read_only):
    result_xml = tenancy_tools_read_only['delete_user'](user_id="10")
    assert "Write operations are disabled" in result_xml
