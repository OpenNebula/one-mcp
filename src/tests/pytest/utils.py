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
        status_xml = status_out[0].text

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
