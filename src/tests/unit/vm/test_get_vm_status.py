"""Unit tests for vm.get_vm_status tool."""

import pytest

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


def test_get_vm_status_happy_path(monkeypatch):
    get_vm_status = _setup(monkeypatch)
    assert get_vm_status("1") == "<VM><ID>1</ID></VM>"