"""Unit tests for vm.get_vm_status tool."""


from src.tests.unit.conftest import register_tools

MODULE_PATH = "src.tools.vm.vm"

def _setup(monkeypatch, xml_out:str = "<VM><ID>1</ID></VM>"):
    tools = register_tools(monkeypatch, MODULE_PATH, xml_out=xml_out, allow_write=True)
    return tools["get_vm_status"]


def test_get_vm_status_invalid_id(monkeypatch):
    get_vm_status = _setup(monkeypatch)
    # non-numeric id -> error
    assert get_vm_status("abc").startswith("<error>")
    # negative integer -> error
    assert get_vm_status("-1").startswith("<error>")


def test_get_vm_status_zero_id_spec_conformance(monkeypatch):
    get_vm_status = _setup(monkeypatch, xml_out="<VM><ID>0</ID></VM>")
    assert get_vm_status("0") == "<VM><ID>0</ID></VM>"


def test_get_vm_status_xml_error_structure(monkeypatch):
    """Test that get_vm_status returns properly structured error XML."""
    get_vm_status = _setup(monkeypatch)
    
    out = get_vm_status("invalid")
    
    # Verify error XML structure
    assert out.startswith("<error>")
    assert "vm_id must be a positive integer" in out


def test_get_vm_status_xml_success_structure(monkeypatch):
    """Test that get_vm_status returns the expected XML structure for valid inputs."""
    expected_xml = "<VM><ID>42</ID><STATE>3</STATE></VM>"
    get_vm_status = _setup(monkeypatch, xml_out=expected_xml)
    
    out = get_vm_status("42")
    
    # Should return the exact XML from the mocked command
    assert out == expected_xml

def test_get_vm_status_happy_path(monkeypatch):
    get_vm_status = _setup(monkeypatch)
    assert get_vm_status("1") == "<VM><ID>1</ID></VM>"