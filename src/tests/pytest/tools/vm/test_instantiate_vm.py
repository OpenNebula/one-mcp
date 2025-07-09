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

"""
Unit tests for the instantiate_vm MCP tool.
"""

import fastmcp
import pytest
from fastmcp import Client
from src.tools.utils.base import execute_one_command
from src.tests.pytest.utils import get_vm_id, search_for_pattern


@pytest.mark.asyncio
async def test_instantiate_vm_tool_exists(mcp_server):
    """Test that the instantiate_vm tool is properly registered."""
    async with Client(mcp_server) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "instantiate_vm" in tool_names


@pytest.mark.asyncio
async def test_instantiate_vm_allow_write_false(mcp_server_read_only):
    """Test that instantiate_vm denies operations when allow_write=False."""
    async with Client(mcp_server_read_only) as client:
        result = await client.call_tool(
            "instantiate_vm", {"template_id": "0", "vm_name": "test_vm"}
        )

        output = result.content[0].text
        expected_error = "Write operations are disabled"
        assert expected_error in output


@pytest.mark.asyncio
async def test_instantiate_vm(mcp_server):
    """Test that instantiate_vm works when write operations are enabled."""
    async with Client(mcp_server) as client:
        # Call instantiate_vm with valid parameters
        result = await client.call_tool(
            "instantiate_vm",
            {"template_id": "0", "vm_name": "deny_test", "cpu": "1", "memory": "1"},
        )

        output = result.content[0].text
        # Assert that a VM has been correctly created
        assert search_for_pattern(output, r"<ID>\d+</ID>"), (
            f"Expected pattern '<ID>\\d+</ID>' not found in output: {output}"
        )

        # Delete the VM instantied for the test
        vm_id = get_vm_id(output)
        execute_one_command(["onevm", "recover", "--delete", vm_id])


@pytest.mark.asyncio
async def test_instantiate_vm_invalid_template_id(mcp_server):
    """Test that instantiate_vm returns an error when the template_id is negative."""
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "instantiate_vm", {"template_id": "-1", "vm_name": "test_vm"}
        )
        output = result.content[0].text
        assert "template_id must be a positive integer" in output

        # Test missing required template_id parameter should raise ToolError
        with pytest.raises(fastmcp.exceptions.ToolError):
            await client.call_tool("instantiate_vm", {"vm_name": "test_vm"})


@pytest.mark.asyncio
async def test_instantiate_vm_invalid_cpu_and_memory(mcp_server):
    """Test that instantiate_vm returns an error when the cpu and memory are invalid."""
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "instantiate_vm", {"template_id": "0", "vm_name": "test_vm", "cpu": "-1"}
        )
        output = result.content[0].text
        assert "cpu must be a positive integer" in output

        result = await client.call_tool(
            "instantiate_vm", {"template_id": "0", "vm_name": "test_vm", "memory": "-1"}
        )
        output = result.content[0].text
        assert "memory must be a positive integer" in output


@pytest.mark.asyncio
async def test_instantiate_vm_with_network_name(mcp_server):
    """Test that instantiate_vm works when a network name is provided."""
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "instantiate_vm",
            {"template_id": "0", "vm_name": "test_vm", "network_name": "service"},
        )
        output = result.content[0].text
        assert search_for_pattern(output, r"<ID>\d+</ID>"), (
            f"Expected pattern '<ID>\\d+</ID>' not found in output: {output}"
        )
        assert search_for_pattern(
            output, r"<NETWORK><!\[CDATA\[service\]\]></NETWORK>"
        ), f"Expected network 'service' not found in output: {output}"

        vm_id = get_vm_id(output)
        execute_one_command(["onevm", "recover", "--delete", vm_id])
