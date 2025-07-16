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

"""Integration tests for the execute_command tool using FastMCP in-memory testing."""

import pytest
from fastmcp import Client


@pytest.mark.asyncio
async def test_execute_command_tool_exists(mcp_server):
    """Test that the execute_command tool is properly registered and can be called."""
    async with Client(mcp_server) as client:
        # List all available tools to verify execute_command is registered
        tools = await client.list_tools()

        # Check that execute_command tool exists
        tool_names = [tool.name for tool in tools]
        assert "execute_command" in tool_names

        # Find the execute_command tool and verify its description
        execute_tool = next(tool for tool in tools if tool.name == "execute_command")
        assert "Execute a shell command" in execute_tool.description
        assert execute_tool.inputSchema is not None


@pytest.mark.asyncio
async def test_execute_command_with_invalid_vm_ip_address(mcp_server):
    """Test that execute_command properly handles invalid VM IP address."""
    async with Client(mcp_server) as client:
        # Test with invalid VM ID (negative number)
        result = await client.call_tool(
            "execute_command", {"vm_ip_address": "-1", "command": "echo test"}
        )

        # The result should contain an error
        assert len(result.content) == 1
        output = result.content[0].text

        assert "<error><message>Invalid IP address</message></error>" in output


@pytest.mark.asyncio
async def test_execute_command_basic_system_info(mcp_server, test_vm_ip):
    """Test basic system commands with specific expected outputs."""
    async with Client(mcp_server) as client:
        # Test whoami - should return root as the user
        result = await client.call_tool(
            "execute_command", {"vm_ip_address": test_vm_ip, "command": "whoami"}
        )

        assert len(result.content) == 1
        output = result.content[0].text
        assert "<error>" not in output
        assert "root" in output


@pytest.mark.asyncio
async def test_execute_command_filesystem_root_access(mcp_server, test_vm_ip):
    """Test filesystem access to root directory - must contain standard Unix directories."""
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "execute_command", {"vm_ip_address": test_vm_ip, "command": "ls -1 /"}
        )

        assert len(result.content) == 1
        output = result.content[0].text
        assert "<error>" not in output

        # Every Unix/Linux system must have these directories in root
        required_dirs = ["etc", "tmp", "usr"]
        for directory in required_dirs:
            assert directory in output, (
                f"Standard directory '{directory}' not found in root listing"
            )


@pytest.mark.asyncio
async def test_execute_command_file_write_read_cycle(mcp_server, test_vm_ip):
    """Test complete file write/read cycle to verify write permissions and data integrity."""
    async with Client(mcp_server) as client:
        test_file = "/tmp/mcp_critical_test.txt"
        test_content = "MCP_TEST_CONTENT_12345"

        # Write test content to file
        write_result = await client.call_tool(
            "execute_command",
            {
                "vm_ip_address": test_vm_ip,
                "command": f"echo '{test_content}' > {test_file}",
            },
        )

        assert len(write_result.content) == 1
        write_output = write_result.content[0].text
        assert "<error>" not in write_output, "Failed to write test file"

        # Read back the content
        read_result = await client.call_tool(
            "execute_command",
            {"vm_ip_address": test_vm_ip, "command": f"cat {test_file}"},
        )

        assert len(read_result.content) == 1
        read_output = read_result.content[0].text
        assert "<error>" not in read_output, "Failed to read test file"
        assert test_content in read_output, (
            f"Expected content '{test_content}' not found in file output"
        )

        # Cleanup - remove test file
        cleanup_result = await client.call_tool(
            "execute_command",
            {"vm_ip_address": test_vm_ip, "command": f"rm -f {test_file}"},
        )

        assert len(cleanup_result.content) == 1
        cleanup_output = cleanup_result.content[0].text
        assert "<error>" not in cleanup_output, "Failed to cleanup test file"


@pytest.mark.asyncio
async def test_execute_command_with_pipes_and_complex_logic(mcp_server, test_vm_ip):
    """Test command chaining and pipes work correctly with expected output."""
    async with Client(mcp_server) as client:
        # Test pipe command that should always work: echo piped to grep
        result = await client.call_tool(
            "execute_command",
            {
                "vm_ip_address": test_vm_ip,
                "command": "echo 'hello world test' | grep 'world'",
            },
        )

        assert len(result.content) == 1
        output = result.content[0].text

        assert "hello world test" in output, "Should contain the full echoed string"


@pytest.mark.asyncio
async def test_execute_command_write_disabled(mcp_server_read_only):
    """Test that execute_command fails when allow_write is False."""
    async with Client(mcp_server_read_only) as client:
        result = await client.call_tool(
            "execute_command",
            {"vm_ip_address": "127.0.0.1", "command": "echo 'test'"},
        )
        assert "write operations are disabled" in result.content[0].text.lower()
