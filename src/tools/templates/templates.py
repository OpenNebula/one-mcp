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
from typing import Optional
import tempfile
import os
import xml.etree.ElementTree as ET
from src.tools.utils.base import execute_one_command

logger = getLogger("opennebula_mcp.tools.templates")


def register_tools(mcp, allow_write):
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

    @mcp.tool(
        name="update_template",
        description="""Update the content of an existing template.

        Args:
            template_id: The ID of the template.
            content: The new template content.
            append: If True, append to existing content instead of replacing.

        Returns:
            str: XML string with operation result or error message.
        """,
    )
    def update_template(template_id: str, content: str, append: bool = False) -> str:
        """Update the content of an existing template."""
        if not allow_write:
            logger.warning("update_template called while allow_write=False")
            return "<error><message>Write operations are disabled on this MCP instance.</message></error>"

        if not template_id.isdigit():
            return "<error><message>template_id must be a non-negative integer</message></error>"

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        logger.debug(f"Updating template {template_id} (append={append})")
        try:
            cmd_parts = ["onetemplate", "update", template_id, tmp_path]
            if append:
                cmd_parts.append("--append")

            result = execute_one_command(cmd_parts)

            # Success wrapper
            success_root = ET.Element("result")
            ET.SubElement(success_root, "template_id").text = template_id
            ET.SubElement(success_root, "operation").text = "update"
            ET.SubElement(success_root, "append").text = str(append)
            ET.SubElement(success_root, "message").text = "Template updated successfully"
            ET.SubElement(success_root, "command_output").text = result.strip()
            return ET.tostring(success_root, encoding="unicode")

        except Exception as e:
            logger.error(f"Failed to update template {template_id}: {e}")
            return f"<error><message>Failed to update template: {e}</message></error>"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
