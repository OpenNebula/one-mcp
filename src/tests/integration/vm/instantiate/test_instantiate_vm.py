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

"""Integration tests for the instantiate_vm MCP tool."""

import xml.etree.ElementTree as ET

import fastmcp
import pytest
from fastmcp import Client

from src.tools.utils.base import execute_one_command  # noqa: F401 (potential future use)
from src.tests.shared.utils import get_vm_id, search_for_pattern, cleanup_test_vms


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
            "instantiate_vm", {"template_id": "0", "vm_name": "test_vm_allow_write_false"}
        )

        output = result.content[0].text
        expected_error = "Write operations are disabled"
        assert expected_error in output
        cleanup_test_vms()


@pytest.mark.asyncio
async def test_instantiate_vm(mcp_server):
    """Test that instantiate_vm works when write operations are enabled."""
    async with Client(mcp_server) as client:
        # Call instantiate_vm with valid parameters
        result = await client.call_tool(
            "instantiate_vm",
            {"template_id": "0", "vm_name": "test_vm_instantiate_vm", "cpu": "1", "memory": "1"},
        )

        output = result.content[0].text
        # Assert that a VM has been correctly created
        assert search_for_pattern(output, r"<ID>\d+</ID>"), (
            f"Expected pattern '<ID>\\d+</ID>' not found in output: {output}"
        )

        cleanup_test_vms()


@pytest.mark.asyncio
async def test_instantiate_vm_invalid_template_id(mcp_server):
    """Test that instantiate_vm returns an error when the template_id is negative."""
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "instantiate_vm", {"template_id": "-1", "vm_name": "test_vm_invalid_template_id"}
        )
        output = result.content[0].text
        assert "error" in output

        # Test missing required template_id parameter should raise ToolError
        with pytest.raises(fastmcp.exceptions.ToolError):
            await client.call_tool("instantiate_vm", {"vm_name": "test_vm_invalid_template_id"})


@pytest.mark.asyncio
async def test_instantiate_vm_invalid_cpu_and_memory(mcp_server):
    """Test that instantiate_vm returns an error when the cpu and memory are invalid."""
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "instantiate_vm", {"template_id": "0", "vm_name": "test_vm_invalid_cpu", "cpu": "-1"}
        )
        output = result.content[0].text
        assert "error" in output

        result = await client.call_tool(
            "instantiate_vm", {"template_id": "0", "vm_name": "test_vm_invalid_memory", "memory": "-1"}
        )
        output = result.content[0].text
        assert "error" in output
        cleanup_test_vms()


@pytest.mark.asyncio
async def test_instantiate_vm_with_network_name(mcp_server):
    """Test that instantiate_vm works when a network name is provided."""
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "instantiate_vm",
            {"template_id": "0", "vm_name": "test_vm_with_network_name", "network_name": "service"},
        )
        output = result.content[0].text
        assert search_for_pattern(output, r"<ID>\d+</ID>"), (
            f"Expected pattern '<ID>\\d+</ID>' not found in output: {output}"
        )
        assert search_for_pattern(
            output, r"<NETWORK><!\[CDATA\[service\]\]></NETWORK>"
        ), f"Expected network 'service' not found in output: {output}"

        cleanup_test_vms()


@pytest.mark.asyncio
async def test_instantiate_vm_multiple_instances(mcp_server):
    """Test that instantiate_vm can create multiple VMs at once."""
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "instantiate_vm",
            {
                "template_id": "0",
                "vm_name": "test_vm_multiple_instances",
                "num_instances": "2",
            },
        )
        output = result.content[0].text

        # Parse XML and check for multiple VM elements
        try:
            root = ET.fromstring(output)
            assert root.tag == "VMS"
            vms = root.findall("VM")
            assert len(vms) == 2
            # Check that each VM has an ID
            for vm in vms:
                assert vm.find("ID") is not None
        except ET.ParseError as e:
            pytest.fail(f"Failed to parse XML output: {e}\nOutput was: {output}")
        finally:
            cleanup_test_vms()


@pytest.mark.asyncio
async def test_instantiate_vm_invalid_num_instances(mcp_server):
    """Test that instantiate_vm returns an error for invalid num_instances."""
    async with Client(mcp_server) as client:
        # Test with negative num_instances
        result = await client.call_tool(
            "instantiate_vm",
            {
                "template_id": "0",
                "vm_name": "test_vm_invalid_num",
                "num_instances": "-1",
            },
        )
        output = result.content[0].text
        assert "error" in output

        # Test with zero num_instances
        result = await client.call_tool(
            "instantiate_vm",
            {
                "template_id": "0",
                "vm_name": "test_vm_invalid_num",
                "num_instances": "0",
            },
        )
        output = result.content[0].text
        assert "error" in output

        # Test with non-integer num_instances
        result = await client.call_tool(
            "instantiate_vm",
            {
                "template_id": "0",
                "vm_name": "test_vm_invalid_num",
                "num_instances": "abc",
            },
        )
        output = result.content[0].text
        assert "error" in output
        cleanup_test_vms() 