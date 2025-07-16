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

"""Integration tests for the manage_vm tool in the VM module."""

import pytest
from fastmcp import Client
from src.tools.utils.base import execute_one_command  # noqa: F401 (used implicitly)
from src.tests.shared.utils import (
    get_vm_id,
    get_vm_ip,
    search_for_pattern,
    wait_for_state,
    cleanup_test_vms,
)

# Mark the entire module as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_manage_vm_tool_exists(mcp_server):
    """Test that the manage_vm tool is properly registered."""
    async with Client(mcp_server) as client:
        tools = await client.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "manage_vm" in tool_names, "manage_vm tool should be registered"


@pytest.mark.asyncio
async def test_manage_vm_allow_write_false(mcp_server_read_only):
    """Test that manage_vm respects the allow_write=False setting."""
    async with Client(mcp_server_read_only) as client:
        result = await client.call_tool(
            "manage_vm", {"vm_id": "1", "operation": "start"}
        )
        output = result.content[0].text
        assert "<error>" in output
        assert "Write operations are disabled" in output


@pytest.mark.asyncio
async def test_manage_vm_invalid_inputs(mcp_server):
    """Test manage_vm with various invalid inputs."""

    async with Client(mcp_server) as client:
        # Test invalid VM ID
        result = await client.call_tool(
            "manage_vm", {"vm_id": "invalid", "operation": "start"}
        )
        output = result.content[0].text
        assert "<error>" in output
        assert "non-negative integer" in output

        # Test negative VM ID
        result = await client.call_tool(
            "manage_vm", {"vm_id": "-1", "operation": "start"}
        )
        output = result.content[0].text
        assert "<error>" in output
        assert "non-negative integer" in output

        # Test invalid operation
        result = await client.call_tool(
            "manage_vm", {"vm_id": "1", "operation": "invalid_op"}
        )
        output = result.content[0].text
        assert "<error>" in output
        assert "Invalid operation" in output


@pytest.mark.asyncio
async def test_manage_vm_lifecycle_operations(mcp_server):
    """Lifecycle happy-path: wait for VM ACTIVE -> stop -> start -> reboot -> terminate."""
    vm_id = None
    try:
        async with Client(mcp_server) as client:
            # 1. Instantiate VM
            inst_out = await client.call_tool(
                "instantiate_vm",
                {"template_id": "0", "vm_name": "test_vm_manage_vm_lifecycle_operations", "network_name": "service"},
            )
            inst_xml = inst_out.content[0].text

            vm_id = get_vm_id(inst_xml)

            assert vm_id and vm_id.isdigit(), (
                "Failed to parse VM ID from instantiate_vm output"
            )

            # 2. Wait until VM is ACTIVE and RUNNING before doing stop
            status_xml = await wait_for_state(
                client, vm_id, "3", target_lcm_state="3", timeout=180
            )

            # Keep the VM alive for the test
            vm_ip = get_vm_ip(status_xml)
            assert vm_ip, f"Could not get IP for VM {vm_id} from XML:\n{status_xml}"
            exec_out = await client.call_tool(
                "execute_command", {"vm_ip_address": vm_ip, "command": "nohup sleep 999 &"}
            )
            assert "<error>" not in exec_out.content[0].text

            # 3. Stop (poweroff) VM – expect success (<result>)
            stop_out = await client.call_tool(
                "manage_vm", {"vm_id": vm_id, "operation": "stop"}
            )
            stop_xml = stop_out.content[0].text
            assert "<result>" in stop_xml, f"Stop operation failed: {stop_xml}"

            # Wait until POWEROFF
            status_xml = await wait_for_state(client, vm_id, "8", timeout=180)
            assert search_for_pattern(status_xml, r"<STATE>8</STATE>"), (
                f"Expected VM to be POWEROFF - output: {status_xml}"
            )

            # 4. Start (resume) VM
            start_out = await client.call_tool(
                "manage_vm", {"vm_id": vm_id, "operation": "start"}
            )
            start_xml = start_out.content[0].text
            assert "<result>" in start_xml or "<error>" in start_xml
            status_xml = await wait_for_state(
                client, vm_id, "3", target_lcm_state="3", timeout=180
            )
            assert search_for_pattern(status_xml, r"<STATE>3</STATE>"), (
                f"Expected VM to be ACTIVE after start - output: {status_xml}"
            )
            assert search_for_pattern(status_xml, r"<LCM_STATE>3</LCM_STATE>"), (
                f"Expected VM to be RUNNING after start - output: {status_xml}"
            )

            # 5. Reboot – just check command returns success XML
            reboot_out = await client.call_tool(
                "manage_vm", {"vm_id": vm_id, "operation": "reboot"}
            )
            reboot_xml = reboot_out.content[0].text
            assert "<result>" in reboot_xml
            status_xml = await wait_for_state(client, vm_id, "3", timeout=180)
            assert search_for_pattern(status_xml, r"<STATE>3</STATE>"), (
                f"Expected VM to be ACTIVE after reboot - output: {status_xml}"
            )
            assert search_for_pattern(status_xml, r"<LCM_STATE>3</LCM_STATE>"), (
                f"Expected VM to be RUNNING after reboot - output: {status_xml}"
            )

            # 6. Terminate – hard to ensure deletion
            term_out = await client.call_tool(
                "manage_vm", {"vm_id": vm_id, "operation": "terminate", "hard": True}
            )
            term_xml = term_out.content[0].text
            assert "<result>" in term_xml or "<error>" in term_xml

    finally:
        cleanup_test_vms()


@pytest.mark.asyncio
async def test_manage_vm_hard_operations(mcp_server):
    """Test manage_vm hard flag functionality."""
    vm_id = None
    try:
        async with Client(mcp_server) as client:
            # 1. Instantiate VM
            inst_out = await client.call_tool(
                "instantiate_vm",
                {"template_id": "0", "vm_name": "test_vm_manage_vm_hard_operations", "network_name": "service"},
            )
            inst_xml = inst_out.content[0].text

            vm_id = get_vm_id(inst_xml)

            assert vm_id and vm_id.isdigit(), (
                "Failed to parse VM ID from instantiate_vm output"
            )

            # 2. Wait until VM is ACTIVE and RUNNING before doing stop
            status_xml = await wait_for_state(
                client, vm_id, "3", target_lcm_state="3", timeout=180
            )

            # Keep the VM alive for the test
            vm_ip = get_vm_ip(status_xml)
            assert vm_ip, f"Could not get IP for VM {vm_id} from XML:\n{status_xml}"
            exec_out = await client.call_tool(
                "execute_command", {"vm_ip_address": vm_ip, "command": "nohup sleep 999 &"}
            )
            assert "<error>" not in exec_out.content[0].text

            print(f"Instantiated VM {vm_id} and is RUNNING")

            # 3. Hard reboot
            reboot_out = await client.call_tool(
                "manage_vm", {"vm_id": vm_id, "operation": "reboot", "hard": True}
            )
            reboot_xml = reboot_out.content[0].text
            assert "<result>" in reboot_xml
            status_xml = await wait_for_state(client, vm_id, "3", timeout=180)
            assert search_for_pattern(status_xml, r"<STATE>3</STATE>"), (
                f"Expected VM to be ACTIVE after hard reboot - output: {status_xml}"
            )
            assert search_for_pattern(status_xml, r"<LCM_STATE>3</LCM_STATE>"), (
                f"Expected VM to be RUNNING after hard reboot - output: {status_xml}"
            )

            print(f"Hard rebooted VM {vm_id}")

            # 4. Hard stop
            stop_out = await client.call_tool(
                "manage_vm", {"vm_id": vm_id, "operation": "stop", "hard": True}
            )
            stop_xml = stop_out.content[0].text
            assert "<result>" in stop_xml
            status_xml = await wait_for_state(client, vm_id, "8", timeout=180)
            assert search_for_pattern(status_xml, r"<STATE>8</STATE>"), (
                f"Expected VM to be POWEROFF after hard stop - output: {status_xml}"
            )

            print(f"Hard stopped VM {vm_id}")

    finally:
        cleanup_test_vms() 