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

"""Base utilities for OpenNebula infrastructure tools."""

import ipaddress
import subprocess
from typing import List
from logging import getLogger

logger = getLogger("opennebula_mcp.utils.base")


def is_valid_ip_address(ip_address: str) -> bool:
    """Check if the given string is a valid IP address."""
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False


def execute_one_command(command_parts: List[str]) -> str:
    """Execute an OpenNebula command and return XML output.

    Args:
        command_parts: List of command parts (e.g., ['onehost', 'list', '--xml'])

    Returns:
        str: XML string output from the command, or XML error format if command fails

    Note:
        Returns XML-formatted error with exit code and detailed messages on failure
    """
    command_str = " ".join(command_parts)

    logger.debug(f"Executing command: {command_str}")

    try:
        result = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            check=True,
        )

        logger.debug(f"Command completed successfully: {command_str}")
        return result.stdout

    except subprocess.CalledProcessError as e:
        # Capture detailed error information including exit code and stderr
        stderr_msg = e.stderr.strip() if e.stderr else "No error message available"
        stdout_msg = e.stdout.strip() if e.stdout else ""

        logger.error(
            f"Command failed: {command_str} (exit code: {e.returncode}, stderr: {stderr_msg}, stdout: {stdout_msg})"
        )

        # Build comprehensive error message
        error_details = f"Command: {command_str}"
        error_details += f"\nExit code: {e.returncode}"
        error_details += f"\nError message: {stderr_msg}"
        if stdout_msg:
            error_details += f"\nStdout: {stdout_msg}"

        return f"<error><exit_code>{e.returncode}</exit_code><command>{command_str}</command><stderr>{stderr_msg}</stderr><stdout>{stdout_msg}</stdout><message>{error_details}</message></error>"

    except FileNotFoundError:
        # Handle case where the command itself doesn't exist
        error_msg = f"Command not found: {command_parts[0]}. Make sure OpenNebula is installed and in PATH."
        logger.error(
            f"Command not found: {command_parts[0]} - OpenNebula may not be installed"
        )
        return f"<error><exit_code>127</exit_code><command>{command_str}</command><stderr>Command not found</stderr><stdout></stdout><message>{error_msg}</message></error>"

    except Exception as e:
        # Handle any other unexpected errors
        error_msg = (
            f"Unexpected error executing {command_str}: {type(e).__name__}: {str(e)}"
        )
        logger.error(f"Unexpected error: {command_str} - {type(e).__name__}: {str(e)}")
        return f"<error><exit_code>-1</exit_code><command>{command_str}</command><stderr>Unexpected error</stderr><stdout></stdout><message>{error_msg}</message></error>"
