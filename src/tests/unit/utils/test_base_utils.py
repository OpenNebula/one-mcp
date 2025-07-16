"""Unit tests for src.tools.utils.base module."""

import subprocess
import pytest
from types import SimpleNamespace

from src.tools.utils import base as base_utils

# ----------------------------- is_valid_ip_address -----------------------------

@pytest.mark.parametrize(
    "ip, expected",
    [
        ("192.168.1.1", True),
        ("255.255.255.255", True),
        ("::1", True),  # IPv6 loopback
        ("300.1.1.1", False),
        ("not_an_ip", False),
        ("", False),
        ("1234:5678:9abc:def0:1234:5678:9abc:defg", False),  # invalid hex
    ],
)
def test_is_valid_ip_address(ip, expected):
    assert base_utils.is_valid_ip_address(ip) is expected


# ----------------------------- execute_one_command -----------------------------

def test_execute_one_command_success(monkeypatch):
    """Should return stdout when subprocess completes successfully."""

    def fake_run(cmd, capture_output, text, check):  # noqa: D401
        assert cmd == ["onehost", "list", "--xml"]
        return SimpleNamespace(stdout="<xml>OK</xml>")

    monkeypatch.setattr(subprocess, "run", fake_run)

    output = base_utils.execute_one_command(["onehost", "list", "--xml"])
    assert output == "<xml>OK</xml>"


def test_execute_one_command_called_process_error(monkeypatch):
    """Should wrap CalledProcessError into XML <error>."""

    class FakeError(subprocess.CalledProcessError):
        def __init__(self):
            super().__init__(returncode=42, cmd="cmd")
            self.stderr = "Boom"
            self.stdout = ""

    def fake_run(*args, **kwargs):
        raise FakeError()

    monkeypatch.setattr(subprocess, "run", fake_run)

    output = base_utils.execute_one_command(["cmd"])
    assert "<error>" in output
    assert "<exit_code>42</exit_code>" in output
    assert "Boom" in output


def test_execute_one_command_file_not_found(monkeypatch):
    """Should produce exit_code 127 when binary is missing."""

    def fake_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "run", fake_run)

    output = base_utils.execute_one_command(["missing-binary"])
    assert "<exit_code>127</exit_code>" in output
    assert "Command not found" in output


def test_execute_one_command_unexpected_error(monkeypatch):
    """Generic exception should map to exit_code -1."""

    def fake_run(*args, **kwargs):
        raise RuntimeError("bad things")

    monkeypatch.setattr(subprocess, "run", fake_run)

    output = base_utils.execute_one_command(["cmd"])
    assert "<exit_code>-1</exit_code>" in output
    assert "RuntimeError" in output 