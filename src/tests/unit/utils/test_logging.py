# Copyright 2002-2025, OpenNebula Project, OpenNebula Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Minimal logging tests focusing on core functionality (unit)."""

import logging
from pathlib import Path
import pytest

from src.logging_config import setup_logging, reset_logging_config


def cleanup_logs():
    """Clean up test log files from the tests subdirectory only."""
    test_log_dir = Path("log") / "tests"
    if test_log_dir.exists():
        import shutil

        shutil.rmtree(test_log_dir)


@pytest.fixture(autouse=True)
def reset_logging_state():
    """Reset logging before and after each test."""
    reset_logging_config()
    cleanup_logs()
    yield
    reset_logging_config()
    cleanup_logs()


def test_basic_setup():
    """Test logging setup works without crashing."""
    setup_logging(log_subdirectory="tests")
    logger = logging.getLogger("opennebula_mcp")

    assert logger.level == logging.INFO
    assert len(logger.handlers) == 2  # Console + file (default)
    assert not logger.propagate


def test_file_logging_toggle():
    """Test file logging enable/disable."""
    # Test enabled (default behavior now)
    setup_logging(enable_file_logging=True, log_subdirectory="tests")
    assert len(logging.getLogger("opennebula_mcp").handlers) == 2  # Console + file
    assert Path("log/tests").exists()

    reset_logging_config()

    # Test disabled (explicit --no-log-file)
    setup_logging(enable_file_logging=False, log_subdirectory="tests")
    assert len(logging.getLogger("opennebula_mcp").handlers) == 1  # Console only


def test_log_levels():
    """Test different log levels work."""
    setup_logging(level="DEBUG", log_subdirectory="tests")
    assert logging.getLogger("opennebula_mcp").level == logging.DEBUG

    reset_logging_config()

    setup_logging(level="ERROR", log_subdirectory="tests")
    assert logging.getLogger("opennebula_mcp").level == logging.ERROR


def test_file_content():
    """Test that logs actually write to file with correct content."""
    setup_logging(level="INFO", enable_file_logging=True, log_subdirectory="tests")

    logger = logging.getLogger("opennebula_mcp.test")
    logger.info("Test message")

    # Find log file and verify content
    log_files = list(Path("log/tests").glob("*.log"))
    assert len(log_files) == 1

    content = log_files[0].read_text()
    assert "Test message" in content
    assert "opennebula_mcp.test" in content
