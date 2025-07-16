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

"""Shared fixtures for integration tests (interact with OpenNebula)."""

import pytest
from fastmcp import FastMCP
from src.static import MCP_SERVER_PROMPT
from src.tools import infra, vm, templates

# Test Configuration
# Update this IP address to match an active VM with SSH access in your OpenNebula environment
TEST_VM_IP_ADDRESS = "172.20.0.12"


@pytest.fixture
def mcp_server():
    """Create a test MCP server instance with all tools registered (write enabled)."""
    server = FastMCP(name="test-opennebula-mcp-server", instructions=MCP_SERVER_PROMPT)

    infra.register_tools(server)
    vm.register_tools(server, allow_write=True)
    templates.register_tools(server)
    return server


@pytest.fixture
def mcp_server_read_only():
    """Create a test MCP server instance with allow_write=False."""
    server = FastMCP(
        name="test-opennebula-mcp-server-read-only", instructions=MCP_SERVER_PROMPT
    )

    infra.register_tools(server)
    vm.register_tools(server, allow_write=False)
    templates.register_tools(server)
    return server


@pytest.fixture
def test_vm_ip():
    """Provide the test VM IP address for VM-related tests."""
    return TEST_VM_IP_ADDRESS
