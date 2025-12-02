import pytest
from unittest.mock import MagicMock, patch
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
    
    vm.register_tools(mcp_mock, allow_write=True)
    return tools

def test_get_vm_log_success(vm_tools):
    with patch('src.tools.vm.vm.execute_one_command') as mock_exec:
        mock_exec.return_value = "VM Log Content"
        
        result = vm_tools['get_vm_log'](vm_id="10")
        
        mock_exec.assert_called_once_with(["onelog", "get-vm", "10"])
        assert result == "VM Log Content"

def test_get_vm_log_invalid_id(vm_tools):
    result = vm_tools['get_vm_log'](vm_id="abc")
    assert "vm_id must be a non-negative integer" in result
