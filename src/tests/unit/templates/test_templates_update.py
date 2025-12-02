import pytest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET
import os
from src.tools.templates import templates

@pytest.fixture
def template_tools():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    templates.register_tools(mcp_mock, allow_write=True)
    return tools

@pytest.fixture
def template_tools_read_only():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    templates.register_tools(mcp_mock, allow_write=False)
    return tools

def parse_result(xml_str):
    root = ET.fromstring(xml_str)
    if root.tag == "error":
        return {"status": "error", "message": root.find("message").text}
    return {
        "status": "success",
        "template_id": root.find("template_id").text,
        "operation": root.find("operation").text,
        "append": root.find("append").text,
        "command_output": root.find("command_output").text
    }

# --- update_template ---

def test_update_template_success_replace(template_tools):
    with patch('src.tools.templates.templates.execute_one_command') as mock_exec, \
         patch('tempfile.NamedTemporaryFile') as mock_temp:
        
        mock_exec.return_value = "Success"
        
        # Mock temp file context manager
        mock_file = MagicMock()
        mock_temp.return_value.__enter__.return_value = mock_file
        mock_file.name = "/tmp/test_temp_file"
        
        # Mock os.path.exists and os.remove to avoid actual file operations
        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            
            result_xml = template_tools['update_template'](template_id="10", content="NEW_CONTENT")
            
            # Verify temp file write
            mock_file.write.assert_called_once_with("NEW_CONTENT")
            
            # Verify command execution
            mock_exec.assert_called_once_with(["onetemplate", "update", "10", "/tmp/test_temp_file"])
            
            # Verify cleanup
            mock_remove.assert_called_once_with("/tmp/test_temp_file")
            
            result = parse_result(result_xml)
            assert result["status"] == "success"
            assert result["template_id"] == "10"
            assert result["operation"] == "update"
            assert result["append"] == "False"

def test_update_template_success_append(template_tools):
    with patch('src.tools.templates.templates.execute_one_command') as mock_exec, \
         patch('tempfile.NamedTemporaryFile') as mock_temp:
        
        mock_exec.return_value = "Success"
        
        mock_file = MagicMock()
        mock_temp.return_value.__enter__.return_value = mock_file
        mock_file.name = "/tmp/test_temp_file"
        
        with patch('os.path.exists', return_value=True), \
             patch('os.remove'):
            
            result_xml = template_tools['update_template'](template_id="10", content="APPEND_CONTENT", append=True)
            
            mock_exec.assert_called_once_with(["onetemplate", "update", "10", "/tmp/test_temp_file", "--append"])
            
            result = parse_result(result_xml)
            assert result["status"] == "success"
            assert result["append"] == "True"

def test_update_template_invalid_input(template_tools):
    result_xml = template_tools['update_template'](template_id="abc", content="CONTENT")
    assert "template_id must be a non-negative integer" in result_xml

def test_update_template_read_only(template_tools_read_only):
    result_xml = template_tools_read_only['update_template'](template_id="10", content="CONTENT")
    assert "Write operations are disabled" in result_xml
