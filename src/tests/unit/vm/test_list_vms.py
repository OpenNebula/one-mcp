"""Unit tests for vm.list_vms validation."""

from src.tests.unit.conftest import register_tools

MODULE_PATH = "src.tools.vm.vm"

def _tool(monkeypatch):
    tools = register_tools(monkeypatch, MODULE_PATH, xml_out="<VM_POOL></VM_POOL>", allow_write=True)
    return tools["list_vms"]


def test_list_vms_invalid_filters(monkeypatch):
    list_vms = _tool(monkeypatch)

    # state non-digit -> error
    out = list_vms(state="abc", host_id=None, cluster_id=None)
    assert out.startswith("<error>")
    # host_id non-digit -> error
    out = list_vms(state=None, host_id="abc", cluster_id=None)
    assert out.startswith("<error>")
    # cluster_id non-digit -> error
    out = list_vms(state=None, host_id=None, cluster_id="xyz")
    assert out.startswith("<error>") 