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
        "image_id": root.find("image_id").text,
        "message": root.find("message").text
    }

# --- create_image ---

def test_create_image_success(infra_tools):
    with patch('src.tools.infra.infra.execute_one_command') as mock_exec:
        mock_exec.return_value = "ID: 10"
        
        result_xml = infra_tools['create_image'](
            name="test-image",
            path="/path/to/image",
            datastore_id="100",
            type="OS",
            prefix="vd",
            persistent=True
        )
        
        mock_exec.assert_called_once_with([
            "oneimage", "create",
            "--name", "test-image",
            "--path", "/path/to/image",
            "--datastore", "100",
            "--type", "OS",
            "--prefix", "vd",
            "--persistent"
        ])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["image_id"] == "10"

def test_create_image_invalid_input(infra_tools):
    result_xml = infra_tools['create_image'](
        name="test-image",
        path="/path/to/image",
        datastore_id="abc"
    )
    assert "datastore_id must be a non-negative integer" in result_xml

def test_create_image_read_only(infra_tools_read_only):
    result_xml = infra_tools_read_only['create_image'](
        name="test-image",
        path="/path/to/image",
        datastore_id="100"
    )
    assert "Write operations are disabled" in result_xml

# --- delete_image ---

def test_delete_image_success(infra_tools):
    with patch('src.tools.infra.infra.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = infra_tools['delete_image'](image_id="10")
        
        mock_exec.assert_called_once_with(["oneimage", "delete", "10"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["image_id"] == "10"

def test_delete_image_invalid_input(infra_tools):
    result_xml = infra_tools['delete_image'](image_id="abc")
    assert "image_id must be a non-negative integer" in result_xml

def test_delete_image_read_only(infra_tools_read_only):
    result_xml = infra_tools_read_only['delete_image'](image_id="10")
    assert "Write operations are disabled" in result_xml

# --- update_image_type ---

def test_update_image_type_success(infra_tools):
    with patch('src.tools.infra.infra.execute_one_command') as mock_exec:
        mock_exec.return_value = "Success"
        
        result_xml = infra_tools['update_image_type'](image_id="10", type="CDROM")
        
        mock_exec.assert_called_once_with(["oneimage", "chtype", "10", "CDROM"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert result["image_id"] == "10"

def test_update_image_type_invalid_input(infra_tools):
    result_xml = infra_tools['update_image_type'](image_id="abc", type="CDROM")
    assert "image_id must be a non-negative integer" in result_xml

def test_update_image_type_read_only(infra_tools_read_only):
    result_xml = infra_tools_read_only['update_image_type'](image_id="10", type="CDROM")
    assert "Write operations are disabled" in result_xml
