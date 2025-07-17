"""Unit tests for infra.list_hosts filtering logic."""

import xml.etree.ElementTree as ET
from src.tools.infra import infra as infra_module
from src.tests.unit.conftest import register_tools


def _get_list_hosts_func(monkeypatch, hosts_xml: str):
    tools = register_tools(monkeypatch, "src.tools.infra.infra", hosts_xml)
    return tools["list_hosts"]


# ----------------------------------------------------------------------------
# XML fixtures
# ----------------------------------------------------------------------------

HOSTS_XML = """<HOST_POOL>
    <HOST><ID>1</ID><CLUSTER_ID>100</CLUSTER_ID></HOST>
    <HOST><ID>2</ID><CLUSTER_ID>200</CLUSTER_ID></HOST>
</HOST_POOL>"""

INVALID_XML = "<broken>"

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------


def test_list_hosts_filters_by_cluster(monkeypatch):
    list_hosts = _get_list_hosts_func(monkeypatch, HOSTS_XML)

    output = list_hosts("100")
    root = ET.fromstring(output)
    hosts = root.findall("HOST")
    assert len(hosts) == 1
    assert hosts[0].find("ID").text == "1"


def test_list_hosts_no_hosts_found(monkeypatch):
    list_hosts = _get_list_hosts_func(monkeypatch, HOSTS_XML)

    output = list_hosts("999")
    assert output.startswith("<error>")
    assert "No hosts found" in output


def test_list_hosts_non_digit_cluster(monkeypatch):
    """Non-digit cluster_id should bypass filtering and return raw XML."""
    list_hosts = _get_list_hosts_func(monkeypatch, HOSTS_XML)
    output = list_hosts("abc")
    assert output == HOSTS_XML


def test_list_hosts_invalid_xml(monkeypatch):
    """Invalid XML should return <error>"""

    list_hosts = _get_list_hosts_func(monkeypatch, INVALID_XML)
    output = list_hosts("100")

    assert output.startswith("<error>")
    assert "Failed to parse" in output 