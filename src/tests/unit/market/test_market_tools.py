import pytest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET
from src.tools.market import market

@pytest.fixture
def market_tools():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    market.register_tools(mcp_mock, allow_write=True)
    return tools

@pytest.fixture
def market_tools_read_only():
    mcp_mock = MagicMock()
    tools = {}
    
    def tool_decorator(name=None, description=None):
        def decorator(func):
            tools[name] = func
            return func
        return decorator
    
    mcp_mock.tool = tool_decorator
    
    market.register_tools(mcp_mock, allow_write=False)
    return tools

def parse_result(xml_str):
    root = ET.fromstring(xml_str)
    if root.tag == "error":
        return {"status": "error", "message": root.find("message").text}
    return {
        "status": "success",
        "output": root.find("output").text
    }

# --- list_markets ---

def test_list_markets_success(market_tools):
    with patch('src.tools.market.market.execute_one_command') as mock_exec:
        mock_exec.return_value = "<MARKET_POOL></MARKET_POOL>"
        
        result = market_tools['list_markets']()
        
        mock_exec.assert_called_once_with(["onemarket", "list", "--xml"])
        assert result == "<MARKET_POOL></MARKET_POOL>"

# --- search_market_apps ---

def test_search_market_apps_all(market_tools):
    with patch('src.tools.market.market.execute_one_command') as mock_exec:
        mock_xml = "<MARKETPLACEAPP_POOL></MARKETPLACEAPP_POOL>"
        mock_exec.return_value = mock_xml
        
        result = market_tools['search_market_apps']()
        
        mock_exec.assert_called_once_with(["onemarketapp", "list", "--xml"])
        assert result == mock_xml

def test_search_market_apps_filtered(market_tools):
    with patch('src.tools.market.market.execute_one_command') as mock_exec:
        # Mock XML with multiple apps, one matching "ubuntu" (case-insensitive)
        mock_xml = """<MARKETPLACEAPP_POOL>
            <MARKETPLACEAPP>
                <ID>1</ID>
                <NAME>Ubuntu 22.04</NAME>
                <DESCRIPTION>Ubuntu Server image</DESCRIPTION>
                <TAGS>ubuntu,linux</TAGS>
            </MARKETPLACEAPP>
            <MARKETPLACEAPP>
                <ID>2</ID>
                <NAME>Debian 12</NAME>
                <DESCRIPTION>Debian Server image</DESCRIPTION>
                <TAGS>debian,linux</TAGS>
            </MARKETPLACEAPP>
        </MARKETPLACEAPP_POOL>"""
        mock_exec.return_value = mock_xml
        
        result = market_tools['search_market_apps'](filter_str="ubuntu")
        
        # Should call list with --xml (no filter), then filter client-side
        mock_exec.assert_called_once_with(["onemarketapp", "list", "--xml"])
        # Result should only contain the Ubuntu app (case-insensitive match)
        assert "Ubuntu" in result
        assert "Debian" not in result

# --- import_market_app ---

def test_import_market_app_success(market_tools):
    with patch('src.tools.market.market.execute_one_command') as mock_exec:
        mock_exec.return_value = "IMAGE ID: 10"
        
        result_xml = market_tools['import_market_app'](app_id="5", datastore_id="100", name="my-image")
        
        mock_exec.assert_called_once_with(["onemarketapp", "export", "5", "my-image", "--datastore", "100"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert "IMAGE ID: 10" in result["output"]

def test_import_market_app_no_name(market_tools):
    with patch('src.tools.market.market.execute_one_command') as mock_exec:
        mock_exec.return_value = "IMAGE ID: 11"
        
        result_xml = market_tools['import_market_app'](app_id="5", datastore_id="100")
        
        mock_exec.assert_called_once_with(["onemarketapp", "export", "5", "--datastore", "100"])
        
        result = parse_result(result_xml)
        assert result["status"] == "success"
        assert "IMAGE ID: 11" in result["output"]

def test_import_market_app_invalid_input(market_tools):
    result_xml = market_tools['import_market_app'](app_id="abc", datastore_id="100")
    assert "app_id must be a non-negative integer" in result_xml
    
    result_xml = market_tools['import_market_app'](app_id="5", datastore_id="abc")
    assert "datastore_id must be a non-negative integer" in result_xml

def test_import_market_app_read_only(market_tools_read_only):
    result_xml = market_tools_read_only['import_market_app'](app_id="5", datastore_id="100")
    assert "Write operations are disabled" in result_xml
