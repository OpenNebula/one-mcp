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

import asyncio
import re
from fastmcp import Client
from typing import Optional
from src.tools.utils.base import execute_one_command


def cleanup_test_vms():
    """Clean up any leftover test VMs from previous runs.
    
    This function looks for VMs with test-related names and deletes them.
    
    Test VM name patterns that will be cleaned up:
    - test_vm_*
    """
    try:
        # Get all VMs and filter for test VMs
        result = execute_one_command(["onevm", "list", "--list", "ID,NAME", "--csv"])
        if "error" not in result:
            cleaned_count = 0
            for line in result.strip().split('\n'):
                if line and 'test_vm_' in line:
                    try:
                        vm_id = line.split(',')[0].strip()
                        if vm_id.isdigit():
                            execute_one_command(["onevm", "recover", "--delete", vm_id])
                            print(f"Cleaned up leftover test VM: {vm_id}")
                            cleaned_count += 1
                    except Exception as e:
                        print(f"Warning: Failed to cleanup VM from line '{line}': {e}")
                        continue
            
            if cleaned_count > 0:
                print(f"✅ Cleaned up {cleaned_count} test VMs")
            else:
                print("ℹ️  No test VMs found to cleanup")
                
    except Exception as e:
        print(f"Warning: VM cleanup failed: {e}")
        # Don't raise - we want tests to continue even if cleanup fails


def get_vm_id(output: str) -> str:
    """Get the VM ID from the output of a command that returns an XML string

    Args:
        output: The output of a command that returns an XML string

    Returns:
        The VM ID
    """
    pattern = r"<ID>\d+</ID>"
    vm_id = re.search(pattern, output).group(0)
    vm_id = vm_id.split(">")[1].split("<")[0]
    return vm_id


def search_for_pattern(output: str, pattern: str) -> str:
    """Search for a pattern in the output of a command that returns an XML string

    Args:
        output: The output of a command that returns an XML string
        pattern: The pattern to search for

    Returns:
        The match if found, otherwise None
    """
    match = re.search(pattern, output)
    if match:
        return match.group(0)
    else:
        return None


async def wait_for_state(
    client: Client,
    vm_id: str,
    target_state: str,
    target_lcm_state: Optional[str] = None,
    timeout: int = 60,
):
    """Poll get_vm_status until VM reaches the target STATE and optional LCM_STATE.
    Used mainly for testing the manage_vm tool and the lifecycle of a VM.

    Args:
        client: The MCP client
        vm_id: The ID of the VM
        target_state: The target state of the VM
        target_lcm_state: The target LCM state of the VM
        timeout: The timeout in seconds

    Returns:
        The XML string of the VM status
    """

    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        status_out = await client.call_tool("get_vm_status", {"vm_id": vm_id})
        status_xml = status_out.content[0].text

        state_match = search_for_pattern(status_xml, rf"<STATE>{target_state}</STATE>")
        if state_match:
            # If no LCM state is specified, a match on the main state is sufficient
            if target_lcm_state is None:
                return status_xml

            # If an LCM state is specified, both must match
            lcm_state_match = search_for_pattern(
                status_xml, rf"<LCM_STATE>{target_lcm_state}</LCM_STATE>"
            )
            if lcm_state_match:
                return status_xml

        if asyncio.get_event_loop().time() > deadline:
            return status_xml  # return last seen
        await asyncio.sleep(3)
