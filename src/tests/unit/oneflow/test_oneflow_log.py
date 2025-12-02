import pytest
from unittest.mock import MagicMock, patch
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

def test_get_service_log_success(oneflow_tools):
    with patch('src.tools.oneflow.oneflow.execute_one_command') as mock_exec:
        mock_exec.return_value = "Service Log Content"
        
        result = oneflow_tools['get_service_log'](service_id="5")
        
        mock_exec.assert_called_once_with(["onelog", "get-service", "5"])
        assert result == "Service Log Content"

def test_get_service_log_invalid_id(oneflow_tools):
    result = oneflow_tools['get_service_log'](service_id="abc")
    assert "service_id must be a non-negative integer" in result
