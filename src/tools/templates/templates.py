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

"""Templates tools for OpenNebula MCP Server."""

from logging import getLogger
from src.tools.utils.base import execute_one_command

logger = getLogger("opennebula_mcp.tools.templates")


def register_tools(mcp):
    @mcp.tool(
        name="list_templates",
        description="List all OpenNebula VM templates accessible to the current user.",
    )
    def list_templates() -> str:
        """List all OpenNebula VM templates accessible to the current user.
        Returns:
            str: XML string conforming to Template Pool XSD Schema
        """
        logger.debug("Listing OpenNebula VM templates")
        return execute_one_command(["onetemplate", "list", "--xml"])
